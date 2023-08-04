package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/ccding/go-stun/stun"
)

func main() {
	// 定义命令行参数
	var serverAddr string
	flag.StringVar(&serverAddr, "s", "stunserver.stunprotocol.org:3478", "STUN服务器地址")
	flag.Parse()

	// 创建STUN客户端
	client := stun.NewClient()
	client.SetServerAddr(serverAddr)

	// 进行STUN测试
	nat, host, err := client.Discover()
	if err != nil {
		fmt.Fprintf(os.Stderr, "STUN测试失败: %v\n", err)
		os.Exit(1)
	}

	// 创建表格写入器
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', tabwriter.AlignLeft)

	// 打印测试结果
	fmt.Fprintln(w, "项目\t结果")
	fmt.Fprintln(w, strings.Repeat("-", 30))
	fmt.Fprintf(w, "NAT类型\t%s\n", nat)
	fmt.Fprintf(w, "外部IP地址族\t%s\n", host.Family())
	fmt.Fprintf(w, "外部IP地址\t%s\n", host.IP())
	fmt.Fprintf(w, "外部端口\t%d\n", host.Port())
	fmt.Fprintf(w, "NAT类型描述\t%s\n", getNATDescription(nat))

	w.Flush()
}

// getNATDescription 根据NAT类型返回相应的描述信息
func getNATDescription(nat stun.NATType) string {
	switch nat {
	case stun.NATNone:
		return "未检测到NAT"
	case stun.NATFull:
		return "完全圆锥型NAT"
	case stun.NATSymmetric:
		return "对称型NAT"
	case stun.NATRestricted:
		return "地址限制圆锥型NAT"
	case stun.NATPortRestricted:
		return "端口限制圆锥型NAT"
	default:
		return "未知NAT类型"
	}
}
