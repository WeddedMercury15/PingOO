package speedtest

import (
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"golang.org/x/net/icmp"
	"golang.org/x/net/ipv4"
)

const (
	icmpCode = 0
	echoData = "Hello, ICMP!"
	targetIP = "8.8.8.8" // 示例中使用了 Google DNS 的 IP 地址
)

func main() {
	// 创建一个 ICMP 连接
	c, err := icmpListen()
	if err != nil {
		log.Fatal(err)
	}
	defer c.Close()

	// 构造 ICMP Echo 请求包
	echoRequest := icmpMessage(icmp.Echo, icmpCode, echoData)

	// 发送 ICMP Echo 请求包
	err = sendEchoRequest(c, targetIP, echoRequest)
	if err != nil {
		log.Fatal(err)
	}

	// 接收 ICMP Echo 回复包
	echoReply, err := receiveEchoReply(c)
	if err != nil {
		log.Fatal(err)
	}

	// 解析 ICMP Echo 回复包
	rtt, err := parseEchoReply(echoReply)
	if err != nil {
		log.Fatal(err)
	}

	// 打印往返时间（RTT）
	fmt.Printf("Round Trip Time: %s\n", rtt)
}

func icmpListen() (*icmp.PacketConn, error) {
	c, err := icmp.ListenPacket("ip4:icmp", "0.0.0.0")
	if err != nil {
		return nil, err
	}

	conn := ipv4.NewPacketConn(c)

	if err := conn.SetControlMessage(ipv4.FlagTTL|ipv4.FlagSrc|ipv4.FlagDst|ipv4.FlagInterface, true); err != nil {
		return nil, err
	}

	if err := conn.SetTOS(0); err != nil {
		return nil, err
	}

	if err := conn.SetTTL(64); err != nil {
		return nil, err
	}

	return c, nil
}

func icmpMessage(messageType icmp.Type, code int, data string) []byte {
	m := icmp.Message{
		Type: messageType,
		Code: code,
		Body: &icmp.Echo{
			ID:   os.Getpid() & 0xffff,
			Seq:  1,
			Data: []byte(data),
		},
	}

	b, err := m.Marshal(nil)
	if err != nil {
		log.Fatal(err)
	}

	return b
}

func sendEchoRequest(conn *icmp.PacketConn, targetIP string, echoRequest []byte) error {
	dst, err := net.ResolveIPAddr("ip", targetIP)
	if err != nil {
		return err
	}

	_, err = conn.WriteTo(echoRequest, dst)
	if err != nil {
		return err
	}

	return nil
}

func receiveEchoReply(conn *icmp.PacketConn) ([]byte, net.Addr, error) {
	reply := make([]byte, 1500) // 假设接收的回复包不超过 1500 字节

	n, addr, err := conn.ReadFrom(reply)
	if err != nil {
		return nil, nil, err
	}

	return reply[:n], addr, nil
}

func parseEchoReply(echoReply []byte) (time.Duration, error) {
	m, err := icmp.ParseMessage(icmp.IPv4Protocol, echoReply)
	if err != nil {
		return 0, err
	}

	switch m.Type {
	case ipv4.ICMPTypeEchoReply:
		echoReplyBody, ok := m.Body.(*icmp.Echo)
		if !ok {
			return 0, fmt.Errorf("unexpected ICMP echo reply body type")
		}

		// 计算往返时间（RTT）
		receiveTime := time.Now()
		sendTime, err := parseEchoRequestTimestamp(echoReplyBody.Data)
		if err != nil {
			return 0, err
		}

		rtt := receiveTime.Sub(sendTime)
		return rtt, nil

	default:
		return 0, fmt.Errorf("unexpected ICMP message type")
	}
}

func parseEchoRequestTimestamp(data []byte) (time.Time, error) {
	if len(data) < 8 {
		return time.Time{}, fmt.Errorf("invalid ICMP echo request data length")
	}

	// 将前 8 字节解析为 64 位无符号整数（大端序）
	timestamp := int64(data[0])<<56 |
		int64(data[1])<<48 |
		int64(data[2])<<40 |
		int64(data[3])<<32 |
		int64(data[4])<<24 |
		int64(data[5])<<16 |
		int64(data[6])<<8 |
		int64(data[7])

	// 将 64 位无符号整数转换为时间
	sendTime := time.Unix(0, timestamp)
	return sendTime, nil
}

func icmpMessage(messageType icmp.Type, code int, data string) []byte {
	m := icmp.Message{
		Type: messageType,
		Code: code,
		Body: &icmp.Echo{
			ID:   os.Getpid() & 0xffff,
			Seq:  1,
			Data: []byte(data),
		},
	}

	b, err := m.Marshal(nil)
	if err != nil {
		log.Fatal(err)
	}

	return b
}

func sendEchoRequest(conn *icmp.PacketConn, targetIP string, echoRequest []byte) error {
	dst, err := net.ResolveIPAddr("ip", targetIP)
	if err != nil {
		return err
	}

	_, err = conn.WriteTo(echoRequest, dst)
	if err != nil {
		return err
	}

	return nil
}

func receiveEchoReply(conn *icmp.PacketConn) ([]byte, net.Addr, error) {
	reply := make([]byte, 1500) // 假设接收的回复包不超过 1500 字节

	n, addr, err := conn.ReadFrom(reply)
	if err != nil {
		return nil, nil, err
	}

	return reply[:n], addr, nil
}

func parseEchoRequestTimestamp(data []byte) (time.Time, error) {
	if len(data) < 8 {
		return time.Time{}, fmt.Errorf("invalid ICMP echo request data length")
	}

	// 将前 8 字节解析为 64 位无符号整数（大端序）
	timestamp := int64(data[0])<<56 |
		int64(data[1])<<48 |
		int64(data[2])<<40 |
		int64(data[3])<<32 |
		int64(data[4])<<24 |
		int64(data[5])<<16 |
		int64(data[6])<<8 |
		int64(data[7])

	// 将 64 位无符号整数转换为时间
	sendTime := time.Unix(0, timestamp)
	return sendTime, nil
}
