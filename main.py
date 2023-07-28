import os
import keyboard

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def handle_key_event(event):
    global current_option
    key = event.name

    if key == 'up':  # 上箭头
        current_option = (current_option - 1) % len(options)
    elif key == 'down':  # 下箭头
        current_option = (current_option + 1) % len(options)
    elif key == 'enter':  # 回车键
        selected_option = options[current_option]
        if selected_option == "TCPing":
            os.system("python tools/tcping.py")
        elif selected_option == "UDPing":
            os.system("python tools/udping.py")
        elif selected_option == "ICMPing":
            os.system("python tools/icmping.py")
    elif key == 'esc':  # ESC键
        keyboard.unhook_all()
        return False

    return True

def main():
    global options, current_option
    options = ["TCPing", "UDPing", "ICMPing"]
    current_option = 0

    keyboard.on_press_key('up', handle_key_event)
    keyboard.on_press_key('down', handle_key_event)
    keyboard.on_press_key('enter', handle_key_event)
    keyboard.on_press_key('esc', handle_key_event)

    while True:
        clear_screen()

        # 打印选项列表
        for i, option in enumerate(options):
            if i == current_option:
                print(f"> {option}")
            else:
                print(f"  {option}")

        # 通过捕获按键事件并设置block参数为False来持续处理按键事件
        keyboard.read_event(suppress=True)

if __name__ == "__main__":
    main()
