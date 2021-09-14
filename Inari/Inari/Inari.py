from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import sys

class InariWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)
    
class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Khaos System | Inari")
        self.setGeometry(300, 50, 766, 980)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        inariWidget = InariWidget(self)

        layout = QtWidgets.QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(inariWidget)
        self.setLayout(layout)

        self.show()

if __name__ == "__main__":
    myApp = QtWidgets.QApplication(sys.argv)
    window = Window()

myApp.exec_()
sys.exit(0)
