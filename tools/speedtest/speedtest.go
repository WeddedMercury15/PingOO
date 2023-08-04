package main

import (
	"encoding/xml"
	"fmt"
	"io/ioutil"
	"net/http"
	"sort"
	"time"
)

type Servers struct {
	Servers []Server `xml:"servers>server"`
}

type Server struct {
	URL  string  `xml:"url,attr"`
	Lat  float64 `xml:"lat,attr"`
	Lon  float64 `xml:"lon,attr"`
	Name string  `xml:"name,attr"`
}

type ByDistance []Server

func (a ByDistance) Len() int           { return len(a) }
func (a ByDistance) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByDistance) Less(i, j int) bool { return a[i].Lat < a[j].Lat }

func main() {
	client := &http.Client{}
	req, _ := http.NewRequest("GET", "https://www.speedtest.net/speedtest-servers-static.php", nil)
	resp, _ := client.Do(req)
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)

	var s Servers
	xml.Unmarshal(body, &s)

	sort.Sort(ByDistance(s.Servers))

	testServer := s.Servers[0]

	fmt.Println("Testing against server:", testServer.Name)

	start := time.Now()
	req, _ = http.NewRequest("GET", testServer.URL, nil)
	resp, _ = client.Do(req)
	defer resp.Body.Close()
	body, _ = ioutil.ReadAll(resp.Body)
	elapsed := time.Since(start)

	size := float64(len(body))
	speed := size / elapsed.Seconds() / 1024 / 1024 * 8

	fmt.Printf("Download speed: %.2f Mbps\n", speed)

	start = time.Now()
	req, _ = http.NewRequest("POST", testServer.URL, nil)
	resp, _ = client.Do(req)
	defer resp.Body.Close()
	body, _ = ioutil.ReadAll(resp.Body)
	elapsed = time.Since(start)

	size = float64(len(body))
	speed = size / elapsed.Seconds() / 1024 / 1024 * 8

	fmt.Printf("Upload speed: %.2f Mbps\n", speed)
}
