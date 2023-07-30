import os
import sys
import time
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def perform_speed_test():
    try:
        messagebox.showinfo("SpeedTest", "测速进行中，请稍候...")
        if platform.system() == "Windows":
            speed_test_cmd = ["speedtest-cli"]
        else:
            speed_test_cmd = ["/usr/local/bin/speedtest-cli"]  # 根据speedtest-cli安装路径修改此处
        speed_test_result = subprocess.run(speed_test_cmd, capture_output=True)
        output = speed_test_result.stdout.decode("utf-8")
        download_speed, upload_speed, ping = 0.0, 0.0, 0.0
        for line in output.split("\n"):
            if "Download:" in line:
                download_speed = float(line.split()[1])
            elif "Upload:" in line:
                upload_speed = float(line.split()[1])
            elif "Ping:" in line:
                ping = float(line.split()[1])
        update_results(download_speed, upload_speed, ping)
        save_results_to_file(download_speed, upload_speed, ping)
    except Exception as e:
        messagebox.showerror("Error", f"测速出错：{e}")

def save_results_to_file(download_speed, upload_speed, ping):
    with open("speedtest_results.txt", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"下载速度：{download_speed:.2f} Mbps, "
                f"上传速度：{upload_speed:.2f} Mbps, "
                f"Ping：{ping:.2f} ms\n")

def view_history():
    if os.path.isfile("speedtest_results.txt"):
        with open("speedtest_results.txt", "r") as f:
            history_text = f.read()
        messagebox.showinfo("历史测速记录", history_text)
    else:
        messagebox.showerror("Error", "未找到历史测速记录。")

def start_speed_test():
    threading.Thread(target=perform_speed_test, daemon=True).start()

def update_results(download_speed, upload_speed, ping):
    lbl_download.config(text=f"下载速度：{download_speed:.2f} Mbps")
    lbl_upload.config(text=f"上传速度：{upload_speed:.2f} Mbps")
    lbl_ping.config(text=f"Ping：{ping:.2f} ms")

# 创建主界面部分
root = tk.Tk()
root.title("SpeedTest in Python - 简体中文版")
root.geometry("400x300")

frame_top = tk.Frame(root)
frame_top.pack(pady=20)

lbl_download = tk.Label(frame_top, text="下载速度：0 Mbps", font=("Arial", 12))
lbl_download.pack(pady=5)

lbl_upload = tk.Label(frame_top, text="上传速度：0 Mbps", font=("Arial", 12))
lbl_upload.pack(pady=5)

lbl_ping = tk.Label(frame_top, text="Ping：0 ms", font=("Arial", 12))
lbl_ping.pack(pady=5)

frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=20)

btn_start = tk.Button(frame_bottom, text="开始测速", font=("Arial", 12), command=start_speed_test)
btn_start.pack(side=tk.LEFT, padx=10)

btn_history = tk.Button(frame_bottom, text="查看历史记录", font=("Arial", 12), command=view_history)
btn_history.pack(side=tk.RIGHT, padx=10)

root.mainloop()
