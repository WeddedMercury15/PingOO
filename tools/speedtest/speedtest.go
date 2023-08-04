package main

import (
	"fmt"
	"log"
	"math"

	"github.com/showwin/speedtest-go/speedtest"
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
	speedtestClient := speedtest.New()

	serverList, err := speedtestClient.FetchServers()
	if err != nil {
		return nil, err
	}

	targets, err := serverList.FindServer([]int{})
	if err != nil {
		return nil, err
	}

	var servers []Server
	for _, s := range targets {
		servers = append(servers, Server{
			URL:  s.URL,
			Name: s.Name,
			Ping: s.Latency.Seconds() * 1000,
		})
	}

	return servers, nil
}

func chooseFastestServer(servers []Server) *Server {
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

func runSpeedTest(serverName string) (float64, float64, error) {
	speedtestClient := speedtest.New()

	serverList, err := speedtestClient.FetchServers()
	if err != nil {
		return 0, 0, err
	}

	var targetServer *speedtest.Server
	for _, server := range serverList {
		if server.Name == serverName {
			targetServer = server
			break
		}
	}

	if targetServer == nil {
		return 0, 0, fmt.Errorf("could not find server with name %s", serverName)
	}

	targetServer.DownloadTest()
	targetServer.UploadTest()

	downloadSpeed := targetServer.DLSpeed
	uploadSpeed := targetServer.ULSpeed

	return downloadSpeed, uploadSpeed, nil
}
