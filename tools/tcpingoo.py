# -*- coding: utf-8 -*-

import sys
import socket
import subprocess
import time
import argparse

def custom_gaierror(msg):
    class CustomGaiError(socket.gaierror):
        def __init__(self, message):
            super().__init__(-1, message)

    raise CustomGaiError(msg)

def resolve_ip(hostname, dns_server=None, force_ipv4=False):
    try:
        if dns_server:
            resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            resolver.settimeout(1)
            resolver.connect((dns_server, 53))
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            ip = addr_info[0][4][0]  # 获取 IPv6 地址
            resolver.close()
        elif force_ipv4:
            # 使用socket.getaddrinfo进行DNS解析，支持IPv4
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
            ip = addr_info[0][4][0]  # 获取 IPv4 地址
        else:
            # 尝试使用 IPv4 解决
            try:
                addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
                ip = addr_info[0][4][0]  # 获取 IPv4 地址
            except socket.gaierror:
                # 如果 IPv4 解析失败，请尝试使用 IPv6
                addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
                ip = addr_info[0][4][0]  # 获取 IPv6 地址
        return ip
    except socket.gaierror:
        raise ValueError(f"TCPing 请求找不到主机 {hostname}。请检查该名称，然后重试。")

def tcping(domain, port, request_nums, force_ipv4, force_ipv6, dns_server=None, timeout=1000, continuous_ping=False):
    try:
        ip = None

        if dns_server:
            resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            resolver.settimeout(1)
            resolver.connect((dns_server, 53))
            addr_info = socket.getaddrinfo(domain, None, socket.AF_INET6)
            ip = addr_info[0][4][0]  # 获取 IPv6 地址
            resolver.close()
        elif force_ipv4:
            ip = resolve_ip(domain, dns_server, force_ipv4=True)
        elif force_ipv6:
            ip = resolve_ip(domain, dns_server, force_ipv4=False)
        else:
            try:
                # 尝试使用 IPv4 进行解析
                ip = resolve_ip(domain, dns_server, force_ipv4=True)
            except ValueError:
                # 如果 IPv4 解析失败，尝试使用 IPv6
                ip = resolve_ip(domain, dns_server, force_ipv4=False)

        print("\n正在 TCPing {}:{} [{}:{}] 具有 32 字节的数据:".format(domain, port, ip, port))

        received_count = 0
        response_times = []
        total_sent = 0  # Track total packets sent, including both successful responses and timeouts

        try:
            while continuous_ping or total_sent < request_nums:
                start_time = time.time()
                try:
                    with socket.create_connection((ip, port), timeout=timeout / 1000) as conn:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                        received_count += 1
                        response_times.append(response_time)
                        print(f"来自 {ip}:{port} 的回复: 字节=32 时间={response_time:.0f}ms TTL=64")
                        total_sent += 1  # Increment total_sent for each ping attempt
                        if not continuous_ping:
                            break  # Exit loop after sending one successful ping
                        time.sleep(1)  # Wait 1 second before sending the next request
                except socket.timeout:
                    print("请求超时。")
                    total_sent += 1  # Increment total_sent for each ping attempt, including timeouts
                    if not continuous_ping:
                        break  # Exit loop after sending one unsuccessful ping
                    time.sleep(1)  # Wait 1 second before sending the next request
                except (OSError, ConnectionRefusedError) as e:
                    if isinstance(e, OSError) and e.errno == 10049:
                        print("请求超时。")
                        total_sent += 1  # Increment total_sent for each ping attempt, including timeouts
                        if not continuous_ping:
                            break  # Exit loop after sending one unsuccessful ping
                        time.sleep(1)  # Wait 1 second before sending the next request
                    else:
                        print(f"无法连接到 {ip}:{port}。")
                        received_count += 1  # Count connection errors as received (to include them in statistics)
                        response_times.append(0)
                        total_sent += 1  # Increment total_sent for each ping attempt, including connection errors
                        if not continuous_ping:
                            break  # Exit loop after sending one unsuccessful ping
                        time.sleep(1)  # Wait 1 second before sending the next request

        except KeyboardInterrupt:
            pass

        if continuous_ping:
            received_count = len(response_times)
            total_sent = received_count

        if total_sent > 0:
            packet_loss_rate = ((total_sent - received_count) / total_sent) * 100
        else:
            packet_loss_rate = 100.0

        print(f"\n{ip}:{port} 的 TCPing 统计信息:")
        print(f"    数据包: 已发送 = {total_sent}，已接收 = {received_count}，丢失 = {packet_loss_rate:.1f}% 丢失")

        if received_count > 0:
            packet_loss_rate = ((request_nums - received_count) / request_nums) * 100
            print(f"\n{ip}:{port} 的 TCPing 统计信息:")
            print(f"    数据包: 已发送 = {request_nums}，已接收 = {received_count}，丢失 = {packet_loss_rate:.1f}% 丢失")

        avg_delay = sum(response_times) / received_count
        min_delay = min(response_times)
        max_delay = max(response_times)
        print("往返行程的估计时间(以毫秒为单位):")
        print(f"    最短 = {min_delay:.0f}ms，最长 = {max_delay:.0f}ms，平均 = {avg_delay:.0f}ms")
        
        if received_count == 0:
            print("请求全部超时，无法计算往返行程时间。")

    except ValueError as e:
        print(e)

