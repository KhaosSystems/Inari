from os import terminal_size
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QStyleOptionGraphicsItem, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem, QFrame, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QGraphicsSceneMouseEvent, QGraphicsColorizeEffect, QGraphicsEffect, QGraphicsBlurEffect
from PySide2.QtGui import QIcon, QPainter, QTransform, QBrush, QColor, QWheelEvent, QCursor, QImage, QPixmap
from PySide2.QtCore import Qt, QObject, QPoint, QPointF
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import json
import sys

# Problems:
# - PySide is quite slow
# - Hover effect seems impossible to do without C++
# - Hover event is based on bounding box, not transparent
# - Pixmap dosn't seem to be exposed to QGraphicsSvgItem

# override decorator for clarity
# TODO: Do propper implementation with error checking and and to KhaosSystemsUtils.py


def override(f):
    return f


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
            pixmap = self.sourcePixmap(Qt.LogicalCoordinates, offset)
            painter.drawPixmap(offset, pixmap)
        else:
            # Draw pixmap in device coordinates to avoid pixmap scaling;
            pixmap = self.sourcePixmap(Qt.DeviceCoordinates, offset)
            painter.setWorldTransform(QTransform())
            painter.drawPixmap(offset, pixmap)


class InariGraphicsSvgItem(QGraphicsSvgItem):
    # TODO: Remove posX and posY from constructor, this is TMP api stuff
    def __init__(self, fileName: str):
        super().__init__(fileName)

        self.command = None
        self.hovering = False

        self.setAcceptHoverEvents(1)

    # override; add highlighting stuff
    # def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget:QWidget=None):

    def setOnClickCommand(self, command: str):
        self.command = command

    @override
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget = None) -> None:
        svgRenderer = self.renderer()

        svgRenderer.render(painter, self.boundingRect())

        # debug bounding rect
        painter.drawRect(self.boundingRect())

        # used by self.verifyHover()
        pixmap = QPixmap(self.boundingRect().size().toSize())
        pixmap.fill(Qt.transparent)
        pixmapPainter = QtGui.QPainter(pixmap)
        svgRenderer.render(pixmapPainter)
        pixmapPainter.end()
        self.hoverMask = pixmap.toImage().createAlphaMask(
            QtCore.Qt.ImageConversionFlag.AutoColor)

    # region Custom verified mouse events
    # the default cursor hovering logic does not include transparency, this function should help verifying the hovering state
    def verifyHover(self, cursorX: int, cursorY: int) -> bool:
        return (self.hoverMask.pixelColor(cursorX, cursorY).red() < 1)

    def verifiedHoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverMoveEvent(event)

    def verifiedHoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverEnterEvent(event)

    def verifiedHoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)

    def verifiedMousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)

        if self.command:
            print(self.command)

    def verifiedMouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        super().mouseReleaseEvent(event)
    # endregion

    # region Overridden QT mouse events
    @override
    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        if self.verifyHover(event.pos().x(), event.pos().y()):
            self.verifiedHoverMoveEvent(event)

            if self.hovering == False:
                self.hovering = True
                self.verifiedHoverEnterEvent(event)
        else:
            if self.hovering == True:
                self.hovering = False
                self.verifiedHoverLeaveEvent(event)

            return

    @override
    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self.verifyHover(event.pos().x(), event.pos().y()):
            if self.hovering == False:
                self.hovering = True
                self.verifiedHoverEnterEvent(event)

    @override
    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self.hovering == True:
            self.hovering = False
            self.verifiedHoverLeaveEvent(event)

    @override
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self.verifyHover(event.pos().x(), event.pos().y()):
            self.verifiedMousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.verifyHover(event.pos().x(), event.pos().y()):
            self.verifiedMouseReleaseEvent(event)
    # endregion


class InariQGraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: QWidget = None):
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
    def wheelEvent(self, event: QWheelEvent):
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

        view = InariQGraphicsView(self.scene, self)
        view.show()

        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(view)
        self.setLayout(layout)

    def Load(self, filepath):
        with open(filepath, "r") as file:
            obj = json.loads(file.read())

            for element in obj["elements"]:
                print("Adding element:")

                item = None
                if "imagePath" in element:
                    print(" - imagePath: " + str(element["imagePath"]))
                    item = InariGraphicsSvgItem(element["imagePath"])
                else:
                    print("[ERROR] All elements need an \"imagePath\".")
                    return

                if "positionX" in element:
                    print(" - positionX: " + str(element["positionX"]))
                    item.setX(element["positionX"])

                if "positionY" in element:
                    print(" - positionY: " + str(element["positionY"]))
                    item.setY(element["positionY"])

                if "flip" in element:
                    print(" - flip: " + str(element["flip"]))
                    if element["flip"] == True:
                        transform = item.transform()
                        transform.scale(-1, 1)
                        item.setX(item.x() + item.boundingRect().width())
                        item.setTransform(transform)

                if "command" in element:
                    print(" - command: " + str(element["command"]))
                    item.setOnClickCommand(element["command"])

                print(item.boundingRect().width())

                self.scene.addItem(item)


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Khaos System | Inari")
        self.setGeometry(300, 50, 766, 980)
        self.setWindowIcon(QIcon("icon.png"))

        inari = Inari(self)
        inari.Load("./example.json")
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
