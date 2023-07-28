import curses

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(1)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    current_row = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        box = stdscr.subwin(h-2, w-2, 1, 1)
        box.box()
        title = "Pingoo 图形化界面 v1.0.0"
        start_x_title = int((w // 2) - (len(title) // 2) - len(title) % 2)
        box.addstr(0, start_x_title, title)
        box.addstr(2, 3, "1. TCP")
        box.addstr(3, 3, "2. UDP")
        box.addstr(4, 3, "3. ICMP")
        if current_row == 0:
            box.attron(curses.color_pair(1))
            box.addstr(2, 3, "1. TCP")
            box.attroff(curses.color_pair(1))
        elif current_row == 1:
            box.attron(curses.color_pair(1))
            box.addstr(3, 3, "2. UDP")
            box.attroff(curses.color_pair(1))
        elif current_row == 2:
            box.attron(curses.color_pair(1))
            box.addstr(4, 3, "3. ICMP")
            box.attroff(curses.color_pair(1))

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < 2:
            current_row += 1
        elif key == ord('\t'):
            # 切换到其他框
            pass

curses.wrapper(main)
