from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QStyleOptionGraphicsItem, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem, QFrame, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QGraphicsSceneMouseEvent, QGraphicsColorizeEffect, QGraphicsEffect, QGraphicsBlurEffect
from PySide2.QtGui import QIcon, QPainter, QTransform, QBrush, QColor, QWheelEvent
from PySide2.QtCore import Qt, QObject, QPoint, QPointF
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer

import sys


class InariGraphicsBrightenEffect(QGraphicsEffect):
    def __init__(self):
        super().__init__()

    def setBrightness(self, brightness):
        pass

    # override
    def draw(self, painter: QPainter):
        offset = QPoint()

        if self.sourceIsPixmap():
            # No point in drawing in device coordinates (pixmap will be scaled anyways).
            pixmap = self.sourcePixmap(Qt.LogicalCoordinates, offset);
            painter.drawPixmap(offset, pixmap)
        else:
             # Draw pixmap in device coordinates to avoid pixmap scaling;
            pixmap = self.sourcePixmap(Qt.DeviceCoordinates, offset)
            painter.setWorldTransform(QTransform())
            painter.drawPixmap(offset, pixmap)


class InariGraphicsSvgItem(QGraphicsSvgItem):
    # TODO: Remove posX and posY from constructor, this is TMP api stuff
    def __init__(self, fileName: str, posX: float = 0, posY: float = 0, command:str = None):
        super().__init__(fileName)

        self.command = command
        self.setSelected(True)
        self.setPos(posX, posY)
        self.setAcceptHoverEvents(1)

    # override; add highlighting stuff
    # def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget:QWidget=None):
        
    # override
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        super().hoverEnterEvent(event)
        
        # add hover effect
        effect = InariGraphicsBrightenEffect()
        effect.setBrightness(1.25)
        self.setGraphicsEffect(effect)

    # override
    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        super().hoverLeaveEvent(event)

        self.setGraphicsEffect(None)

    # override
    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        super().hoverEnterEvent(event)

    # override
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        super().mousePressEvent(event)

        # run command
        if self.command:
            print(self.command)

        # add pressed effect
        effect = InariGraphicsBrightenEffect()
        effect.setBrightness(1.5)
        self.setGraphicsEffect(effect)

    # override
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        super().mouseReleaseEvent(event)
        
        self.setGraphicsEffect(None)


class InariQGraphicsView(QGraphicsView):
    def __init__(self, scene:QGraphicsScene, parent:QWidget=None):
        super().__init__(scene, parent)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setGeometry(0, 0, 300, 300)
        self.setBackgroundBrush(QColor(45, 45, 45))
        self.setFrameShape(QFrame.NoFrame)

    # override
    def wheelEvent(self, event:QWheelEvent):
        super().wheelEvent(event)

        if event.delta() > 0:
            self.scale(1.05, 1.05)
        else:
            self.scale(0.95, 0.95)

class Inari(QWidget):
    def __init__(self, parent: QObject):
        super().__init__(parent)

        self.setStyleSheet("background-color: black")

        self.scene = QGraphicsScene(self)
        # lEyebrow
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow.svg"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button01.svg", 14.66, 24.57, "command 1"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button02.svg", 154.64, 31.2, "command 2"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button03.svg", 206.37, 36.7, "command 3"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button04.svg", 58 + (26 * 0), 97, "command 4"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button04.svg", 58 + (26 * 1), 97, "command 5"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button04.svg", 58 + (26 * 2), 97, "command 6"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button04.svg", 58 + (26 * 3), 97, "command 7"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button04.svg", 58 + (26 * 4), 97, "command 8"))
        self.scene.addItem(InariGraphicsSvgItem("./assets/eyebrow_button05.svg", 78, 15, "command 9"))

        view = InariQGraphicsView(self.scene, self)
        view.show()

        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(view)
        self.setLayout(layout)


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Khaos System | Inari")
        self.setGeometry(300, 50, 766, 980)
        self.setWindowIcon(QIcon("icon.png"))

        inari = Inari(self)
        # TODO: Figur out the best API for shipped build

        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(inari)
        self.setLayout(layout)

        self.show()


myApp = QApplication(sys.argv)
window = Window()

myApp.exec_()
sys.exit(0)