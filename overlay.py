import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen

class Overlay(QWidget):
    def __init__(self, x, y):
        super().__init__()
        self.target_x = x
        self.target_y = y
        self.initUI()

    def initUI(self):
        # Set window flags for transparency and always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Make the window full screen
        screen = QApplication.primaryScreen()
        size = screen.size()
        self.setGeometry(0, 0, size.width(), size.height())
        
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw red dot
        radius = 5
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0, 255))) # Red, fully opaque
        painter.drawEllipse(QPoint(self.target_x, self.target_y), radius, radius)

    def keyPressEvent(self, event):
        # Close on Escape
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Default position (center of screen if not specified)
    # You can change these coordinates to your desired pixel position
    screen_geom = app.primaryScreen().geometry()
    x = screen_geom.width() // 2
    y = screen_geom.height() // 2
    
    # Example: Override with specific coordinates
    # x = 100
    # y = 100
    
    ex = Overlay(x, y)
    sys.exit(app.exec_())
