package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/ccding/go-stun/stun"
	"github.com/olekukonko/tablewriter"
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
	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"项目", "结果"})
	table.SetBorder(false)
	table.SetColumnSeparator("")
	table.SetRowSeparator("")
	table.SetCenterSeparator("")
	table.SetAlignment(tablewriter.ALIGN_LEFT)

	// 打印测试结果
	table.Append([]string{"NAT类型", fmt.Sprintf("%s", nat)})
	table.Append([]string{"外部IP地址族", fmt.Sprintf("%d", host.Family())})
	table.Append([]string{"外部IP地址", fmt.Sprintf("%s", host.IP())})
	table.Append([]string{"外部端口", fmt.Sprintf("%d", host.Port())})
	table.Append([]string{"NAT类型描述", getNATDescription(nat)})

	table.Render()
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
