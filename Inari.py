from os import terminal_size
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import typing
import json
import sys
import time
import math
import numpy as np  

# TODO: Set propper stating position
# Alt mouse wheel always zoom out

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
    _shouldPropagateEventsToItems: bool = True

    def __init__(self, parentItem: QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)
        QtCore.QObject.connect(self, QtCore.SIGNAL("selectionChanged()"), self.selectionChangedSignal)

    def SetShouldPropagateEventsToItems(self, shouldPropagateEventsToItems: bool) -> None:
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
    _lastMoveEventPosition:QtCore.QPoint = None
    _lastRightMousePressPosition:QtCore.QPoint = None
    _initialRightMousePressVerticalScalingFactor:float = None
    _initialRightMousePressHorizontalScalingFactor:float = None


    def __init__(self, scene: QtWidgets.QGraphicsScene, parent: QtWidgets.QWidget = None):
        super().__init__(scene, parent)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
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
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyReleaseEvent(event)

        # Handle KeyboardModifiers
        if not bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            self.scene().SetShouldPropagateEventsToItems(True)
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.RightButton:
            self._lastRightMousePressPosition = event.pos()
            self._initialRightMousePressHorizontalScalingFactor = self.matrix().m11()
            self._initialRightMousePressVerticalScalingFactor = self.matrix().m22()

        self._lastLeftMouseZoomFactor = 1
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        # Camera panning and zooming
        if self._lastMoveEventPosition == None:
            self._lastMoveEventPosition = event.pos()
        if self._lastRightMousePressPosition == None:
            self._lastRightMousePressPosition = event.pos()
        if bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            if bool((event.buttons() & QtCore.Qt.MiddleButton) or (event.buttons() & QtCore.Qt.LeftButton)):
                verticalScrollBar = self.verticalScrollBar()
                horizontalScrollBar = self.horizontalScrollBar()
                delta = event.pos() - self._lastMoveEventPosition
                verticalScrollBar.setValue(verticalScrollBar.value() - delta.y())
                horizontalScrollBar.setValue(horizontalScrollBar.value() - delta.x())
            elif bool(event.buttons() & QtCore.Qt.RightButton):
                self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
                """scaleFactor = 0.9999;
                originPoint = np.array((self._lastPressEventPosition.x(), self._lastPressEventPosition.y()))
                cursorPosition = np.array((event.pos().x(), event.pos().y()))
                viewportOffset = np.multiply(originPoint, scaleFactor)
                newViewportCenter = np.add(viewportOffset, cursorPosition)
                self.scale(scaleFactor, scaleFactor)
                self.centerOn(newViewportCenter[0], newViewportCenter[1])"""
                # TODO: Use the starting mouse position as zoom anchor, this requires some manual math the correct the possition
                # Current implementation is quite shitty... Also, the zoom need to be distance based; not an if/else statement.
                """cursorPosition = np.array((event.pos().x(), event.pos().y()))
                originPoint = np.array((self._lastPressEventPosition.x(), self._lastPressEventPosition.y()))
                offsetOriginPoint = originPoint + np.array((-1, 1))
                distance = np.linalg.norm(cursorPosition - originPoint)
                ba = cursorPosition - originPoint
                bc = offsetOriginPoint - originPoint
                cosineAngle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
                angle = np.arccos(cosineAngle)
                zoomFactor = distance if bool(angle >= math.pi/2) else -distance
                print(zoomFactor)
                self._currentLeftMouseButtonZoom += zoomFactor/10000"""
                
                #print("test: " + str(zoomFactor/10000))
                #print(self._currentLeftMouseButtonZoom)
                #self.scale(zoomFactor, zoomFactor)
                # Custom transformation anchor
                """transformationDiff:QtCore.QPoint = self.mapToScene(self.viewport().rect().center()) 
                transformationDiff -= self.mapToScene(self.viewport().mapFromGlobal(QtGui.QCursor.pos()))
                transformationDiff.setX(transformationDiff.x() * zoomFactor)
                transformationDiff.setY(transformationDiff.y() * zoomFactor)
                print(transformationDiff)
                self.scene().addRect(cursorPosition[0] + transformationDiff.x(), cursorPosition[1] + transformationDiff.y(), 10, 10)
                self.centerOn(cursorPosition[0] + transformationDiff.x(), cursorPosition[1] + transformationDiff.y())"""
                """self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)

                zoomInFactor = 1.25;
                zoomOutFactor = 1 / zoomInFactor;

                oldPos = self.mapToScene(event.pos());

                zoomFactor = zoomInFactor;
                if event.angleDelta().y() > 0:
                    zoomFactor = zoomInFactor
                else:
                    zoomFactor = zoomOutFactor
                self.scale(zoomFactor, zoomFactor)

                newPos = self.mapToScene(event.pos())

                delta = newPos - oldPos;
                self.translate(delta.x(), delta.y())"""
                self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
                oldSceneSpaceOriginPoint = self.mapToScene(self._lastRightMousePressPosition)

                cursorPoint = np.array((event.pos().x(), event.pos().y()))
                originPoint = np.array((self._lastRightMousePressPosition.x(), self._lastRightMousePressPosition.y()))
                orientationPoint = np.add(originPoint, np.array((1, 1)))
                orientationVector = np.subtract(orientationPoint, originPoint)
                cursorVector = np.subtract(orientationPoint, cursorPoint)
                orientationUnitVector = orientationVector/np.linalg.norm(orientationVector)
                cursorUnitVector = cursorVector/np.linalg.norm(cursorVector)
                dotProduct = np.dot(orientationUnitVector, cursorUnitVector)
                distance = np.linalg.norm(cursorPoint - originPoint)
                zoomSensitivity = 0.01
                globalScaleFactor = 1 - (dotProduct * distance * zoomSensitivity)
                
                self.scale(globalScaleFactor, globalScaleFactor)

                matrix = self.matrix()
                horizontalScalingFactor = self._initialRightMousePressHorizontalScalingFactor * globalScaleFactor
                verticalScalingFactor = self._initialRightMousePressVerticalScalingFactor * globalScaleFactor
                m12 = matrix.m12()
                m21 = matrix.m21()
                dx = matrix.dx()
                dy = matrix.dy()

                self.setMatrix(QtGui.QMatrix(horizontalScalingFactor, m12, m21, verticalScalingFactor, dx, dy))
                              
                newSceneSpaceOriginPoint = self.mapToScene(self._lastRightMousePressPosition)
                translationDelta = newSceneSpaceOriginPoint - oldSceneSpaceOriginPoint;
                self.translate(translationDelta.x(), translationDelta.y())
                #print(globalScaleFactor)
                #self._lastLeftMouseZoomFactor = globalScaleFactor

                pass
        self._lastMoveEventPosition = event.pos()

        super().mouseMoveEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        event.accept()
        # Mouse wheel zooming
        zoomFactor = 1.05
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        if event.angleDelta().y() > 0:
            self.scale(zoomFactor, zoomFactor)
        else:
            self.scale(1 / zoomFactor, 1 / zoomFactor)
        

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
