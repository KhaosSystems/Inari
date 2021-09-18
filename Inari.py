from os import terminal_size
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import typing
import json
import sys
import time

# TODO: When alt is down, don't send mouse events to items.
# TODO: Set propper stating position


class InariGraphicsSvgItem(QtSvg.QGraphicsSvgItem):
    _useComplexHoverCollision: bool = False
    _isUnderMouse: bool = False
    _isClicking: bool = False
    _alphaMask: QtGui.QImage = QtGui.QImage()

    """def sceneEvent(self, event: QtCore.QEvent) -> bool:
        if self.scene.isMoveing
            event.ignore()
        else:
            super().sceneEvent(event)"""

    def __init__(self, fileName: str, parentItem: typing.Optional[QtWidgets.QGraphicsItem] = ...) -> None:
        super().__init__(fileName)
        # TODO: This is temporary set in Load, fix
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        # self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.AllButtons)
        # self.setAcceptHoverEvents(True)

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget = None) -> None:
        # Render SVG to pixmap.
        pixmap = QtGui.QPixmap(painter.device().width(), painter.device().height())
        pixmap.fill(QtCore.Qt.transparent)
        pixmapPainter = QtGui.QPainter()
        pixmapPainter.begin(pixmap)
        pixmapPainter.setRenderHint(QtGui.QPainter.Antialiasing)
        pixmapPainter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.renderer().render(pixmapPainter)
        pixmapPainter.end()

        # Render self.alphaMask used to verify hover events against transparency.
        # One possible optimization to the hover verification process would be to downsize this mask to a lower resolution.
        self._alphaMask = pixmap.toImage().createAlphaMask(QtCore.Qt.ImageConversionFlag.AutoColor)

        # Configure and render pixmap to screen.
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        image = pixmap.toImage()
        painter.drawImage(self.boundingRect(), image)

        # Highlighting. TODO: Find a way of highlighting without using screen.
        if self.isUnderMouse() or self.isSelected():
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)
            painter.drawImage(self.boundingRect(), image)
            if self.isClicking() == True:
                painter.drawImage(self.boundingRect(), image)

    def isUnderMouse(self) -> bool:
        return self._isUnderMouse

    def isClicking(self) -> bool:
        return self._isClicking

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        self._isClicking = True
        self.update()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self._isClicking = False
        self.update()

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        super().hoverEnterEvent(event)
        self._isUnderMouse = True

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        self._isUnderMouse = False


class InariQGraphicsScene(QtWidgets.QGraphicsScene):
    _shouldPropagateEventsToItems:bool = True

    def __init__(self, parentItem: QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)
        QtCore.QObject.connect(self, QtCore.SIGNAL("selectionChanged()"), self.selectionChangedSignal)

    def SetShouldPropagateEventsToItems(self, shouldPropagateEventsToItems:bool) -> None:
        self._shouldPropagateEventsToItems = shouldPropagateEventsToItems

    def event(self, event: QtCore.QEvent) -> bool:
        if self._shouldPropagateEventsToItems:
            super().event(event)
        else:
            return True

    def addItem(self, item: QtWidgets.QGraphicsItem) -> None:
        super().addItem(item)
        self.setSceneRect(self.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(1024*128, 1024*128, 1024*128, 1024*128)))

    def selectionChangedSignal(self) -> None:
        pass  # Update in Maya

    def selectionItemsBoundingRect(self):
        # Does not take untransformable items into account.
        boundingRect = QtCore.QRectF()
        items = self.selectedItems()
        for item in items:
            boundingRect |= item.sceneBoundingRect()
        return boundingRect


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

        if event.key() == QtCore.Qt.Key_F:
            if len(self.scene().selectedItems()) > 0:
                selectionBounds = self.scene().selectionItemsBoundingRect()
            else:
                selectionBounds = self.scene().itemsBoundingRect()
            selectionBounds = selectionBounds.marginsAdded(QtCore.QMarginsF(64, 64, 64, 64))
            self.fitInView(selectionBounds, QtCore.Qt.KeepAspectRatio)

        # Handle KeyboardModifiers
        if bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            self.scene().SetShouldPropagateEventsToItems(False)
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyReleaseEvent(event)

        # Handle KeyboardModifiers
        if not bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            self.scene().SetShouldPropagateEventsToItems(True)
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

                # TODO: This should happen inside the item, not here
                if "command" in element:
                    item.setFlag(
                        QtWidgets.QGraphicsItem.ItemIsSelectable, True)
                    item.setAcceptedMouseButtons(
                        QtCore.Qt.MouseButton.AllButtons)
                    item.setAcceptHoverEvents(True)
                else:
                    item.setAcceptedMouseButtons(
                        QtCore.Qt.MouseButton.NoButton)
                    item.setAcceptHoverEvents(False)

                self.scene.addItem(item)
        


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
