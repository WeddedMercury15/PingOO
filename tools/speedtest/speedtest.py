import tkinter as tk
from tkinter import messagebox, ttk
import speedtest
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import psutil
import platform
from ttkthemes import ThemedTk
import canvas

# 初始化界面
root = ThemedTk(theme="arc")  # 使用arc主题，你可以根据自己的喜好选择其他主题
root.title("SpeedTest")
root.geometry("800x600")

# 全局变量
servers_var = tk.StringVar()
unit_var = tk.StringVar()
language_var = tk.StringVar()
count_var = tk.StringVar()

# 在全局变量中定义卡片列表和测速结果列表
cards = []
speed_results = []
drag_data = {"x": 0, "y": 0, "item": None}

def create_card(x, y, download_speed, upload_speed, ping, quality):
    card_width = 200
    card_height = 100
    card_color = "lightblue"

    card = canvas.create_rectangle(x, y, x+card_width, y+card_height, fill=card_color)
    canvas.create_text(x+10, y+10, anchor="nw", text=f"下载：{download_speed:.2f} {unit_var.get()}")
    canvas.create_text(x+10, y+30, anchor="nw", text=f"上传：{upload_speed:.2f} {unit_var.get()}")
    canvas.create_text(x+10, y+50, anchor="nw", text=f"Ping：{ping:.2f} ms")
    canvas.create_text(x+10, y+70, anchor="nw", text=f"质量：{quality}")

    # 添加拖拽功能
    canvas.tag_bind(card, "<ButtonPress-1>", on_drag_start)
    canvas.tag_bind(card, "<B1-Motion>", on_drag_motion)
    canvas.tag_bind(card, "<ButtonRelease-1>", on_drag_release)

    return card

def on_drag_start(event):
    global drag_data
    drag_data["item"] = canvas.find_closest(event.x, event.y)[0]
    drag_data["x"] = event.x
    drag_data["y"] = event.y

def on_drag_motion(event):
    global drag_data
    delta_x = event.x - drag_data["x"]
    delta_y = event.y - drag_data["y"]
    canvas.move(drag_data["item"], delta_x, delta_y)
    drag_data["x"] = event.x
    drag_data["y"] = event.y

def on_drag_release(event):
    # 更新卡片顺序
    global cards
    cards = [c for c in cards if c != drag_data["item"]]
    cards.insert(0, drag_data["item"])

def update_card_positions():
    card_x = 10
    card_y = 250
    for card in cards:
        canvas.move(card, card_x - canvas.coords(card)[0], card_y - canvas.coords(card)[1])
        card_x += 220

def update_speed_results(download_speed, upload_speed, ping, quality):
    # 更新测速结果
    speed_results.insert(0, (download_speed, upload_speed, ping, quality))

def update_card_content():
    # 更新卡片内容
    global cards, speed_results
    for i, card in enumerate(cards):
        download_speed, upload_speed, ping, quality = speed_results[i]
        canvas.itemconfig(card, text=f"下载：{download_speed:.2f} {unit_var.get()}\n"
                                    f"上传：{upload_speed:.2f} {unit_var.get()}\n"
                                    f"Ping：{ping:.2f} ms\n"
                                    f"质量：{quality}")

