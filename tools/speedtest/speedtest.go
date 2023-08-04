package main

import (
	"fmt"
	"log"
	"math"

	"github.com/showwin/speedtest-go/speedtest/v2"
)

type Server struct {
	URL  string  `json:"url"`
	Name string  `json:"name"`
	Ping float64 `json:"ping"`
}

func main() {
	fmt.Println("正在获取服务器列表...")
	servers, err := getServerList()
	if err != nil {
		log.Fatal("无法获取服务器列表:", err)
	}

	fmt.Println("正在选择最优服务器...")
	fastestServer := chooseFastestServer(servers)
	if fastestServer == nil {
		fmt.Println("无法找到可用服务器")
		return
	}

	fmt.Println("最优服务器信息:")
	fmt.Printf("名称: %s\n", fastestServer.Name)
	fmt.Printf("URL: %s\n", fastestServer.URL)
	fmt.Printf("延迟: %.2f ms\n", fastestServer.Ping)

	fmt.Println("开始测速...")
	downloadSpeed, uploadSpeed, err := runSpeedTest(fastestServer.URL)
	if err != nil {
		log.Fatal("测速失败:", err)
	}

	fmt.Printf("下载速度: %.2f Mbps\n", downloadSpeed)
	fmt.Printf("上传速度: %.2f Mbps\n", uploadSpeed)
}

func getServerList() ([]Server, error) {
	client, err := speedtest.NewDefaultClient()
	if err != nil {
		return nil, err
	}

	// 获取服务器列表
	servers, err := client.GetServers()
	if err != nil {
		return nil, err
	}

	var serverList []Server
	for _, s := range servers {
		serverList = append(serverList, Server{
			URL:  s.URL,
			Name: s.Name,
			Ping: s.Latency.Seconds() * 1000,
		})
	}

	return serverList, nil
}

func chooseFastestServer(servers []Server) *Server {
	// 根据服务器的ping值排序，选择最小的ping值的服务器
	var fastestServer *Server
	minPing := math.MaxFloat64

	for _, server := range servers {
		if server.Ping < minPing {
			minPing = server.Ping
			fastestServer = &server
		}
	}

	return fastestServer
}

func runSpeedTest(serverURL string) (float64, float64, error) {
	client, err := speedtest.NewDefaultClient()
	if err != nil {
		return 0, 0, err
	}

	server, err := client.GetServer(serverURL)
	if err != nil {
		return 0, 0, err
	}

	downloadSpeed, err := client.Download(server)
	if err != nil {
		return 0, 0, err
	}

	uploadSpeed, err := client.Upload(server)
	if err != nil {
		return 0, 0, err
	}

	return downloadSpeed.MegabitsPerSecond, uploadSpeed.MegabitsPerSecond, nil
}
