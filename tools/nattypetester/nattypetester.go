package main

import (
	"flag"
	"fmt"

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
		fmt.Println(err)
		return
	}

	// 输出测试结果
	fmt.Println("NAT类型:", nat)
	fmt.Println("外部IP地址族:", host.Family())
	fmt.Println("外部IP地址:", host.IP())
	fmt.Println("外部端口:", host.Port())

	switch nat {
	case stun.NATNone:
		fmt.Println("未检测到NAT")
	case stun.NATFull:
		fmt.Println("完全圆锥型NAT")
	case stun.NATSymmetric:
		fmt.Println("对称型NAT")
	case stun.NATRestricted:
		fmt.Println("地址限制圆锥型NAT")
	case stun.NATPortRestricted:
		fmt.Println("端口限制圆锥型NAT")
	default:
		fmt.Println("未知NAT类型")
	}
}
