from os import terminal_size
from PySide2.QtCore import QPoint

from PySide2.QtWidgets import QGraphicsItem
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import typing
import json

# TODO: Set propper stating position.
# TODO: Alt mouse wheel always zoom out.
# TODO: Click+dragging a locator moves it.

class InariCommandInterpreter():
    def Host_SetSelection(self, items:typing.List[str]) -> None:
        print("Host_SetSelection")

    def Host_GetSelection(self) -> typing.List[str]:
        print("Host_GetSelection")
        return []

    def Host_SetPosition(self, item:str, x:float, y:float, z:float, worldSpace:bool=False, relative:bool=True) -> None:
        print("Host_SetPosition")

    def Host_GetPosition(self, item:str, worldSpace:bool=False, relative:bool=True) -> typing.List[float]:
        print("Host_GetPosition")
        return [0, 0, 0]


class InariGraphicsSvgItem(QtSvg.QGraphicsSvgItem):
    _useComplexHoverCollision: bool = False
    _isUnderMouse: bool = False
    _isClicking: bool = False
    _alphaMask: QtGui.QImage = QtGui.QImage()
    _commandInterpreter:InariCommandInterpreter = None 
    _name = None
    _initialLeftClickPosition = None
    _initialPosition:QtCore.QPoint() = None

    """def sceneEvent(self, event: QtCore.QEvent) -> bool:
        if self.scene.isMoveing
            event.ignore()
        else:
            super().sceneEvent(event)"""

    def __init__(self, fileName: str, commandInterpreter:InariCommandInterpreter=None, parentItem: typing.Optional[QtWidgets.QGraphicsItem] = ...) -> None:
        super().__init__(fileName)

        self._commandInterpreter = commandInterpreter
        # TODO: This is temporary set in Load, fix
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        # self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.AllButtons)
        # self.setAcceptHoverEvents(True)

    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter):
        self._commandInterpreter = commandInterpreter

    def setName(self, name:str) -> str:
        self._name = name

    def name(self) -> str:
        return self._name

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

        if (event.button() == QtCore.Qt.LeftButton):
            self.scene().registerSceneMouseMoveEventListener(self)
            self._initialLeftClickPosition = event.scenePos()
            pos = self._commandInterpreter.Host_GetPosition(self.name(), worldSpace=False)
            self._initialPosition = QtCore.QPointF(pos[0], pos[1])

        self._isClicking = True
        self.update()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        if (event.button() == QtCore.Qt.LeftButton):
            self.scene().unregisterSceneMouseMoveEventListener(self)

        self._isClicking = False
        self.update()

    def hoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        super().hoverEnterEvent(event)
        self._isUnderMouse = True

    def hoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        self._isUnderMouse = False

    def sceneMouseMoveEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent) -> None:
        delta = (event.scenePos() - self._initialLeftClickPosition)
        delta.setY(delta.y() * -1)
        delta /= 100

        newPosition = self._initialPosition + delta

        print(delta)

        self._commandInterpreter.Host_SetPosition(self.name(), newPosition.x(), newPosition.y(), 0, worldSpace=False, relative=False)

class InariLocator(InariGraphicsSvgItem):
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)


