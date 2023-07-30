import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QRect, QPoint, QPropertyAnimation, QObject, pyqtProperty, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QPainterPath, QIcon

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
                background-color: rgba(255, 255, 255, 200);
            }

            QPushButton {
                border: none; /* 移除按钮的边框 */
                background-color: #007BFF;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #0056b3; /* 鼠标悬停时按钮的背景色 */
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

class CloseButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.animation = QPropertyAnimation(self, b"_angle")
        self.animation.setDuration(1000)
        self.animation.setLoopCount(-1)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the blue rounded rectangle background
        radius = 50
        rect = QRectF(0.0, 0.0, 35.0, 35.0)
        painter_path = QPainterPath()
        painter_path.addRoundedRect(rect, radius, radius)

        color = QColor("#007BFF")  # Blue color for the rounded rectangle background
        painter.setPen(QPen(color, 2))
        painter.setBrush(color)
        painter.drawPath(painter_path)

        # Draw the red cross (X)
        size = 10
        pen = QPen(Qt.red, 2)
        painter.setPen(pen)

        center_x = int(rect.width() / 2)
        center_y = int(rect.height() / 2)

        painter.drawLine(center_x - size, center_y - size, center_x + size, center_y + size)
        painter.drawLine(center_x - size, center_y + size, center_x + size, center_y - size)

    def sizeHint(self):
        return self.size()

    @pyqtProperty(int)
    def _angle(self):
        return self.__angle

    @_angle.setter
    def _angle(self, value):
        self.__angle = value
        self.update()

    def enterEvent(self, event):
        self.animation.start()

    def leaveEvent(self, event):
        self.animation.stop()

    close_clicked = pyqtSignal()  # 自定义信号 close_clicked

    def mousePressEvent(self, event):
        self.close_clicked.emit()  # 触发 close_clicked 信号

class SpeedTestApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SpeedTest GUI")
        self.setGeometry(100, 100, 400, 200)

        self.setWindowFlags(Qt.FramelessWindowHint)  # 去掉窗口边框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 开启窗口透明效果

        main_layout = QVBoxLayout()

        # 添加右上角的小红叉
        close_button = CloseButton(self)
        close_button.close_clicked.connect(self.close)  # 关联 close_clicked 信号到关闭窗口槽函数
        main_layout.addWidget(close_button, alignment=Qt.AlignTop | Qt.AlignRight)

        self.card = SpeedTestCard()
        main_layout.addWidget(self.card)

        self.setLayout(main_layout)

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)

    def mouseReleaseEvent(self, event):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    speed_test_app = SpeedTestApp()
    speed_test_app.show()
    sys.exit(app.exec_())