def perform_speed_test():
    try:
        st = speedtest.Speedtest()

        # 获取选项设置
        selected_server = servers_var.get()
        unit = unit_var.get()
        language = language_var.get()
        test_count = int(count_var.get())

        # 设置语言
        st.set_lang(language)

        # 获取测速服务器
        if selected_server == "自动选择":
            st.get_best_server()
        else:
            st.get_servers(servers=[selected_server])

        # 进行测速
        speeds = {"download": [], "upload": [], "ping": []}
        for i in range(test_count):
            st.download(threads=None)
            st.upload(threads=None)
            speeds["download"].append(st.results.download / 10**6 if unit == "Mbps" else st.results.download / 10**3)
            speeds["upload"].append(st.results.upload / 10**6 if unit == "Mbps" else st.results.upload / 10**3)
            speeds["ping"].append(st.results.ping)
            root.after(500, update_progress, i+1, test_count)  # 更新进度条
        # 获取平均测速结果
        download_speed = sum(speeds["download"]) / len(speeds["download"])
        upload_speed = sum(speeds["upload"]) / len(speeds["upload"])
        ping = sum(speeds["ping"]) / len(speeds["ping"])

        # 更新界面
        root.after(100, update_results, download_speed, upload_speed, ping)

        # 记录测速结果到日志文件
        with open("speedtest_log.txt", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {download_speed:.2f}, {upload_speed:.2f}, {ping:.2f}\n")

        # 绘制测速结果图表
        plot_speed_results(speeds)

        # 更新网络质量评估
        quality = evaluate_network_quality(download_speed, upload_speed, ping)

        # 自动保存测速结果
        save_speed_results(download_speed, upload_speed, ping)

        # 更新卡片列表和测速结果列表
        cards.insert(0, create_card(10, 250, download_speed, upload_speed, ping, quality))
        speed_results.insert(0, (download_speed, upload_speed, ping, quality))

        # 更新卡片顺序和内容
        update_card_positions()
        update_card_content()

        btn_start.config(state=tk.NORMAL)
        btn_cancel.config(state=tk.DISABLED)
        progress_bar["value"] = 0  # 重置进度条

    except speedtest.ConfigRetrievalError:
        messagebox.showerror("Error", "无法获取测速服务器列表。请检查网络连接。")
        btn_start.config(state=tk.NORMAL)
        btn_cancel.config(state=tk.DISABLED)
        progress_bar["value"] = 0  # 重置进度条

def save_speed_results(download_speed, upload_speed, ping):
    # 自动保存测速结果到文件
    with open("speedtest_results.txt", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"下载速度：{download_speed:.2f} {unit_var.get()}, "
                f"上传速度：{upload_speed:.2f} {unit_var.get()}, "
                f"Ping：{ping:.2f} ms\n")

def check_network_status():
    while True:
        # 使用ping来检测网络连接状态
        response = os.system("ping -c 1 8.8.8.8")
        if response == 0:
            img_connected = tk.PhotoImage(file="connected.png")
            lbl_connection_status.config(image=img_connected)
        else:
            img_disconnected = tk.PhotoImage(file="disconnected.png")
            lbl_connection_status.config(image=img_disconnected)
        time.sleep(5)

def view_history():
    try:
        with open("speedtest_log.txt", "r") as f:
            history_text = f.read()
        messagebox.showinfo("历史测速记录", history_text)
    except FileNotFoundError:
        messagebox.showerror("Error", "未找到历史测速记录。")

def start_speed_test():
    threading.Thread(target=perform_speed_test).start()

def cancel_speed_test():
    root.after_cancel(update_results)
    btn_start.config(state=tk.NORMAL)
    btn_cancel.config(state=tk.DISABLED)
    progress_bar["value"] = 0  # 重置进度条

def update_results(download_speed, upload_speed, ping):
    lbl_download.config(text=f"下载速度：{download_speed:.2f} {unit_var.get()}")
    lbl_upload.config(text=f"上传速度：{upload_speed:.2f} {unit_var.get()}")
    lbl_ping.config(text=f"Ping：{ping:.2f} ms")

def plot_speed_results(speeds):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(range(1, len(speeds["download"])+1), speeds["download"], label="下载速度")
    ax.plot(range(1, len(speeds["upload"])+1), speeds["upload"], label="上传速度")
    ax.plot(range(1, len(speeds["ping"])+1), speeds["ping"], label="Ping")
    ax.set_xticks(range(1, len(speeds["download"])+1))
    ax.set_xlabel("次数")
    ax.set_ylabel("速度/延迟 (Mbps/ms)")
    ax.legend()
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

def evaluate_network_quality(download_speed, upload_speed, ping):
    # 根据测速结果，评估网络质量
    quality = ""
    if ping > 100:
        quality = "较差"
    elif 50 < ping <= 100:
        quality = "一般"
    elif ping <= 50:
        quality = "良好"

    if download_speed < 10:
        quality += ", 速度较慢"
    elif 10 <= download_speed < 50:
        quality += ", 速度一般"
    elif download_speed >= 50:
        quality += ", 速度快"

    lbl_quality.config(text=f"网络质量：{quality}")
    return quality

# 创建主界面部分
lbl_title = tk.Label(root, text="SpeedTest in Python - 简体中文版", font=("Arial", 16, "bold"))
lbl_title.pack(pady=10)

# ... 其他代码 ...

root.mainloop()
