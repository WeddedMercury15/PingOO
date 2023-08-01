package udping

import (
	"context"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"
)

var ctrlCUsed = false

func signalHandler() {
	ctrlCUsed = true
}

func resolveIP(hostname string, forceIPv4, forceIPv6 bool, dnsServer string) (string, error) {
	if dnsServer == "" {
		resolver := net.DefaultResolver
		ips, err := resolver.LookupIPAddr(context.Background(), hostname)
		if err != nil {
			return "", err
		}

		if forceIPv4 || !forceIPv6 {
			for _, ip := range ips {
				parsedIP := ip.IP
				if parsedIP.To4() != nil {
					return parsedIP.String(), nil
				}
			}
		}

		if forceIPv6 {
			for _, ip := range ips {
				parsedIP := ip.IP
				if parsedIP.To4() == nil {
					return parsedIP.String(), nil
				}
			}
		}

		return "", fmt.Errorf("UDPing 请求找不到主机 %s。请检查该名称，然后重试。", hostname)
	}

	var family string
	if forceIPv4 {
		family = "ip4"
	} else if forceIPv6 {
		family = "ip6"
	} else {
		family = ""
	}

	resolver := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{
				Timeout:   2 * time.Second,
				DualStack: true,
			}
			return d.DialContext(ctx, "udp", dnsServer+":53")
		},
	}

	ips, err := resolver.LookupIPAddr(context.Background(), hostname)
	if err != nil {
		return "", err
	}

	for _, ip := range ips {
		parsedIP := ip.IP
		if family == "" || (family == "ip4" && parsedIP.To4() != nil) || (family == "ip6" && parsedIP.To4() == nil) {
			return parsedIP.String(), nil
		}
	}

	return "", fmt.Errorf("UDPing 请求找不到主机 %s。请检查该名称，然后重试。", hostname)
}

func udping(domain string, port int, requestNums int, forceIPv4, forceIPv6 bool, timeout time.Duration, continuousPing bool, ttl int, dnsServer string, isIP bool) {
	ip, err := resolveIP(domain, forceIPv4, forceIPv6, dnsServer)
	if err != nil {
		fmt.Println(err)
		return
	}

	if isIP {
		fmt.Printf("\n正在 UDPing %s:%d 具有 32 字节的数据:\n", domain, port)
	} else {
		fmt.Printf("\n正在 UDPing %s:%d [%s:%d] 具有 32 字节的数据:\n", domain, port, ip, port)
	}

	requestNum := 1
	responseTimes := []float64{}
	receivedCount := 0
	lostCount := 0

	for continuousPing || requestNum <= requestNums {
		if ctrlCUsed {
			break
		}

		startTime := time.Now()

		// 创建UDP连接
		conn, err := net.DialTimeout("udp", fmt.Sprintf("%s:%d", ip, port), timeout)
		if err == nil {
			defer conn.Close()

			err = conn.SetDeadline(time.Now().Add(timeout))
			if err != nil {
				fmt.Println("设置连接超时时间时出错:", err)
				break
			}

			endTime := time.Now()
			responseTime := endTime.Sub(startTime).Seconds() * 1000
			responseTimes = append(responseTimes, responseTime)
			fmt.Printf("来自 %s:%d 的回复: 字节=32 时间=%.0fms TTL=%d\n", ip, port, responseTime, ttl)
			receivedCount++
		} else {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				fmt.Println("请求超时。")
			} else {
				fmt.Printf("无法连接到 %s:%d。\n", ip, port)
			}
			lostCount++
		}

		requestNum++
		time.Sleep(1 * time.Second)
	}

	totalPacketsSent := requestNum - 1
	packetLossRate := float64(lostCount) / float64(totalPacketsSent) * 100.0
	avgDelay := sum(responseTimes) / float64(receivedCount)
	minDelay := min(responseTimes)
	maxDelay := max(responseTimes)

	fmt.Printf("\n%s:%d 的 UDPing 统计信息:\n", ip, port)
	fmt.Printf("    数据包: 已发送 = %d, 已接收 = %d，丢失 = %d (%.1f%% 丢失)\n", totalPacketsSent, receivedCount, lostCount, packetLossRate)
	if receivedCount > 0 {
		fmt.Printf("往返行程的估计时间(以毫秒为单位):\n")
		fmt.Printf("    最短 = %.0fms，最长 = %.0fms，平均 = %.0fms\n", minDelay, maxDelay, avgDelay)
	} else {
		fmt.Println("所有请求均超时，无法计算往返行程时间.")
	}

	if ctrlCUsed {
		fmt.Println("Control-C")
	}
}

func sum(values []float64) float64 {
	total := 0.0
	for _, v := range values {
		total += v
	}
	return total
}

func min(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	minValue := values[0]
	for _, v := range values {
		if v < minValue {
			minValue = v
		}
	}
	return minValue
}

func max(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	maxValue := values[0]
	for _, v := range values {
		if v > maxValue {
			maxValue = v
		}
	}
	return maxValue
}

func main() {
	if len(os.Args) < 3 {
		fmt.Println("用法: udping <target_nane> <port> [-4] [-6] [-n count] [-w timeout] [-i TTL] [-d DNS_server]")
		fmt.Println("")
		fmt.Println("选项:")
		fmt.Println("    -4             强制使用 IPv4。")
		fmt.Println("    -6             强制使用 IPv6。")
		fmt.Println("    -d DNS_server  自定义 DNS 服务器地址。")
		fmt.Println("    -h             显示帮助信息并退出。")
		fmt.Println("    -i TTL         生存时间。")
		fmt.Println("    -n count       要发送的回显请求数。")
		fmt.Println("    -w timeout     等待每次回复的超时时间（毫秒）。")
		os.Exit(0)
	}

	domain := os.Args[1]
	port, err := strconv.Atoi(os.Args[2])
	if err != nil {
		fmt.Println("端口号无效:", os.Args[2])
		os.Exit(0)
	}

	requestNums := 4
	timeout := 1000
	continuousPing := false
	forceIPv4 := false
	forceIPv6 := false
	ttl := 128
	dnsServer := ""

	for i := 3; i < len(os.Args); i++ {
		arg := os.Args[i]
		switch arg {
		case "-4":
			forceIPv4 = true
		case "-6":
			forceIPv6 = true
		case "-n":
			if i+1 < len(os.Args) {
				requestNums, err = strconv.Atoi(os.Args[i+1])
				if err != nil {
					fmt.Println("请求数量无效:", os.Args[i+1])
					os.Exit(0)
				}
				i++
			}
		case "-w":
			if i+1 < len(os.Args) {
				timeout, err = strconv.Atoi(os.Args[i+1])
				if err != nil {
					fmt.Println("超时时间无效:", os.Args[i+1])
					os.Exit(0)
				}
				i++
			}
		case "-i":
			if i+1 < len(os.Args) {
				ttl, err = strconv.Atoi(os.Args[i+1])
				if err != nil {
					fmt.Println("TTL值无效:", os.Args[i+1])
					os.Exit(0)
				}
				i++
			}
		case "-d":
			if i+1 < len(os.Args) {
				dnsServer = os.Args[i+1]
				i++
			}
		default:
			fmt.Println("无效的参数:", arg)
			os.Exit(0)
		}
	}

	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signalChan
		signalHandler()
	}()

	targetIP := net.ParseIP(domain)

	udping(domain, port, requestNums, forceIPv4, forceIPv6, time.Duration(timeout)*time.Millisecond, continuousPing, ttl, dnsServer, targetIP != nil)
}
