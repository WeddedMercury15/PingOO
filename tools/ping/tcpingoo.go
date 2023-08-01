package main

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

// ctrlCUsed 是一个全局标志变量，用于跟踪是否使用了Ctrl+C
var ctrlCUsed = false

// signalHandler 处理SIGINT信号（Ctrl+C）
func signalHandler() {
	ctrlCUsed = true
}

// resolveIP 解析目标主机的IP地址，支持IPv4和IPv6，并添加系统默认DNS服务器支持
func resolveIP(hostname string, forceIPv4, forceIPv6 bool, dnsServer string) (string, error) {
	if dnsServer == "" {
		// 未指定自定义DNS服务器，使用系统默认的DNS服务器
		resolver := net.DefaultResolver
		ips, err := resolver.LookupIPAddr(context.Background(), hostname)
		if err != nil {
			return "", err
		}

		// 尝试使用IPv4进行解析
		if forceIPv4 || !forceIPv6 {
			for _, ip := range ips {
				parsedIP := ip.IP
				if parsedIP.To4() != nil {
					return parsedIP.String(), nil
				}
			}
		}

		// 尝试使用IPv6进行解析
		if forceIPv6 {
			for _, ip := range ips {
				parsedIP := ip.IP
				if parsedIP.To4() == nil {
					return parsedIP.String(), nil
				}
			}
		}

		return "", fmt.Errorf("TCPing 请求找不到主机 %s。请检查该名称，然后重试.", hostname)
	}

	// 使用自定义DNS服务器进行解析
	var family string
	if forceIPv4 {
		family = "ip4"
	} else if forceIPv6 {
		family = "ip6"
	} else {
		family = ""
	}

	// 使用指定的DNS服务器进行解析
	resolver := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{
				Timeout:   2 * time.Second,
				DualStack: true,
			}
			return d.DialContext(ctx, "tcp", dnsServer+":53")
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

	return "", fmt.Errorf("TCPing 请求找不到主机 %s。请检查该名称，然后重试.", hostname)
}

// tcping 执行TCP Ping操作，测量响应时间和丢包率
func tcping(domain string, port int, requestNums int, forceIPv4, forceIPv6 bool, timeout time.Duration, continuousPing bool, ttl int, dnsServer string) {
	ip, err := resolveIP(domain, forceIPv4, forceIPv6, dnsServer)
	if err != nil {
		fmt.Println(err)
		return
	}

	fmt.Printf("\n正在 TCPing %s:%d [%s:%d] 具有 32 字节的数据:\n", domain, port, ip, port)
	requestNum := 1
	responseTimes := []float64{}
	receivedCount := 0
	lostCount := 0

	for continuousPing || requestNum <= requestNums {
		if ctrlCUsed { // 检查是否使用了 Ctrl+C
			break
		}

		startTime := time.Now()
		conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", ip, port), timeout)
		if err == nil {
			defer conn.Close()

			err = conn.SetDeadline(time.Now().Add(timeout))
			if err != nil {
				fmt.Println("设置连接超时时间时出错:", err)
				break
			}

			endTime := time.Now()
			responseTime := endTime.Sub(startTime).Seconds() * 1000 // 转换为毫秒
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

	// 计算发送的总数据包数（requestNum - 1）
	totalPacketsSent := requestNum - 1

	// 计算丢包率，考虑没有接收到数据包的情况
	packetLossRate := float64(lostCount) / float64(totalPacketsSent) * 100.0

	// 计算平均、最小和最大延迟
	avgDelay := sum(responseTimes) / float64(receivedCount)
	minDelay := min(responseTimes)
	maxDelay := max(responseTimes)

	fmt.Printf("\n%s:%d 的 TCPing 统计信息:\n", ip, port)
	fmt.Printf("    数据包: 已发送 = %d, 已接收 = %d，丢失 = %d (%.1f%% 丢失)\n", totalPacketsSent, receivedCount, lostCount, packetLossRate)
	if receivedCount > 0 {
		fmt.Printf("往返行程的估计时间(以毫秒为单位):\n")
		fmt.Printf("    最短 = %.0fms，最长 = %.0fms，平均 = %.0fms\n", minDelay, maxDelay, avgDelay)
	} else {
		fmt.Println("所有请求均超时，无法计算往返行程时间.")
	}

	if ctrlCUsed { // 如果使用 Ctrl+C，则仅打印“Control-C”
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
		fmt.Println("用法: tcping <目标主机> <端口> [-4] [-6] [-n 数量] [-t] [-w 超时时间] [-i TTL] [-d DNS服务器]")
		os.Exit(0)
	}

	domain := os.Args[1]
	port, err := strconv.Atoi(os.Args[2])
	if err != nil {
		fmt.Println("端口号无效:", os.Args[2])
		os.Exit(1)
	}

	requestNums := 4
	timeout := 1000
	continuousPing := false
	forceIPv4 := false
	forceIPv6 := false
	ttl := 128      // 默认TTL值
	dnsServer := "" // 默认为空，不使用自定义DNS服务器

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
					os.Exit(1)
				}
				i++
			}
		case "-t":
			continuousPing = true
		case "-w":
			if i+1 < len(os.Args) {
				timeout, err = strconv.Atoi(os.Args[i+1])
				if err != nil {
					fmt.Println("超时时间无效:", os.Args[i+1])
					os.Exit(1)
				}
				i++
			}
		case "-i":
			if i+1 < len(os.Args) {
				ttl, err = strconv.Atoi(os.Args[i+1])
				if err != nil {
					fmt.Println("TTL值无效:", os.Args[i+1])
					os.Exit(1)
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
			os.Exit(1)
		}
	}

	// 注册Ctrl+C信号处理函数
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signalChan
		signalHandler()
	}()

	tcping(domain, port, requestNums, forceIPv4, forceIPv6, time.Duration(timeout)*time.Millisecond, continuousPing, ttl, dnsServer)
}

func atoi(s string) int {
	n := 0
	for _, c := range s {
		n = n*10 + int(c-'0')
	}
	return n
}
