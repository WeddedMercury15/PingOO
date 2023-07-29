import sys
import time

# 旋转的碗字符画
bowl_frames = [
    "      .-~~~-.",
    "     /       \\",
    "    |         |",
    "    |         |",
    "     \\       /",
    "      `~-~-~'"
]

def clear_terminal():
    # 清除终端屏幕内容，适用于Linux和Windows
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

def print_bowl_frame(frame):
    # 打印碗的字符画
    clear_terminal()
    for line in frame:
        print(line)

def rotate_bowl():
    # 循环播放旋转的碗
    while True:
        for frame in bowl_frames:
            print_bowl_frame(bowl_frames)
            time.sleep(0.1)
            bowl_frames.append(bowl_frames.pop(0))

if __name__ == "__main__":
    rotate_bowl()
