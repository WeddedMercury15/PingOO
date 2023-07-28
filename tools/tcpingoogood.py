import sys
import socket
import subprocess
import time

def custom_gaierror(msg):
    class CustomGaiError(socket.gaierror):
        def __init__(self, message):
            super().__init__(-1, message)

    raise CustomGaiError(msg)

def resolve_ip(hostname, dns_server=None):
    try:
        if dns_server:
            resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            resolver.settimeout(1)
            resolver.connect((dns_server, 53))
            ip = resolver.gethostbyname(hostname)
            resolver.close()
        else:
            ip = socket.gethostbyname(hostname)
        return ip
    except socket.gaierror:
        raise ValueError(f"TCPing 请求找不到主机 {hostname}。请检查该名称，然后重试。")

def tcping(domain, port, request_nums, dns_server=None):
    try:
        # Check if the domain is an IP address
        ip = socket.inet_aton(domain)
        ip = domain
    except socket.error:
        ip = resolve_ip(domain, dns_server)

    print(f"\n正在 TCPing {domain}:{port} 具有 32 字节的数据:")

    received_count = 0
    response_times = []

    try:
        for i in range(request_nums):
            start_time = time.time()
            try:
                with socket.create_connection((domain, port), timeout=1) as conn:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # 转换成毫秒
                    received_count += 1
                    response_times.append(response_time)
                    print(f"来自 {ip}:{port} 的回复: 字节=32 时间={response_time:.0f}ms TTL=64")
            except (socket.timeout, ConnectionRefusedError):
                print("请求超时。")
            
            if i < request_nums - 1:
                time.sleep(1)  # 等待1秒后再发送下一个请求

    except KeyboardInterrupt:
        if received_count > 0:
            print(f"\n{ip}:{port} 的 TCPing 统计信息:")
            packet_loss_rate = ((request_nums - received_count) / request_nums) * 100
            print(f"    数据包: 已发送 = {received_count}，已接收 = {received_count}，丢失 = {0} (0.0% 丢失)")
            avg_delay = sum(response_times) / received_count
            min_delay = min(response_times)
            max_delay = max(response_times)
            print("往返行程的估计时间(以毫秒为单位):")
            print(f"    最短 = {min_delay:.0f}ms，最长 = {max_delay:.0f}ms，平均 = {avg_delay:.0f}ms")
        print("Control-C")
        sys.exit(0)

    packet_loss_rate = ((request_nums - received_count) / request_nums) * 100
    print(f"\n{ip}:{port} 的 TCPing 统计信息:")
    print(f"    数据包: 已发送 = {received_count}，已接收 = {received_count}，丢失 = {0} (0.0% 丢失)")
    if received_count > 0:
        avg_delay = sum(response_times) / received_count
        min_delay = min(response_times)
        max_delay = max(response_times)
        print("往返行程的估计时间(以毫秒为单位):")
        print(f"    最短 = {min_delay:.0f}ms，最长 = {max_delay:.0f}ms，平均 = {avg_delay:.0f}ms")

def print_help():
    print("""
用法: tcpingoo [-t] [-a] [-n count] [-l size] [-f] [-i TTL] [-v TOS]
            [-r count] [-s count] [[-j host-list] | [-k host-list]]
            [-w timeout] [-R] [-S srcaddr] [-c compartment] [-p]
            [-4] [-6] [-d] target_name [port]

选项:
    -h, --help     显示帮助信息
    -t             TCPing 指定的主机，直到停止。
                   若要查看统计信息并继续操作，请键入 Ctrl+Break；
                   若要停止，请键入 Ctrl+C。
    -a             将地址解析为主机名。
    -n count       要发送的回显请求数。
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
    -w timeout     等待每次回复的超时时间(毫秒)。
    -R             同样使用路由标头测试反向路由(仅适用于 IPv6)。
                   根据 RFC 5095，已弃用此路由标头。
                   如果使用此标头，某些系统可能丢弃
                   回显请求。
    -S srcaddr     要使用的源地址。
    -c compartment 路由隔离舱标识符。
    -p             Ping Hyper-V 网络虚拟化提供程序地址。
    -4             强制使用 IPv4。
    -6             强制使用 IPv6。
    -d             自定义 DNS 服务器地址
    """)

def main():
    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help']:
        print_help()
        return

    dns_server = None
    args = sys.argv[1:]

    # Check for custom DNS server using -d option
    if '-d' in args:
        try:
            index = args.index('-d')
            dns_server = args[index + 1]
            args = args[:index] + args[index + 2:]
        except IndexError:
            print("未指定自定义 DNS 服务器。")
            sys.exit(1)

    if len(args) != 2:
        print_help()
        sys.exit(1)

    ipAddress, port = args

    # 发送4个TCPing请求
    request_nums = 4

    try:
        tcping(ipAddress, int(port), request_nums, dns_server)
    except ValueError as e:
        print(e)

if __name__ == '__main__':
    main()
