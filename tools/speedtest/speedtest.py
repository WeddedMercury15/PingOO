import os
import sys
import time
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class SpeedTestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SpeedTest in Python - 简体中文版")
        self.geometry("400x400")

        self.create_widgets()

    def create_widgets(self):
        self.frame_top = tk.Frame(self)
        self.frame_top.pack(pady=20)

        self.lbl_download = tk.Label(self.frame_top, text="下载速度：0 Mbps", font=("Arial", 12))
        self.lbl_download.pack(pady=5)

        self.lbl_upload = tk.Label(self.frame_top, text="上传速度：0 Mbps", font=("Arial", 12))
        self.lbl_upload.pack(pady=5)

        self.lbl_ping = tk.Label(self.frame_top, text="Ping：0 ms", font=("Arial", 12))
        self.lbl_ping.pack(pady=5)

        self.frame_bottom = tk.Frame(self)
        self.frame_bottom.pack(pady=20)

        self.btn_start = tk.Button(self.frame_bottom, text="开始测速", font=("Arial", 12), command=self.start_speed_test)
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_history = tk.Button(self.frame_bottom, text="查看历史记录", font=("Arial", 12), command=self.view_history)
        self.btn_history.pack(side=tk.RIGHT, padx=10)

        self.is_speed_test_running = False
        self.speed_test_interval = 10  # 测速时间间隔（秒）
        self.speed_test_timer = None

        self.update_speed_test_results()

    def perform_speed_test(self):
        try:
            messagebox.showinfo("SpeedTest", "测速进行中，请稍候...")
            speed_test_cmd = ["speedtest-cli"]
            if platform.system() != "Windows":
                speed_test_cmd.insert(0, sys.executable)  # 在Linux/macOS上使用Python解释器执行speedtest-cli

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
            self.update_results(download_speed, upload_speed, ping)
            self.save_results_to_file(download_speed, upload_speed, ping)
        except Exception as e:
            messagebox.showerror("Error", f"测速出错：{e}")

    def start_speed_test(self):
        if not self.is_speed_test_running:
            self.is_speed_test_running = True
            threading.Thread(target=self.run_speed_test, daemon=True).start()

    def run_speed_test(self):
        while self.is_speed_test_running:
            self.perform_speed_test()
            time.sleep(self.speed_test_interval)

    def stop_speed_test(self):
        self.is_speed_test_running = False

    def update_results(self, download_speed, upload_speed, ping):
        self.lbl_download.config(text=f"下载速度：{download_speed:.2f} Mbps")
        self.lbl_upload.config(text=f"上传速度：{upload_speed:.2f} Mbps")
        self.lbl_ping.config(text=f"Ping：{ping:.2f} ms")

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

    def update_speed_test_results(self):
        self.perform_speed_test()  # 进行初始测速
        self.speed_test_timer = self.after(self.speed_test_interval * 1000, self.update_speed_test_results)

if __name__ == "__main__":
    app = SpeedTestApp()
    app.mainloop()
