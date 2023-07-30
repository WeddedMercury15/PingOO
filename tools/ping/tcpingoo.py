import sys
import socket
import time
import argparse
import signal
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QPlainTextEdit,
    QMessageBox,
)


# 添加此全局标志变量以跟踪是否使用了 Ctrl+C
ctrl_c_used = False


# 自定义DNS解析异常类，用于抛出更具体的错误信息
def custom_gaierror(msg):
    class CustomGaiError(socket.gaierror):
        def __init__(self, message):
            super().__init__(-1, message)

    raise CustomGaiError(msg)


# SIGINT信号处理程序 (Ctrl+C)
def signal_handler(sig, frame):
    global ctrl_c_used
    ctrl_c_used = True


# 解析目标主机的IP地址，支持IPv4和IPv6
def resolve_ip(hostname, force_ipv4=False):
    try:
        # 默认使用IPv4进行DNS查询
        family = socket.AF_INET if force_ipv4 else socket.AF_INET6

        # 使用系统默认的DNS服务器进行查询
        addr_info = socket.getaddrinfo(hostname, None, family)
        ip = addr_info[0][4][0]  # 获取IP地址

        return ip

    except socket.gaierror:
        raise ValueError(f"TCPing 请求找不到主机 {hostname}。请检查该名称，然后重试.")


# 执行TCP Ping操作，测量响应时间和丢包率
def tcping(
    domain,
    port,
    request_nums,
    force_ipv4,
    force_ipv6,
    timeout=1000,
    continuous_ping=False,
    ttl=64,
    output_text_edit=None,
):
    try:
        ip = None

        # 根据参数设置DNS解析方式
        if force_ipv4:
            # 如果使用 -4 参数，只使用IPv4进行DNS查询
            ip = resolve_ip(domain, force_ipv4=True)
        elif force_ipv6:
            # 如果使用 -6 参数，只使用IPv6进行DNS查询
            ip = resolve_ip(domain, force_ipv4=False)
        else:
            # 否则，根据系统的网络配置来选择DNS查询方式
            try:
                # 尝试使用IPv4进行DNS查询
                ip = resolve_ip(domain, force_ipv4=True)
            except ValueError:
                # 如果IPv4查询失败，则使用IPv6进行DNS查询
                ip = resolve_ip(domain, force_ipv4=False)

        output_text_edit.appendPlainText(f"\n正在 TCPing {domain}:{port} [{ip}:{port}] 具有 32 字节的数据:")
        request_num = 1
        response_times = []
        received_count = 0
        lost_count = 0

        try:
            while continuous_ping or request_num <= request_nums:
                if ctrl_c_used:  # 检查是否使用了 Ctrl+C
                    break

                start_time = time.time()
                try:
                    with socket.create_connection(
                        (ip, port), timeout=timeout / 1000
                    ) as conn:
                        # 在发送 ping 请求之前设置 TTL 值
                        conn.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # 转换为毫秒
                        response_times.append(response_time)
                        output_text_edit.appendPlainText(
                            f"来自 {ip}:{port} 的回复: 字节=32 时间={response_time:.0f}ms TTL={ttl}"
                        )
                        received_count += 1
                        request_num += 1
                        time.sleep(1)
                except socket.timeout:
                    output_text_edit.appendPlainText("请求超时。")
                    lost_count += 1
                    request_num += 1
                    time.sleep(1)
                except (OSError, ConnectionRefusedError) as e:
                    if isinstance(e, OSError) and e.errno == 10049:
                        output_text_edit.appendPlainText("请求超时。")
                        lost_count += 1
                        request_num += 1
                        time.sleep(1)
                    else:
                        output_text_edit.appendPlainText(f"无法连接到 {ip}:{port}。")
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

        output_text_edit.appendPlainText(f"\n{ip}:{port} 的 TCPing 统计信息:")
        output_text_edit.appendPlainText(
            f"    数据包: 已发送 = {total_packets_sent}, 已接收 = {received_count}，丢失 = {lost_count} ({packet_loss_rate:.1f}% 丢失)"
        )

        if received_count > 0:
            output_text_edit.appendPlainText("往返行程的估计时间(以毫秒为单位):")
            output_text_edit.appendPlainText(
                f"    最短 = {min_delay:.0f}ms，最长 = {max_delay:.0f}ms，平均 = {avg_delay:.0f}ms"
            )
        else:
            output_text_edit.appendPlainText("所有请求均超时，无法计算往返行程时间.")

        if ctrl_c_used:  # 如果使用 Ctrl+C，则仅打印“Control-C”
            output_text_edit.appendPlainText("Control-C")

    except ValueError as e:
        output_text_edit.appendPlainText(str(e))


