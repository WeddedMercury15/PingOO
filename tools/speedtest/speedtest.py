import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, QScrollArea, QFrame
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont

class SpeedTestThread(QThread):
    speed_test_done = pyqtSignal(str)

    def run(self):
        try:
            # 模拟测速过程
            import time
            time.sleep(3)
            result = "测试结果：100 Mbps"
            self.speed_test_done.emit(result)
        except Exception as e:
            self.speed_test_done.emit("测速失败。")

class SpeedTestCard(QFrame):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        font = QFont("Arial", 12)

        vbox = QVBoxLayout()

        self.result_label = QLabel("点击 '开始测试' 开始测速", self)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("QLabel { background-color : white; }")

        self.start_button = QPushButton("开始测试", self)
        self.start_button.setFont(font)
        self.start_button.clicked.connect(self.start_speed_test)

        vbox.addWidget(self.result_label)
        vbox.addWidget(self.start_button)

        self.setLayout(vbox)

        # 设置卡片样式
        self.setStyleSheet(
            """
            QFrame {
                border: 2px solid #007BFF;
                border-radius: 10px;
                padding: 10px;
            }
            """
        )

    def start_speed_test(self):
        self.start_button.setEnabled(False)
        self.result_label.setText("正在进行测速...")
        self.thread = SpeedTestThread()
        self.thread.speed_test_done.connect(self.on_speed_test_done)
        self.thread.start()

    @pyqtSlot(str)
    def on_speed_test_done(self, result):
        self.result_label.setText(result)
        self.start_button.setEnabled(True)

class SpeedTestApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SpeedTest GUI")
        self.setGeometry(100, 100, 400, 200)

        main_layout = QVBoxLayout()

        self.card = SpeedTestCard()
        main_layout.addWidget(self.card)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)

        self.setCentralWidget(scroll_area)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    speed_test_app = SpeedTestApp()
    speed_test_app.show()
    sys.exit(app.exec_())
