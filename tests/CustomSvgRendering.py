from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import sys

try:
    from OpenGL import GL
except ImportError:
    print("Failed to import OpenGl: ")

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 50, 766, 980)
        self.show()
    
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        #painter = QtWidgets.QStylePainter (self)
        #print(painter.style())

        painter = QtGui.QPainter(self)

        svgRenderer = QtSvg.QSvgRenderer()
        svgRenderer.load("../assets/eyebrow.svg")
        viewBox = svgRenderer.viewBox() # this is important!

        gradient = QtGui.QRadialGradient(50, 50, 50, 50, 50)
        gradient.setColorAt(0, QtCore.Qt.red)
        gradient.setColorAt(0, QtCore.Qt.blue)
        painter.setBrush(QtGui.QBrush(gradient))

        svgRenderer.render(painter)    

myApp = QtWidgets.QApplication(sys.argv)
window = Window()
myApp.exec_()
sys.exit(0)
