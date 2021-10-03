import sys
from Inari import InariWidget, InariCommandInterpreter

from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem, QFrame, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QGraphicsSceneMouseEvent, QGraphicsColorizeEffect, QGraphicsEffect, QGraphicsBlurEffect
from PySide2.QtGui import QIcon, QPainter, QTransform, QBrush, QColor, QWheelEvent, QCursor, QImage, QPixmap, QBitmap
from PySide2.QtCore import Qt, QObject, QPoint, QPointF
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Khaos System | Inari")
        self.setGeometry(300, 50, 766, 980)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        inariWidget = InariWidget(self, InariCommandInterpreter())

        layout = QtWidgets.QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(inariWidget)
        self.setLayout(layout)

        self.show()


if __name__ == "__main__":
    myApp = QtWidgets.QApplication(sys.argv)
    window = Window()

myApp.exec_()
sys.exit(0)

