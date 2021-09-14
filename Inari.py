from os import terminal_size
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import typing
import json
import sys



class InariGraphicsSvgItem(QtSvg.QGraphicsSvgItem):
    _useComplexHoverCollision: bool = False
    _hovering: bool = False
    _clicking: bool = False
    _alphaMask: QtGui.QImage = QtGui.QImage()

    def __init__(self, fileName: str, parentItem:typing.Optional[QtWidgets.QGraphicsItem]=...) -> None:
        super().__init__(fileName)
        self.setAcceptMouseEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)

    # Overridden from QtSvg.QGraphicsSvgItem
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget = None) -> None:
        # Render a QPixmap from the SVG.
        pixmap = QtGui.QPixmap(painter.device().width(),
                               painter.device().height())
        pixmap.fill(QtCore.Qt.transparent)
        pixmapPainter = QtGui.QPainter()
        pixmapPainter.begin(pixmap)
        pixmapPainter.setRenderHint(QtGui.QPainter.Antialiasing)
        pixmapPainter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.renderer().render(pixmapPainter)
        pixmapPainter.end()

        # Render self.alphaMask; used by self.verifyHover() and mask for the hover effect.
        # One possible optimization to the hover verification process would be to downsize this mask to a lower resolution.
        self._alphaMask = pixmap.toImage().createAlphaMask(
            QtCore.Qt.ImageConversionFlag.AutoColor)

        # Configure and render pixmap to screen.
        # TODO: Implement color event with QImage::applyColorTransform
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        image = pixmap.toImage()
        painter.drawImage(self.boundingRect(), image)

        # painter.drawImage(self.boundingRect(), self.alphaMask)
        if self._hovering or self.isSelected():
            # TODO: Make the clipping mask scale with the widget
            """clippingMask = QtGui.QRegion(QtGui.QBitmap().fromImage(self.alphaMask))
            painter.setClipRegion(clippingMask)"""
            if self._clicking == True:
                painter.fillRect(self.boundingRect(), QtGui.QColor(255, 255, 255, 150))
            else:
                painter.fillRect(self.boundingRect(), QtGui.QColor(255, 255, 255, 100))

        # DEBUG
        # painter.drawImage(self.boundingRect(), self.alphaMask)
        # painter.drawRect(painter.viewport())

    # region Methods related to (verified) mouse events; you can override these :)
    def setAcceptMouseEvents(self, enabled: bool) -> bool:
        if enabled:
            self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.AllButtons)
            self.setAcceptHoverEvents(True)
        else:
            self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
            self.setAcceptHoverEvents(False)

    def verifyQtHoverEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> bool:
        if self._useComplexHoverCollision:
            return (self._alphaMask.pixelColor(event.pos().x(), event.pos().y()).red() < 1)
        else:
            return True

    def verifiedHoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        pass

    def verifiedHoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def verifiedHoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        pass 

    def verifiedMousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)

    def verifiedMouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)

    # endregion

    # region We'll fire you if you override these methods.
    def hoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self.verifyQtHoverEvent(event):
            self.verifiedHoverMoveEvent(event)
            if not self._hovering:
                self.__hovering = True
                self.verifiedHoverEnterEvent(event)
        else:
            if self._hovering:
                self._hovering = False
                self.verifiedHoverLeaveEvent(event)

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self.verifyQtHoverEvent(event):
            if not self._hovering:
                self._hovering = True
                self.verifiedHoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        if self._hovering:
            self._hovering = False
            self.verifiedHoverLeaveEvent(event)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self._hovering:
            self._clicking = True
            event.setAccepted(True)
            self.verifiedMousePressEvent(event)
        else:
            raise NotImplementedError

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self._clicking:
            self._clicking = False
            self.verifiedMouseReleaseEvent(event)
        else:
            raise NotImplementedError
    # endregion


class InariBackdropItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, x: float, y: float, w: float, h: float, parent: typing.Optional[QtWidgets.QGraphicsItem]) -> None:
        super().__init__(x, y, w, h, parent=parent)


class InariQGraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parentItem: QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)
        QtCore.QObject.connect(self, QtCore.SIGNAL("selectionChanged()"), self.selectionChangedSignal)

    def selectionChangedSignal(self):
        pass # Update in Maya

class InariQGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, scene: QtWidgets.QGraphicsScene, parent: QtWidgets.QWidget = None):
        super().__init__(scene, parent)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setGeometry(0, 0, 300, 300)
        self.setBackgroundBrush(QtGui.QColor(45, 45, 45))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyPressEvent(event)

        if bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyReleaseEvent(event)

        if not bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)

        

    # Overridden from QtWidgets.QGraphicsView
    def wheelEvent(self, event: QtGui.QWheelEvent):
        if event.delta() > 0:
            self.scale(1.05, 1.05)
        else:
            self.scale(0.95, 0.95)


class InariWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)

        self.setStyleSheet("background-color: black")

        self.scene = InariQGraphicsScene(self)
        self.view = InariQGraphicsView(self.scene, self)
        self.view.show()

        layout = QtWidgets.QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def Load(self, filepath):
        with open(filepath, "r") as file:
            obj = json.loads(file.read())

            for element in obj["elements"]:
                print("Adding element:")

                item = None
                if "imagePath" in element:
                    print(" - imagePath: " + str(element["imagePath"]))
                    item = InariGraphicsSvgItem(element["imagePath"], self)
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

                self.scene.addItem(item)

            # TODO: set the starting position, unhiding and monitoring the scrollbars might be a good starting point
            self.view.horizontalScrollBar().setRange(0, 1)
            self.view.horizontalScrollBar().setValue(0.5)


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Khaos System | Inari")
        self.setGeometry(300, 50, 766, 980)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        inariWidget = InariWidget(self)
        inariWidget.Load("./example.json")

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