# 主窗口类
class TcpPingWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("TCP Ping工具")
        self.setGeometry(100, 100, 600, 400)

        # 主部件
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # 主布局
        main_layout = QVBoxLayout(main_widget)

        # 输入部件
        input_widget = QWidget(self)
        input_layout = QFormLayout(input_widget)

        self.domain_line_edit = QLineEdit(self)
        self.port_spin_box = QSpinBox(self)
        self.force_ipv4_check_box = QCheckBox("强制使用IPv4", self)
        self.force_ipv6_check_box = QCheckBox("强制使用IPv6", self)
        self.custom_dns_line_edit = QLineEdit(self)
        self.continuous_ping_check_box = QCheckBox("连续Ping", self)
        self.ttl_spin_box = QSpinBox(self)
        self.request_num_spin_box = QSpinBox(self)
        self.timeout_spin_box = QSpinBox(self)

        self.port_spin_box.setMaximum(65535)
        self.ttl_spin_box.setMaximum(255)
        self.request_num_spin_box.setMinimum(1)
        self.timeout_spin_box.setMinimum(1)
        self.timeout_spin_box.setSuffix("ms")

        input_layout.addRow("域名或IP地址：", self.domain_line_edit)
        input_layout.addRow("端口号：", self.port_spin_box)
        input_layout.addWidget(self.force_ipv4_check_box)
        input_layout.addWidget(self.force_ipv6_check_box)
        input_layout.addRow("自定义DNS服务器：", self.custom_dns_line_edit)
        input_layout.addWidget(self.continuous_ping_check_box)
        input_layout.addRow("TTL：", self.ttl_spin_box)
        input_layout.addRow("请求次数：", self.request_num_spin_box)
        input_layout.addRow("超时时间：", self.timeout_spin_box)

        # 按钮
        ping_button = QPushButton("Ping", self)
        clear_button = QPushButton("清空结果", self)

        # 输出文本框
        self.output_text_edit = QPlainTextEdit(self)
        self.output_text_edit.setReadOnly(True)

        main_layout.addWidget(input_widget)
        main_layout.addWidget(ping_button)
        main_layout.addWidget(clear_button)
        main_layout.addWidget(self.output_text_edit)

        ping_button.clicked.connect(self.ping_button_clicked)
        clear_button.clicked.connect(self.clear_button_clicked)

    def ping_button_clicked(self):
        domain = self.domain_line_edit.text().strip()
        port = self.port_spin_box.value()
        force_ipv4 = self.force_ipv4_check_box.isChecked()
        force_ipv6 = self.force_ipv6_check_box.isChecked()
        custom_dns_server = self.custom_dns_line_edit.text().strip()
        continuous_ping = self.continuous_ping_check_box.isChecked()
        ttl = self.ttl_spin_box.value()
        request_nums = self.request_num_spin_box.value()
        timeout = self.timeout_spin_box.value()

        try:
            ip = None
            if custom_dns_server:
                socket.set_default_dns_resolver(socket.getaddrinfo, custom_dns_server)

            if not domain:
                raise ValueError("请填写域名或IP地址。")

            # 根据参数设置DNS解析方式
            if force_ipv4:
                ip = resolve_ip(domain, force_ipv4=True)
            elif force_ipv6:
                ip = resolve_ip(domain, force_ipv4=False)
            else:
                try:
                    ip = resolve_ip(domain, force_ipv4=True)
                except ValueError:
                    ip = resolve_ip(domain, force_ipv4=False)

            self.output_text_edit.setPlainText(
                f"开始 TCPing {domain}:{port} [{ip}:{port}] 具有 32 字节的数据:"
            )

            # 调用tcping函数并将输出文本框作为参数传递
            tcping(
                domain,
                port,
                request_nums,
                force_ipv4,
                force_ipv6,
                timeout,
                continuous_ping,
                ttl,
                output_text_edit=self.output_text_edit,
            )

        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def clear_button_clicked(self):
        self.output_text_edit.clear()


# 主函数
def main():
    # 设置 SIGINT 的信号处理程序 (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    app = QApplication(sys.argv)
    window = TcpPingWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
