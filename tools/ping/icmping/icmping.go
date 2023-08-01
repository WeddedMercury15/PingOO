package icmping

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

// resolveIP 解析目标主机的IP地址，支持IPv4和IPv6，并添加自定义DNS服务器支持
func resolveIP(hostname string, dnsServer string) (string, error) {
	if dnsServer == "" {
		// 未指定自定义DNS服务器，使用系统默认的DNS服务器
		resolver := net.DefaultResolver
		ips, err := resolver.LookupIPAddr(context.Background(), hostname)
		if err != nil {
			return "", err
		}

		for _, ip := range ips {
			parsedIP := ip.IP
			if parsedIP.To4() != nil {
				return parsedIP.String(), nil
			}
		}

		return "", fmt.Errorf("ICMPing 请求找不到主机 %s。请检查该名称，然后重试。", hostname)
	}

	// 使用自定义DNS服务器进行解析
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
		if parsedIP.To4() != nil {
			return parsedIP.String(), nil
		}
	}

	return "", fmt.Errorf("ICMPing 请求找不到主机 %s。请检查该名称，然后重试。", hostname)
}

// icmping 执行ICMP Ping操作，测量响应时间和丢包率
func icmping(domain string, requestNums int, timeout time.Duration, continuousPing bool, ttl int, dnsServer string, isIP bool) {
	ip, err := resolveIP(domain, dnsServer)
	if err != nil {
		fmt.Println(err)
		return
	}

	if isIP {
		// 如果目标是IP地址，则修改输出字符串
		fmt.Printf("\n正在 ICMPing %s 具有 32 字节的数据:\n", domain)
	} else {
		// 如果目标是域名，则保持现有的输出字符串
		fmt.Printf("\n正在 ICMPing %s [%s] 具有 32 字节的数据:\n", domain, ip)
	}

	requestNum := 1
	responseTimes := []float64{}
	receivedCount := 0
	lostCount := 0

	for continuousPing || requestNum <= requestNums {
		if ctrlCUsed { // 检查是否使用了 Ctrl+C
			break
		}

		startTime := time.Now()
		conn, err := net.DialTimeout("ip:icmp", ip, timeout)
		if err == nil {
			defer conn.Close()

			// 创建 ICMP 报文
			echoRequest := createICMPEchoRequest()

			// 设置 TTL
			err = conn.(*net.IPConn).SetTTL(ttl)
			if err != nil {
				fmt.Println("设置 TTL 时出错:", err)
				break
			}

			// 发送 ICMP 报文
			_, err = conn.Write(echoRequest)
			if err != nil {
				fmt.Println("发送 ICMP 报文时出错:", err)
				break
			}

			// 接收 ICMP 报文响应
			receiveBuf := make([]byte, 1500) // 使用一个足够大的缓冲区来接收 ICMP 响应
			err = conn.SetReadDeadline(time.Now().Add(timeout))
			if err != nil {
				fmt.Println("设置读取超时时间时出错:", err)
				break
			}
			_, err = conn.Read(receiveBuf)
			if err != nil {
				fmt.Println("读取 ICMP 响应时出错:", err)
				lostCount++
			} else {
				endTime := time.Now()
				responseTime := endTime.Sub(startTime).Seconds() * 1000 // 转换为毫秒
				responseTimes = append(responseTimes, responseTime)
				fmt.Printf("来自 %s 的回复: 字节=32 时间=%.0fms TTL=%d\n", ip, responseTime, ttl)
				receivedCount++
			}
		} else {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				fmt.Println("请求超时。")
			} else {
				fmt.Printf("无法连接到 %s。\n", ip)
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

	fmt.Printf("\n%s 的 ICMPing 统计信息:\n", ip)
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

// createICMPEchoRequest 创建 ICMP Echo 请求报文
func createICMPEchoRequest() []byte {
	// ICMP Echo 请求报文格式
	// Type (8 bits) | Code (8 bits) | Checksum (16 bits) | Identifier (16 bits) | Sequence Number (16 bits) | Data

	// 预设数据大小为32字节
	dataSize := 32

	// 创建ICMP报文
	msg := make([]byte, dataSize+8) // 报文大小为 数据大小(32字节) + ICMP头部(8字节)

	// 设置Type字段为ICMP Echo请求
	msg[0] = 8

	// 填写校验和字段，此处暂不计算，后面再设置

	// 填写标识符和序列号字段
	identifier := os.Getpid() & 0xFFFF
	sequence := 1
	msg[4] = byte(identifier >> 8)
	msg[5] = byte(identifier & 0xFF)
	msg[6] = byte(sequence >> 8)
	msg[7] = byte(sequence & 0xFF)

	// 填写数据字段（可以填充任意数据）
	for i := 8; i < dataSize+8; i++ {
		msg[i] = byte(i)
	}

	// 计算校验和并设置到报文中
	checksum := checkSum(msg)
	msg[2] = byte(checksum >> 8)
	msg[3] = byte(checksum & 0xFF)

	return msg
}

// checkSum 计算ICMP校验和
func checkSum(msg []byte) uint16 {
	sum := 0
	for i := 0; i < len(msg); i += 2 {
		sum += int(msg[i])<<8 | int(msg[i+1])
	}

	sum = (sum >> 16) + (sum & 0xFFFF)
	sum += (sum >> 16)
	return uint16(^sum)
}

// 省略原来的 sum、min、max 函数，可直接使用之前的代码

func main() {
	if len(os.Args) < 2 {
		fmt.Println("用法: icmping <target_nane> [-n count] [-t] [-w timeout] [-i TTL] [-d DNS_server]")
		fmt.Println("")
		fmt.Println("选项:")
		fmt.Println("    -d DNS_server  自定义 DNS 服务器地址。")
		fmt.Println("    -h             显示帮助信息并退出。")
		fmt.Println("    -i TTL         生存时间。")
		fmt.Println("    -n count       要发送的回显请求数。")
		fmt.Println("    -t             ICMPing 指定的主机，直到停止。")
		fmt.Println("                   若要查看统计信息并继续操作，请键入 Ctrl+Break；")
		fmt.Println("                   若要停止，请键入 Ctrl+C。")
		fmt.Println("    -w timeout     等待每次回复的超时时间（毫秒）。")
		os.Exit(0)
	}

	domain := os.Args[1]

	requestNums := 4
	timeout := 1000
	continuousPing := false
	ttl := 128      // 默认TTL值
	dnsServer := "" // 默认为空，不使用自定义DNS服务器

	for i := 2; i < len(os.Args); i++ {
		arg := os.Args[i]
		switch arg {
		case "-n":
			if i+1 < len(os.Args) {
				requestNums, err = strconv.Atoi(os.Args[i+1])
				if err != nil {
					fmt.Println("请求数量无效:", os.Args[i+1])
					os.Exit(0)
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

	// 注册Ctrl+C信号处理函数
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signalChan
		signalHandler()
	}()

	// 检查目标是否是IP地址
	targetIP := net.ParseIP(domain)

	icmping(domain, requestNums, time.Duration(timeout)*time.Millisecond, continuousPing, ttl, dnsServer, targetIP != nil)
}
