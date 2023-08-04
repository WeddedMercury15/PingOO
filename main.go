package main

import (
	"fmt"

	"github.com/eiannone/keyboard"
	"github.com/inancgumus/screen"
	"github.com/showwin/speedtest-go/speedtest"
)

func main() {
	err := keyboard.Open()
	if err != nil {
		panic(err)
	}
	defer keyboard.Close()

	var speedtestClient = speedtest.New()
	serverList, _ := speedtestClient.FetchServers()
	targets, _ := serverList.FindServer([]int{})

	menuItems := []string{"测试下载速度", "测试上传速度", "测试延迟", "退出"}
	selectedIndex := 0

	for {
		screen.Clear()
		screen.MoveTopLeft()

		fmt.Println("选择一个选项:")
		for i, item := range menuItems {
			if i == selectedIndex {
				fmt.Printf("-> %s\n", item)
			} else {
				fmt.Printf("   %s\n", item)
			}
		}

		char, key, err := keyboard.GetKey()
		if err != nil {
			panic(err)
		}

		switch key {
		case keyboard.KeyArrowUp:
			if selectedIndex > 0 {
				selectedIndex--
			}
		case keyboard.KeyArrowDown:
			if selectedIndex < len(menuItems)-1 {
				selectedIndex++
			}
		case keyboard.KeyEnter:
			switch selectedIndex {
			case 0:
				for _, s := range targets {
					s.PingTest(nil)
					s.DownloadTest()
					fmt.Printf("从 %s 下载速度: %.2f Mbps\n", s.Name, s.DLSpeed)
				}
			case 1:
				for _, s := range targets {
					s.PingTest(nil)
					s.UploadTest()
					fmt.Printf("从 %s 上传速度: %.2f Mbps\n", s.Name, s.ULSpeed)
				}
			case 2:
				for _, s := range targets {
					s.PingTest(nil)
					fmt.Printf("从 %s 延迟: %d ms\n", s.Name, s.Latency)
				}
			case 3:
				return
			default:
				fmt.Println("无效的选项")
			}
			fmt.Println("\n按任意键继续...")
			keyboard.GetKey()
		default:
			fmt.Printf("您按下了 %q 键\n", char)
		}
	}
}
