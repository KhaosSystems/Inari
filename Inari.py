from os import terminal_size
from types import FrameType
from PySide2.QtCore import QPoint, QPointF, QRectF, Qt

from PySide2.QtWidgets import QApplication, QFileDialog, QGraphicsItem, QHBoxLayout, QPushButton, QStyleOptionViewItem, QWidget
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import typing
import json

# TODO: Alt mouse wheel always zoom out.

# region Core
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


class InariScene(QtWidgets.QGraphicsScene):
    _shouldPropagateEventsToItems: bool = True
    _commandInterpreter:InariCommandInterpreter = None
    _sceneMouseMoveEventListeners:typing.List["InariItem"] = []

    def __init__(self, parentItem: QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)
        QtCore.QObject.connect(self, QtCore.SIGNAL("selectionChanged()"), self.selectionChangedSignal)
        
    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter):
        self._commandInterpreter = commandInterpreter

    def registerSceneMouseMoveEventListener(self, item: "InariItem") -> None:
        self._sceneMouseMoveEventListeners.append(item)

    def unregisterSceneMouseMoveEventListener(self, item: "InariItem") -> None:
        self._sceneMouseMoveEventListeners.remove(item)

    def mouseMoveEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent):
        for listener in self._sceneMouseMoveEventListeners:
            listener.sceneMouseMoveEvent(event)

        return super().mouseMoveEvent(event)

    def SetShouldPropagateEventsToItems(self, shouldPropagateEventsToItems: bool) -> None:
        self._shouldPropagateEventsToItems = shouldPropagateEventsToItems

    def event(self, event: QtCore.QEvent) -> bool:
        if self._shouldPropagateEventsToItems:
            return super().event(event)
        else:
            return True

    def addItem(self, item: QtWidgets.QGraphicsItem) -> None:
        super().addItem(item)
        self.setSceneRect(self.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(1024*128, 1024*128, 1024*128, 1024*128)))

    def selectionChangedSignal(self) -> None:
        items = [item.name for item in self.selectedItems() if isinstance(item, InariLocator)]
        self._commandInterpreter.Host_SetSelection(items)

    def selectionItemsBoundingRect(self):
        # Does not take untransformable items into account.
        boundingRect = QtCore.QRectF()
        items = self.selectedItems()
        for item in items:
            boundingRect |= item.sceneBoundingRect()
        return boundingRect


class InariView(QtWidgets.QGraphicsView):
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
        self.setBackgroundBrush(QtGui.QColor(26, 26, 26))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        QtWidgets.QApplication.instance().setStyleSheet("QGraphicsView { background-color: yellow }")

    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter):
        self._commandInterpreter = commandInterpreter

    def frameSelected(self):
        if len(self.scene().selectedItems()) > 0:
            selectionBounds = self.scene().selectionItemsBoundingRect()
        else:
            selectionBounds = self.scene().itemsBoundingRect()
        selectionBounds = selectionBounds.marginsAdded(QtCore.QMarginsF(64, 64+50, 64, 64))
        self.fitInView(selectionBounds, QtCore.Qt.KeepAspectRatio)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyPressEvent(event)

        if event.key() == QtCore.Qt.Key_F:
            self.frameSelected()

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
    inariCommandInterpreter:InariCommandInterpreter = InariCommandInterpreter()

    def __init__(self, parent: QtCore.QObject, commandInterpreter:InariCommandInterpreter):
        super().__init__(parent)

        self.inariCommandInterpreter = commandInterpreter

        self.inariScene = InariScene(self)
        self.inariScene.setCommandInterpreter(self.inariCommandInterpreter)
        self.inariView = InariView(self.inariScene, self)
        self.inariView.move(0, 0)
        self.inariView.show()

        self.toolbarWidget = InariToolbarWidget(self, Qt.WindowFlags())
        self.toolbarWidget.move(10, 10)
        self.toolbarWidget.show()
        
        #clearButton.clicked.connect(self.RemoveAllItems)
        #openButton.clicked.connect(self.Open)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.inariView.resize(self.size().width(), self.size().height())
        self.toolbarWidget.resize(self.size().width()-20, 35)

    def SetSelection(self, items:typing.List[str]) -> None:
        self.inariScene.clearSelection()
        for item in self.inariScene.items():
            if isinstance(item, InariLocator):
                if item.name() in items:
                    item.setSelected(True)

    def clearScene(self):
        for item in self.inariScene.items():
            self.inariScene.removeItem(item)

    def deserializeScene(self, filepath: str):
        with open(filepath, "r") as file:
            obj = json.loads(file.read())

            for element in obj["elements"]:
                item = None
                if "type" in element:
                    if element["type"] == "InariItem":
                        item = InariItem(self, str(element["imagePath"]))
                        item.setCommandInterpreter(self.inariCommandInterpreter)
                        item.setPos(float(element["positionX"]), float(element["positionY"]))
                    elif element["type"] == "InariLocator":
                        item = InariLocator(self, str(element["imagePath"]), str(element["hoverImagePath"]))
                        item.setCommandInterpreter(self.inariCommandInterpreter)
                        item.setPos(float(element["positionX"]), float(element["positionY"]))

                if item != None:
                    self.inariScene.addItem(item)

                """
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
                    """
# endregion

# region Items
class InariItem(QtWidgets.QGraphicsItem):
    inariWidget: "InariWidget" = None
    renderer: QtSvg.QSvgRenderer = None
    commandInterpreter: InariCommandInterpreter = None 

    def __init__(self, inariWidget: "InariWidget", filepath: str) -> None:
        super().__init__()
        self.renderer = QtSvg.QSvgRenderer(filepath)

    def setCommandInterpreter(self, commandInterpreter: InariCommandInterpreter):
        self.commandInterpreter = commandInterpreter

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(QtCore.QPointF(0, 0), self.renderer.defaultSize())

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
        self.renderer.render(painter, self.boundingRect())


