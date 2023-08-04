package main

import (
	"flag"
	"fmt"
	"os"
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
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 1, ' ', 0)
	defer w.Flush()

	// 打印表头
	fmt.Fprintln(w, "项目\t结果\t")

	// 打印测试结果
	fmt.Fprintf(w, "NAT类型\t%s\t\n", nat)
	fmt.Fprintf(w, "外部IP地址族\t%s\t\n", host.Family())
	fmt.Fprintf(w, "外部IP地址\t%s\t\n", host.IP())
	fmt.Fprintf(w, "外部端口\t%d\t\n", host.Port())

	// 打印NAT类型描述
	natDesc := ""
	switch nat {
	case stun.NATNone:
		natDesc = "未检测到NAT"
	case stun.NATFull:
		natDesc = "完全圆锥型NAT"
	case stun.NATSymmetric:
		natDesc = "对称型NAT"
	case stun.NATRestricted:
		natDesc = "地址限制圆锥型NAT"
	case stun.NATPortRestricted:
		natDesc = "端口限制圆锥型NAT"
	default:
		natDesc = "未知NAT类型"
	}
	fmt.Fprintf(w, "\x1b[32m%s\x1b[0m\t\x1b[32m%s\x1b[0m\t\n", "NAT类型描述", natDesc)
}
