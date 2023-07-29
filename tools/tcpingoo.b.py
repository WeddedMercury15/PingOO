import sys
import socket
import time
import argparse
import dns.resolver

def custom_gaierror(msg):
    class CustomGaiError(socket.gaierror):
        def __init__(self, message):
            super().__init__(-1, message)

    raise CustomGaiError(msg)

def resolve_ip(hostname, dns_server=None, force_ipv4=False):
    try:
        if dns_server:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            answer = resolver.query(hostname, "A" if force_ipv4 else "AAAA", raise_on_no_answer=False)
            if answer.rrset is not None:
                ip = str(answer.rrset[0])
            else:
                raise TimeoutError("DNS query to custom server timed out.")
        else:
            family = socket.AF_INET6 if not force_ipv4 else socket.AF_INET
            addr_info = socket.getaddrinfo(hostname, None, family)
            ip = addr_info[0][4][0]  # Get the IP address

        return ip

    except socket.gaierror:
        raise ValueError(f"TCPing 请求找不到主机 {hostname}。请检查该名称，然后重试.")

def tcping(domain, port, request_nums, force_ipv4, force_ipv6, dns_server=None, timeout=1000):
    try:
        ip = None

        if dns_server:
            try:
                # Check if the custom DNS server is valid and reachable
                resolve_ip(domain, dns_server, force_ipv4=False)
                # If valid, resolve the domain using the custom DNS server
                ip = resolve_ip(domain, dns_server, force_ipv4=False)
            except ValueError:
                raise ValueError(f"TCPing 请求找不到主机 {domain}。请检查该名称，然后重试。")

        elif force_ipv4:
            ip = resolve_ip(domain, dns_server, force_ipv4=True)
        elif force_ipv6:
            ip = resolve_ip(domain, dns_server, force_ipv4=False)
        else:
            # Resolve using IPv4 as default
            ip = resolve_ip(domain, dns_server, force_ipv4=True)

        print(f"\n正在 TCPing {domain}:{port} [{ip}:{port}] 具有 32 字节的数据:")
        received_count = 0
        response_times = []
        total_sent = 0  # Initialize total_sent to track the actual number of packets sent

        try:
            while total_sent < request_nums:
                start_time = time.time()
                try:
                    with socket.create_connection((ip, port), timeout=timeout / 1000) as conn:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                        received_count += 1
                        response_times.append(response_time)
                        print(f"来自 {ip}:{port} 的回复: 字节=32 时间={response_time:.0f}ms TTL=64")
                        total_sent += 1  # Increment total_sent only when a packet is sent
                        time.sleep(1)
                except socket.timeout:
                    print("请求超时。")
                    time.sleep(1)
                except (OSError, ConnectionRefusedError) as e:
                    if isinstance(e, OSError) and e.errno == 10049:
                        print("请求超时。")
                        time.sleep(1)
                    else:
                        print(f"无法连接到 {ip}:{port}。")
                        total_sent += 1  # Increment total_sent even if the packet is lost
                        time.sleep(1)

        except KeyboardInterrupt:
            pass

        packet_loss_rate = ((total_sent - received_count) / total_sent) * 100 if total_sent > 0 else 0.0
        avg_delay = sum(response_times) / received_count if received_count > 0 else 0.0
        min_delay = min(response_times) if received_count > 0 else 0.0
        max_delay = max(response_times) if received_count > 0 else 0.0

        print(f"\n{ip}:{port} 的 TCPing 统计信息:")
        print(
            f"    数据包: 已发送 = {total_sent}, 已接收 = {received_count}，丢失 = {int(total_sent - received_count)} ({packet_loss_rate:.1f}% 丢失)")

        if received_count > 0:
            print("往返行程的估计时间(以毫秒为单位):")
            print(f"    最短 = {min_delay:.0f}ms，最长 = {max_delay:.0f}ms，平均 = {avg_delay:.0f}ms")
        else:
            print("请求全部超时，无法计算往返行程时间.")

    except ValueError as e:
        print(e)

def print_help():
    print("""
用法: tcpingoo [-n count] [-d DNS_server] [-w timeout] [-4] [-6] target_name port

选项:
    -n count       计划发送的请求数 (默认: 4)。
    -d DNS_server  自定义 DNS 服务器地址。
    -w timeout     每次请求的超时时间(毫秒) (默认: 1000)。
    -4             强制使用 IPv4。
    -6             强制使用 IPv6。
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

    args = parser.parse_args()

    try:
        if args.request_nums < 1:
            args.request_nums = 4  # Set default value to 4 if no value is specified

        tcping(args.domain, args.port, args.request_nums, args.force_ipv4, args.force_ipv6, args.dns_server, args.timeout)
    except ValueError as e:
        print(e)

if __name__ == '__main__':
    main()