class InariLocator(InariItem):
    hoverRenderer: QtSvg.QSvgRenderer = None
    name: str = None
    _initialLeftClickPosition: QtCore.QPointF = None
    _initialPosition: QtCore.QPoint = None

    def __init__(self, inariWidget: "InariWidget", filepath: str, hoverFilepath: str) -> None:
        super().__init__(inariWidget, filepath)
        self.hoverRenderer = QtSvg.QSvgRenderer(hoverFilepath)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.AllButtons)
        self.setAcceptHoverEvents(True)

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
        self.renderer.render(painter, self.boundingRect())
        if self.isSelected():
            self.hoverRenderer.render(painter, self.boundingRect())
            
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)

        if (event.button() == QtCore.Qt.LeftButton):
            self.scene().registerSceneMouseMoveEventListener(self)
            self._initialLeftClickPosition = event.scenePos()
            pos = self.commandInterpreter.Host_GetPosition(self.name, worldSpace=False)
            self._initialPosition = QtCore.QPointF(pos[0], pos[1])
            
        self.update()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        if (event.button() == QtCore.Qt.LeftButton):
            self.scene().unregisterSceneMouseMoveEventListener(self)

        self.update()

    def sceneMouseMoveEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent) -> None:
        delta = (event.scenePos() - self._initialLeftClickPosition)
        delta.setY(delta.y() * -1)
        delta /= 100
        newPosition = self._initialPosition + delta
        self.commandInterpreter.Host_SetPosition(self.name, newPosition.x(), newPosition.y(), 0, worldSpace=False, relative=False)
# endregion

#region Toolbar
class InariToolbarButton(QtWidgets.QPushButton):
    _hovering: bool = False

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None, filepath: str = None, hoverFilepath: str = None) -> None:
        super().__init__(parent=parent)
        self.icon = QtGui.QIcon(filepath)
        self.hoverIcon = QtGui.QIcon(hoverFilepath)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self._hovering:
            self.hoverIcon.paint(painter, self.rect())
        else:
            self.icon.paint(painter, self.rect())
        painter.end()

    def enterEvent(self, event: QtCore.QEvent) -> None:
        super().enterEvent(event)
        self._hovering = True
        self.update()

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        super().leaveEvent(event)
        self._hovering = False
        self.update()


class InariToolbarWidget(QtWidgets.QWidget):
    _inariWidget: "InariWidget" = None

    def __init__(self, inariWidget: "InariWidget", f: QtCore.Qt.WindowFlags = None) -> None:
        super().__init__(parent=inariWidget, f=f)
        self._inariWidget = inariWidget
        self.buttonSize = QtCore.QSize(22, 22)
        self.buttonMargin = (self.size().height()-self.buttonSize.height())/2
        self.settingsButton = InariToolbarButton(self, "./assets/v2/Button_Settings.svg", "./assets/v2/Button_Settings_Hover.svg")
        self.settingsButton.resize(self.buttonSize)
        self.openButton = InariToolbarButton(self, "./assets/v2/Button_Open.svg", "./assets/v2/Button_Open_Hover.svg")
        self.openButton.resize(self.buttonSize)
        self.openButton.clicked.connect(self.openButtonPressed)
        self.saveButton = InariToolbarButton(self, "./assets/v2/Button_Save.svg", "./assets/v2/Button_Save_Hover.svg")
        self.saveButton.resize(self.buttonSize)
        self.newButton = InariToolbarButton(self, "./assets/v2/Button_New.svg", "./assets/v2/Button_New_Hover.svg")
        self.newButton.resize(self.buttonSize)
        self.newButton.clicked.connect(self.newButtonPressed)
        self.terminalButton = InariToolbarButton(self, "./assets/v2/Button_Terminal.svg", "./assets/v2/Button_Terminal_Hover.svg")
        self.terminalButton.resize(self.buttonSize)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        path = QtGui.QPainterPath()
        path.addRoundedRect(0, 0, self.size().width(), self.size().height(), 10, 10)
        painter.fillPath(path, QtGui.QColor(59, 59, 59))
        painter.setFont(QtGui.QFont('Consolas', 12))
        painter.setPen(QtGui.QColor(156, 156, 156))
        painter.drawText(QtCore.QPointF(14, 22), "Khaos Systems | Inari")
        painter.end()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.buttonMargin = (self.size().height()-self.buttonSize.height())/2
        self.settingsButton.move(self.size().width()-self.buttonSize.width()-self.buttonMargin, self.buttonMargin)
        self.openButton.move(self.size().width()-(self.buttonSize.width()*2)-(self.buttonMargin*2), self.buttonMargin)
        self.saveButton.move(self.size().width()-(self.buttonSize.width()*3)-(self.buttonMargin*3), self.buttonMargin)
        self.newButton.move(self.size().width()-(self.buttonSize.width()*4)-(self.buttonMargin*4), self.buttonMargin)
        self.terminalButton.move(self.size().width()-(self.buttonSize.width()*5)-(self.buttonMargin*5), self.buttonMargin)

    def newButtonPressed(self):
        self._inariWidget.clearScene()

    def openButtonPressed(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self)[0]
        self._inariWidget.clearScene()
        self._inariWidget.deserializeScene(path)
        self._inariWidget.inariView.frameSelected()
#endregion