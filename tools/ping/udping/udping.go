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

// ctrlCUsed 是一个全局标志变量，用于跟踪是否使用了Ctrl+C
var ctrlCUsed = false

// signalHandler 处理SIGINT信号（Ctrl+C）
func signalHandler() {
	ctrlCUsed = true
}

// resolveIP 解析目标主机的IP地址，支持IPv4和IPv6，并添加系统默认DNS服务器支持
func resolveIP(hostname string, forceIPv4, forceIPv6 bool, dnsServer string) (string, error) {
	if dnsServer == "" {
		resolver := net.DefaultResolver
		ips, err := resolver.LookupIPAddr(context.Background(), hostname)
		if err != nil {
			return "", err
		}

// udping 执行UDP Ping操作，测量响应时间和丢包率
func udping(domain string, port int, requestNums int, forceIPv4, forceIPv6 bool, timeout time.Duration, continuousPing bool, ttl int, dnsServer string, isIP bool) {
	ip, err := resolveIP(domain, forceIPv4, forceIPv6, dnsServer)
	if err != nil {
		fmt.Println(err)
		return
	}

// sum 计算切片中所有元素的总和
func sum(values []float64) float64 {
	total := 0.0
	for _, v := range values {
		total += v
	}
	return total
}

// min 返回切片中的最小值
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

// max 返回切片中的最大值
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

	// 注册Ctrl+C信号处理函数
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signalChan
		signalHandler()
	}()

	// 检查目标是否是IP地址
	targetIP := net.ParseIP(domain)

	udping(domain, port, requestNums, forceIPv4, forceIPv6, time.Duration(timeout)*time.Millisecond, continuousPing, ttl, dnsServer, targetIP != nil)
}