class InariQGraphicsScene(QtWidgets.QGraphicsScene):
    _shouldPropagateEventsToItems: bool = True
    _commandInterpreter:InariCommandInterpreter = None
    _sceneMouseMoveEventListeners:typing.List[InariGraphicsSvgItem] = []

    def __init__(self, parentItem: QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)
        QtCore.QObject.connect(self, QtCore.SIGNAL("selectionChanged()"), self.selectionChangedSignal)
        
    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter):
        self._commandInterpreter = commandInterpreter

    def registerSceneMouseMoveEventListener(self, item: InariGraphicsSvgItem) -> None:
        self._sceneMouseMoveEventListeners.append(item)

    def unregisterSceneMouseMoveEventListener(self, item: InariGraphicsSvgItem) -> None:
        self._sceneMouseMoveEventListeners.remove(item)

    def mouseMoveEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent):
        for listener in self._sceneMouseMoveEventListeners:
            listener.sceneMouseMoveEvent(event)

        return super().mouseMoveEvent(event)

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
        items = [item.name() for item in self.selectedItems() if isinstance(item, InariLocator)]
        self._commandInterpreter.Host_SetSelection(items)

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
    _commandInterpreter:InariCommandInterpreter = None

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

    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter):
        self._commandInterpreter = commandInterpreter

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
                # TODO: Make zooming slower when distanceToOrigin increases
                # Capture data for correcting view translation offset.
                oldSceneSpaceOriginPoint = self.mapToScene(self._lastRightMousePressPosition)
                ### Calculate scaleing factor
                cursorPoint = QtGui.QVector2D(event.pos())
                originPoint = QtGui.QVector2D(self._lastRightMousePressPosition)
                orientationPoint = originPoint + QtGui.QVector2D(1, 1)
                orientationVector = orientationPoint - originPoint
                cursorVector = orientationPoint - cursorPoint
                # Introduce a small constant value if the vector length is 0.
                # This is needed since the vector normalization calulation will cause an error if the vector has a length of 0
                orientationVector = (orientationVector + QtGui.QVector2D(0.001, 0.001)) if bool(orientationVector.length() == 0) else orientationVector
                cursorVector = (cursorVector + QtGui.QVector2D(0.001, 0.001)) if bool(cursorVector.length() == 0) else cursorVector
                orientationUnitVector = orientationVector.normalized() # Normalization calulation
                cursorUnitVector = cursorVector.normalized() # Normalization calulation
                dotProduct = QtGui.QVector2D.dotProduct(orientationUnitVector, cursorUnitVector)
                distanceToOrigin = originPoint.distanceToPoint(cursorPoint)
                globalScaleFactor = 1 - (dotProduct * distanceToOrigin * 0.0015) # dot * dist * zoomSensitivity
                ### Create the actial matrix for applying the scale; the initial scaleing factors should be set on mouse putton pressed.
                finalHorizontalScalingFactor = min(max(self._initialRightMousePressHorizontalScalingFactor * globalScaleFactor, 0.2), 2)
                finalVerticalScalingFactor = min(max(self._initialRightMousePressVerticalScalingFactor * globalScaleFactor, 0.2), 2)
                # print(finalHorizontalScalingFactor)
                # print(finalVerticalScalingFactor) 
                horizontalScalingFactor = finalHorizontalScalingFactor # FIXME: This should possibly not by multiplying since it wont be linear; i think...
                verticalScalingFactor = finalVerticalScalingFactor # FIXME: If addition or subtraction is the correct way to go, the globalScaleFactor range need to change.
                verticalShearingFactor = self.matrix().m12()
                horizontalShearingFactor = self.matrix().m21()
                self.setMatrix(QtGui.QMatrix(horizontalScalingFactor, verticalShearingFactor, horizontalShearingFactor, verticalScalingFactor, self.matrix().dx(), self.matrix().dy()))
                # Correct view translation offset.
                newSceneSpaceOriginPoint = self.mapToScene(self._lastRightMousePressPosition)
                translationDelta = newSceneSpaceOriginPoint - oldSceneSpaceOriginPoint;
                self.translate(translationDelta.x(), translationDelta.y())
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
    _commandInterpreter:InariCommandInterpreter = InariCommandInterpreter()

    def __init__(self, parent: QtCore.QObject, commandInterpreter:InariCommandInterpreter):
        super().__init__(parent)

        self._commandInterpreter = commandInterpreter

        self.scene = InariQGraphicsScene(self)
        self.scene.setCommandInterpreter(self._commandInterpreter)
        self.view = InariQGraphicsView(self.scene, self)
        self.view.show()

        layout = QtWidgets.QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def SetSelection(self, items:typing.List[str]) -> None:
        self.scene.clearSelection()
        for item in self.scene.items():
            if isinstance(item, InariLocator):
                if item.name() in items:
                    item.setSelected(True)

    def Load(self, filepath):
        with open(filepath, "r") as file:
            obj = json.loads(file.read())

            for element in obj["elements"]:
                print("Adding element:")

                item = None
                if "imagePath" in element:
                    print(" - imagePath: " + str(element["imagePath"]))
                    item = InariLocator("C:/Dev/Inari/" + element["imagePath"], self._commandInterpreter, self)
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
                    item.setName(element["command"])
                else:
                    item.setAcceptedMouseButtons(
                        QtCore.Qt.MouseButton.NoButton)
                    item.setAcceptHoverEvents(False)

                self.scene.addItem(item)        