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

	"golang.org/x/net/icmp"
	"golang.org/x/net/ipv4"
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

		return "", fmt.Errorf("TCPing 请求找不到主机 %s。请检查该名称，然后重试。", hostname)
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

	return "", fmt.Errorf("TCPing 请求找不到主机 %s。请检查该名称，然后重试。", hostname)
}

func createICMPEchoRequest() []byte {
	// 创建 ICMP Echo 请求报文
	echo := icmp.Echo{
		ID:   os.Getpid() & 0xffff,
		Seq:  1, // 请求序列号为1
		Data: []byte("PingOO"),
	}
	msg := icmp.Message{
		Type: ipv4.ICMPTypeEcho, // 使用 ipv4.ICMPTypeEcho 替代 icmp.TypeEcho
		Code: 0,                 // 使用0代替 icmp.Code
		Body: &echo,
	}
	data, err := msg.Marshal(nil)
	if err != nil {
		fmt.Printf("创建 ICMP Echo 请求报文失败：%v\n", err)
		return nil
	}
	return data
}

func checkSum(msg []byte) uint16 {
	sum := 0
	n := len(msg)
	for i := 0; i < n-1; i += 2 {
		sum += int(msg[i])*256 + int(msg[i+1])
	}
	if n&1 == 1 {
		sum += int(msg[n-1]) * 256
	}
	sum = (sum >> 16) + (sum & 0xffff)
	sum += sum >> 16
	return uint16(^sum)
}

func icmpListen() (*icmp.PacketConn, error) {
	c, err := icmp.ListenPacket("ip4:icmp", "0.0.0.0")
	if err != nil {
		return nil, err
	}
	return c, nil
}

func icmping(domain string, requestNums int, timeout time.Duration, continuousPing bool, ttl int, dnsServer string, isIP bool) {
	ip, err := resolveIP(domain, false, false, dnsServer)
	if err != nil {
		fmt.Println(err)
		return
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
		conn, err := icmp.ListenPacket("ip4:icmp", "0.0.0.0")
		if err != nil {
			fmt.Println("无法打开 ICMP 连接:", err)
			break
		}
		defer conn.Close()

		err = conn.IPv4PacketConn().SetTTL(ttl)
		if err != nil {
			fmt.Println("设置 TTL 值时出错:", err)
			break
		}

		msgBytes := createICMPEchoRequest()
		_, err = conn.WriteTo(msgBytes, &net.IPAddr{IP: net.ParseIP(ip)})
		if err != nil {
			fmt.Println("发送 ICMP Echo 请求失败:", err)
			break
		}

		conn.SetReadDeadline(time.Now().Add(timeout))
		respBytes := make([]byte, 1500)
		n, _, err := conn.ReadFrom(respBytes)
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				fmt.Println("请求超时。")
			} else {
				fmt.Println("接收 ICMP Echo 响应失败:", err)
			}
			lostCount++
		} else {
			endTime := time.Now()
			responseTime := endTime.Sub(startTime).Seconds() * 1000
			responseTimes = append(responseTimes, responseTime)
			fmt.Printf("来自 %s 的回复: 字节=%d 时间=%.0fms TTL=%d\n", ip, n, responseTime, ttl)
			receivedCount++
		}

		requestNum++
		time.Sleep(1 * time.Second)
	}

	totalPacketsSent := requestNum - 1
	packetLossRate := float64(lostCount) / float64(totalPacketsSent) * 100.0
	avgDelay := sum(responseTimes) / float64(receivedCount)
	minDelay := min(responseTimes)
	maxDelay := max(responseTimes)

	fmt.Printf("\n%s 的 ICMPing 统计信息:\n", ip)
	fmt.Printf("    数据包: 已发送 = %d, 已接收 = %d，丢失 = %d (%.1f%% 丢失)\n", totalPacketsSent, receivedCount, lostCount, packetLossRate)
	if receivedCount > 0 {
		fmt.Printf("往返行程的估计时间(以毫秒为单位)：\n")
		fmt.Printf("    最短 = %.0fms，最长 = %.0fms，平均 = %.0fms\n", minDelay, maxDelay, avgDelay)
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
	if len(os.Args) < 2 {
		fmt.Println("用法: icmping <目标主机> [请求次数] [超时时间] [持续Ping] [TTL] [DNS服务器] [IPv6]")
		return
	}

	domain := os.Args[1]
	requestNums := 4
	timeout := 500 * time.Millisecond
	continuousPing := false
	ttl := 128
	dnsServer := ""
	isIP := false

	if len(os.Args) >= 3 {
		reqNum, err := strconv.Atoi(os.Args[2])
		if err == nil && reqNum > 0 {
			requestNums = reqNum
		}
	}

	if len(os.Args) >= 4 {
		timeoutVal, err := strconv.Atoi(os.Args[3])
		if err == nil && timeoutVal > 0 {
			timeout = time.Duration(timeoutVal) * time.Millisecond
		}
	}

	if len(os.Args) >= 5 {
		continuousPing = os.Args[4] == "-t"
	}

	if len(os.Args) >= 6 {
		ttlVal, err := strconv.Atoi(os.Args[5])
		if err == nil && ttlVal > 0 {
			ttl = ttlVal
		}
	}

	if len(os.Args) >= 7 {
		dnsServer = os.Args[6]
	}

	if len(os.Args) >= 8 {
		isIP = os.Args[7] == "-6"
	}

	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT)
	go func() {
		<-signalChan
		signalHandler()
	}()

	icmping(domain, requestNums, timeout, continuousPing, ttl, dnsServer, isIP)
}
