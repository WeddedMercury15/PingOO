import sys
import socket
import subprocess
import time

def custom_gaierror(msg):
    class CustomGaiError(socket.gaierror):
        def __init__(self, message):
            super().__init__(-1, message)

    raise CustomGaiError(msg)

def resolve_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        raise ValueError(f"TCPing 请求找不到主机 {hostname}。请检查该名称，然后重试。")

def resolve_cname_with_nslookup(hostname):
    try:
        result = subprocess.run(["nslookup", hostname], capture_output=True, text=True)
        output_lines = result.stdout.splitlines()
        for line in output_lines:
            if "名称" in line:
                cname = line.split(":")[1].strip()
                if cname != hostname:
                    return cname
    except subprocess.CalledProcessError:
        pass
    return None

def tcping(domain, port, request_nums):
    resolved_hostname = None
    cname = resolve_cname_with_nslookup(domain)
    if cname is not None:
        resolved_hostname = cname
        ip = resolve_ip(cname)
        if ip is None:
            custom_gaierror(f"TCPing 请求找不到主机 {resolved_hostname}。请检查该名称，然后重试。")

    if resolved_hostname is None:
        hostname = f"{domain}:{port}"
    else:
        hostname = f"{resolved_hostname}:{port}"

    ip = resolve_ip(domain)
    if ip is not None:
        print(f"\n正在 TCPing {hostname} [{ip}:{port}] 具有 32 字节的数据:")
    else:
        print(f"\n正在 TCPing {hostname} [{domain}:{port}] 具有 32 字节的数据:")

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
                print(f"请求超时。")
            
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
        print("\nControl-C")
        sys.exit(0)

    packet_loss_rate = ((request_nums - received_count) / request_nums) * 100
    print("\n{0}:{1} 的 TCPing 统计信息:".format(ip, port))
    print(f"    数据包: 已发送 = {received_count}，已接收 = {received_count}，丢失 = {0} (0.0% 丢失)")
    if received_count > 0:
        avg_delay = sum(response_times) / received_count
        min_delay = min(response_times)
        max_delay = max(response_times)
        print("往返行程的估计时间(以毫秒为单位):")
        print(f"    最短 = {min_delay:.0f}ms，最长 = {max_delay:.0f}ms，平均 = {avg_delay:.0f}ms")

    print()

def print_help():
    print("""
用法: python tcping.py [地址:端口]

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
    -4             仅使用 IPv4。
    """)

def main():
    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help']:
        print_help()
        return

    address_port = sys.argv[1].split(':')
    if len(address_port) != 2:
        print("地址和端口格式不正确，请使用'地址:端口'的格式来指定。")
        sys.exit(1)
    ipAddress = address_port[0]
    port = int(address_port[1])

    # 发送4个TCPing请求
    request_nums = 4

    try:
        domain = resolve_cname_with_nslookup(ipAddress)
        if domain is not None:
            tcping(domain, port, request_nums)
        else:
            tcping(ipAddress, port, request_nums)
    except ValueError as e:
        print(e)

if __name__ == '__main__':
    main()
