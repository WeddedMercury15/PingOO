import sys
import speedtest
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, QGroupBox, QHBoxLayout, QScrollArea
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class SpeedTestThread(QThread):
    speed_test_done = pyqtSignal(str)

    def run(self):
        st = speedtest.Speedtest()
        st.get_best_server()
        st.download()
        st.upload()
        result = st.results.dict()
        download_speed = result["download"] / 10**6
        upload_speed = result["upload"] / 10**6
        ping = result["ping"]
        self.speed_test_done.emit(f"下载速度: {download_speed:.2f} Mbps\n上传速度: {upload_speed:.2f} Mbps\nPing值: {ping:.2f} ms")


class SpeedTestApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SpeedTest GUI")
        self.setGeometry(100, 100, 400, 200)

        main_layout = QVBoxLayout()
        self.central_widget = QWidget(self)
        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        card_layout = QHBoxLayout(content_widget)
        card_layout.setAlignment(Qt.AlignLeft)

        font = QFont("Arial", 12)

        self.result_label = QLabel("点击 '开始测试' 开始测速", self)
        self.result_label.setFont(font)
        card_layout.addWidget(self.result_label)

        self.start_button = QPushButton("开始测试", self)
        self.start_button.setFont(font)
        self.start_button.clicked.connect(self.start_speed_test)
        card_layout.addWidget(self.start_button)

    def start_speed_test(self):
        self.start_button.setEnabled(False)
        self.result_label.setText("正在进行测速...")
        self.thread = SpeedTestThread()
        self.thread.speed_test_done.connect(self.on_speed_test_done)
        self.thread.finished.connect(self.on_speed_test_finished)
        self.thread.start()

    def on_speed_test_done(self, result):
        self.result_label.setText(result)

    def on_speed_test_finished(self):
        self.start_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    speed_test_app = SpeedTestApp()
    speed_test_app.show()
    sys.exit(app.exec_())
