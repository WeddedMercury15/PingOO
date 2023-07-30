import os
import sys
import time
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class SpeedTestCard(ttk.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, relief="raised", borderwidth=2)
        self.parent = parent
        self.title = title
        self.create_widgets()

    def create_widgets(self):
        self.lbl_title = tk.Label(self, text=self.title, font=("Arial", 14, "bold"))
        self.lbl_title.pack(pady=5)

        self.lbl_download = tk.Label(self, text="下载速度：0 Mbps", font=("Arial", 12))
        self.lbl_download.pack(pady=5)

        self.lbl_upload = tk.Label(self, text="上传速度：0 Mbps", font=("Arial", 12))
        self.lbl_upload.pack(pady=5)

        self.lbl_ping = tk.Label(self, text="Ping：0 ms", font=("Arial", 12))
        self.lbl_ping.pack(pady=5)

        if self.title == "测速选项":
            self.create_speed_options()
        elif self.title == "网络连接状态":
            self.create_network_status()

    def create_speed_options(self):
        self.speed_test_interval = 10

        self.lbl_interval = tk.Label(self, text="测速间隔（秒）：", font=("Arial", 12))
        self.lbl_interval.pack(pady=5)

        self.scale_interval = tk.Scale(self, from_=1, to=60, orient=tk.HORIZONTAL, length=200)
        self.scale_interval.set(self.speed_test_interval)
        self.scale_interval.pack(pady=5)

        self.btn_apply = tk.Button(self, text="应用设置", font=("Arial", 12), command=self.apply_settings)
        self.btn_apply.pack(pady=5)

    def apply_settings(self):
        self.speed_test_interval = self.scale_interval.get()
        messagebox.showinfo("设置", f"测速间隔设置为：{self.speed_test_interval} 秒")

    def create_network_status(self):
        self.lbl_status = tk.Label(self, text="网络连接状态：未知", font=("Arial", 12))
        self.lbl_status.pack(pady=5)
        self.update_network_status()

    def update_network_status(self):
        if platform.system() == "Windows":
            ping_cmd = ["ping", "8.8.8.8", "-n", "1"]
        else:
            ping_cmd = ["ping", "8.8.8.8", "-c", "1"]

        try:
            subprocess.check_output(ping_cmd, text=True, stderr=subprocess.STDOUT)
            status = "已连接"
        except subprocess.CalledProcessError:
            status = "未连接"

        self.lbl_status.config(text=f"网络连接状态：{status}")
        self.after(5000, self.update_network_status)

class SpeedTestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SpeedTest in Python - 简体中文版")
        self.geometry("400x400")
        self.minsize(400, 400)  # 设置窗口最小尺寸
        self.maxsize(800, 800)  # 设置窗口最大尺寸
        self.overrideredirect(True)  # 移除边框和标题栏，取消最大化和最小化按钮

        self.create_widgets()

    def create_widgets(self):
        self.paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.cards = []
        self.cards.append(SpeedTestCard(self.paned_window, "测速选项"))
        self.cards.append(SpeedTestCard(self.paned_window, "网络连接状态"))
        for i in range(3):
            title = f"卡片 {i+1}"
            card = SpeedTestCard(self.paned_window, title)
            self.paned_window.add(card)
            self.cards.append(card)

        self.frame_bottom = tk.Frame(self)
        self.frame_bottom.pack(pady=10)

        self.btn_start = tk.Button(self.frame_bottom, text="开始测速", font=("Arial", 12), command=self.start_speed_test)
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(self.frame_bottom, text="停止测速", font=("Arial", 12), command=self.stop_speed_test)
        self.btn_stop.pack(side=tk.LEFT, padx=10)
        self.btn_stop.config(state=tk.DISABLED)

        self.btn_history = tk.Button(self.frame_bottom, text="查看历史记录", font=("Arial", 12), command=self.view_history)
        self.btn_history.pack(side=tk.RIGHT, padx=10)

        self.is_speed_test_running = False
        self.speed_test_interval = 10
        self.speed_test_timer = None
        self.speed_test_thread = None

        self.update_speed_test_results()

        self.paned_window.bind("<ButtonRelease-1>", self.on_paned_release)

    def on_paned_release(self, event):
        self.paned_window.update()

    def perform_speed_test(self):
        try:
            messagebox.showinfo("SpeedTest", "测速进行中，请稍候...")
            speed_test_cmd = ["speedtest-cli"]
            if platform.system() != "Windows":
                speed_test_cmd.insert(0, sys.executable)

            speed_test_result = subprocess.run(speed_test_cmd, capture_output=True, text=True)
            output = speed_test_result.stdout

            download_speed, upload_speed, ping = 0.0, 0.0, 0.0
            for line in output.split("\n"):
                if "Download:" in line:
                    download_speed = float(line.split()[1])
                elif "Upload:" in line:
                    upload_speed = float(line.split()[1])
                elif "Ping:" in line:
                    ping = float(line.split()[1])

            for card in self.cards[3:]:
                card.update_results(download_speed, upload_speed, ping)

            self.save_results_to_file(download_speed, upload_speed, ping)

            # 输出信息到控制台
            print(f"下载速度：{download_speed:.2f} Mbps")
            print(f"上传速度：{upload_speed:.2f} Mbps")
            print(f"Ping：{ping:.2f} ms")
        except Exception as e:
            messagebox.showerror("Error", f"测速出错：{e}")
            print("测速出错:", e)

    def start_speed_test(self):
        if not self.is_speed_test_running:
            self.is_speed_test_running = True
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.speed_test_thread = threading.Thread(target=self.run_speed_test)
            self.speed_test_thread.daemon = True
            self.speed_test_thread.start()

    def run_speed_test(self):
        while self.is_speed_test_running:
            self.perform_speed_test()
            time.sleep(self.speed_test_interval)

    def stop_speed_test(self):
        self.is_speed_test_running = False
        if self.speed_test_thread and self.speed_test_thread.is_alive():
            self.speed_test_thread.join()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def update_speed_test_results(self):
        self.perform_speed_test()
        self.speed_test_timer = self.after(self.speed_test_interval * 1000, self.update_speed_test_results)

    def view_history(self):
        if os.path.isfile("speedtest_results.txt"):
            with open("speedtest_results.txt", "r") as f:
                history_text = f.read()
            messagebox.showinfo("历史测速记录", history_text)
        else:
            messagebox.showerror("Error", "未找到历史测速记录。")

    def save_results_to_file(self, download_speed, upload_speed, ping):
        with open("speedtest_results.txt", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"下载速度：{download_speed:.2f} Mbps, "
                    f"上传速度：{upload_speed:.2f} Mbps, "
                    f"Ping：{ping:.2f} ms\n")

if __name__ == "__main__":
    app = SpeedTestApp()
    app.mainloop()
