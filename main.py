from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
import sys

class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        on_load=self._reload_list,
                                        hover_focus=True,
                                        can_scroll=False,
                                        title="Pingoo 图形化界面 v1.0.0")
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        self._list = ListBox(
            Widget.FILL_FRAME,
            [("TCP", 1), ("UDP", 2), ("ICMP", 3)],
            name="protocols",
            on_change=self._on_pick)
        layout.add_widget(self._list)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()

    def _on_pick(self):
        pass

    def _reload_list(self):
        pass

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

def demo(screen, scene):
    screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