def print_help():
    print("""
用法: tcpingoo [-t] [-a] [-n count] [-l size] [-f] [-i TTL] [-v TOS]
            [-r count] [-s count] [[-j host-list] | [-k host-list]]
            [-w timeout] [-R] [-S srcaddr] [-c compartment] [-p]
            [-4] [-6] [-d] target_name [port]

选项:
    -t             TCPing 指定的主机，直到停止。
                   若要查看统计信息并继续操作，请键入 Ctrl+Break；
                   若要停止，请键入 Ctrl+C。
    -a             将地址解析为主机名。
    -l size        发送缓冲区大小。
    -f             在数据包中设置“不分段”标记(仅适用于 IPv4)。
    -i TTL         生存时间。
    -v TOS         服务类型(仅适用于 IPv4。该设置已被弃用，
                   对 IP 标头中的服务类型字段没有任何
                   影响)。
    -r count       记录计数跃点的路由(仅适用于 IPv4)。
    -s count       计数跃点的时间戳(仅适用于 IPv4)。
    -j host-list   与主机列表一起使用的松散源路由(仅适用于 IPv4)。
    -k host-list   与主机列表一起使用的严格源路由(仅适用于 IPv4)。
    #-w timeout     等待每次回复的超时时间(毫秒)。
    -R             同样使用路由标头测试反向路由(仅适用于 IPv6)。
                   根据 RFC 5095，已弃用此路由标头。
                   如果使用此标头，某些系统可能丢弃
                   回显请求。
    -S srcaddr     要使用的源地址。
    -c compartment 路由隔离舱标识符。
    -p             Ping Hyper-V 网络虚拟化提供程序地址。
    #-4             强制使用 IPv4。
    #-6             强制使用 IPv6。
    #-d             自定义 DNS 服务器地址
    """)

def main():
    # 使用argparse模块处理命令行参数
    parser = argparse.ArgumentParser(description="TCPing - Test TCP connectivity to a host and port.")
    parser.add_argument("domain", type=str, help="Target domain or IP address to TCPing.")
    parser.add_argument("port", type=int, help="Target port number to TCPing.")
    parser.add_argument("-n", dest="request_nums", type=int, default=4, help="Number of requests to send (default: 4).")
    parser.add_argument("-d", dest="dns_server", type=str, help="Custom DNS server address for resolution.")
    parser.add_argument("-w", dest="timeout", type=int, default=1000, help="Timeout for each request in milliseconds (default: 1000).")

    # 通过添加互斥组，确保 -4 和 -6 参数互斥
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-4", dest="force_ipv4", action="store_true", help="Force using IPv4.")
    group.add_argument("-6", dest="force_ipv6", action="store_true", help="Force using IPv6.")

    # 添加 -t 参数来支持连续 TCPing
    parser.add_argument("-t", dest="continuous_ping", action="store_true", help="TCPing the specified host continuously until stopped.")

    args = parser.parse_args()

    try:
        tcping(args.domain, args.port, args.request_nums, args.force_ipv4, args.force_ipv6, args.dns_server, args.timeout, args.continuous_ping)
    except ValueError as e:
        print(e)

if __name__ == '__main__':
    main()
