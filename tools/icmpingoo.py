import sys
import socket
import time
import argparse
import signal
import os
from ping3 import ping

# 添加此全局标志变量以跟踪是否使用了 Ctrl+C
ctrl_c_used = False

# 自定义DNS解析异常类，用于抛出更具体的错误信息
def custom_gaierror(msg):
    class CustomGaiError(Exception):
        def __init__(self, message):
            super().__init__(message)

    raise CustomGaiError(msg)

# SIGINT信号处理程序 (Ctrl+C)
def signal_handler(sig, frame):
    global ctrl_c_used
    ctrl_c_used = True

# 解析目标主机的IP地址
def resolve_ip(host, force_ipv4=False):
    try:
        # 默认使用IPv4进行DNS查询
        family = socket.AF_INET if force_ipv4 else socket.AF_INET6

        # 使用系统默认的DNS服务器进行查询
        addr_info = socket.getaddrinfo(host, None, family)
        ip = addr_info[0][4][0]  # 获取IP地址

        return ip

    except socket.gaierror:
        raise ValueError(f"ICMPing 请求找不到主机 {host}。请检查该名称，然后重试.")

# 检查主机名是否为IP地址
def is_valid_ip(host):
    try:
        socket.inet_pton(socket.AF_INET, host)
        return True
    except (socket.error, ValueError):
        pass

    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except (socket.error, ValueError):
        pass

    return False

# 执行ICMP Ping操作，测量响应时间和丢包率
def icmping(
    hostname,
    request_nums,
    force_ipv4,
    force_ipv6,
    timeout=1000,
    continuous_ping=False,
    ttl=64,
):
    try:
        ip = None

        # 根据参数设置DNS解析方式
        if force_ipv4:
            # 如果使用 -4 参数，只使用IPv4进行DNS查询
            ip = resolve_ip(hostname, force_ipv4=True)
        elif force_ipv6:
            # 如果使用 -6 参数，只使用IPv6进行DNS查询
            ip = resolve_ip(hostname, force_ipv4=False)
        else:
            # 否则，根据系统的网络配置来选择DNS查询方式
            try:
                # 尝试使用IPv4进行DNS查询
                ip = resolve_ip(hostname, force_ipv4=True)
            except ValueError:
                # 如果IPv4查询失败，则使用IPv6进行DNS查询
                ip = resolve_ip(hostname, force_ipv4=False)

        if not is_valid_ip(hostname):
            print(f"\n正在 ICMPing {hostname} [{ip}] 具有 32 字节的数据:")  # 修改输出行
        else:
            print(f"\n正在 ICMPing {hostname} 具有 32 字节的数据:")

        request_num = 1
        response_times = []
        received_count = 0
        lost_count = 0

        try:
            while continuous_ping or request_num <= request_nums:
                if ctrl_c_used:  # 检查是否使用了 Ctrl+C
                    break

                # 使用 ping3 库发送 ICMP Echo 请求
                start_time = time.time()
                response_time = ping(hostname, timeout=timeout / 1000, unit="ms", ttl=ttl)

                if response_time is not None:
                    response_times.append(response_time)  # 毫秒为单位
                    print(
                        f"来自 {hostname} 的回复: 字节=32 时间={response_time:.0f}ms TTL={ttl}"
                    )
                    received_count += 1
                else:
                    print("请求超时。")
                    lost_count += 1

                request_num += 1
                time.sleep(1)

        except KeyboardInterrupt:
            pass

        # 计算发送的总数据包数（request_num - 1）
        total_packets_sent = request_num - 1

        # 计算丢包率，考虑没有接收到数据包的情况
        if total_packets_sent > 0:
            packet_loss_rate = (lost_count / total_packets_sent) * 100
        else:
            packet_loss_rate = 100.0

        avg_delay = sum(response_times) / received_count if received_count > 0 else 0.0
        min_delay = min(response_times) if received_count > 0 else 0.0
        max_delay = max(response_times) if received_count > 0 else 0.0

        print(f"\n{ip} 的 ICMPing 统计信息:")
        print(
            f"    数据包: 已发送 = {total_packets_sent}, 已接收 = {received_count}，丢失 = {lost_count} ({packet_loss_rate:.1f}% 丢失)"
        )

        if received_count > 0:
            print("往返行程的估计时间(以毫秒为单位):")
            print(
                f"    最短 = {min_delay:.0f}ms，最长 = {max_delay:.0f}ms，平均 = {avg_delay:.0f}ms"
            )
        else:
            print("所有请求均超时，无法计算往返行程时间.")

        if ctrl_c_used:  # 如果使用 Ctrl+C，则仅打印“Control-C”
            print("Control-C")

    except ValueError as e:
        print(e)

# 主函数
def main():
    script_name = os.path.basename(sys.argv[0])  # 获取脚本或可执行文件名称

    parser = argparse.ArgumentParser(
        description=f"{script_name} - 使用 ICMP 协议检查目标主机的可达性。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
        f"{script_name} example.com\n"
        f"{script_name} example.com -4\n"
        f"{script_name} example.com -6\n"
        f"{script_name} example.com -h\n"
        f"{script_name} example.com -i 128\n"
        f"{script_name} example.com -n 4\n"
        f"{script_name} example.com -t\n"
        f"{script_name} example.com -w 1000",
        usage="%(prog)s hostname [-4] [-6] [-h] [-i TTL] [-n count] [-t] [-w timeout]",
        add_help=False,
    )

    parser.add_argument("hostname", help="要 ICMPing 的目标主机名或IP地址。")
    parser.add_argument("-4", dest="force_ipv4", action="store_true", help="强制使用 IPv4。")
    parser.add_argument("-6", dest="force_ipv6", action="store_true", help="强制使用 IPv6。")
    parser.add_argument("-h", action="help", help="显示帮助信息并退出。")
    parser.add_argument(
        "-i", dest="ttl", metavar="TTL", type=int, default=64, help="生存时间。"
    )
    parser.add_argument(
        "-n",
        dest="request_nums",
        metavar="count",
        type=int,
        default=4,
        help="要发送的回显请求数。",
    )
    parser.add_argument(
        "-t",
        dest="continuous_ping",
        action="store_true",
        help="Ping 指定的主机，直到停止。\n若要查看统计信息并继续操作，请键入 Ctrl+Break； \n若要停止，请键入 Ctrl+C。",
    )
    parser.add_argument(
        "-w",
        dest="timeout",
        metavar="timeout",
        type=int,
        default=1000,
        help="等待每次回复的超时时间(毫秒)。",
    )

    args = parser.parse_args()

    try:
        if args.request_nums < 1:
            args.request_nums = 4

        icmping(
            args.hostname,
            args.request_nums,
            args.force_ipv4,
            args.force_ipv6,
            args.timeout,
            args.continuous_ping,
            args.ttl,
        )

    except ValueError as e:
        print(e)

if __name__ == '__main__':
    # 设置 SIGINT 的信号处理程序 (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    main()
