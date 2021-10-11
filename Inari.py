from os import terminal_size
from types import FrameType
from PySide2.QtCore import QPoint, QPointF, QRectF, Qt

from PySide2.QtWidgets import QApplication, QFileDialog, QGraphicsItem, QHBoxLayout, QPushButton, QStyleOptionViewItem, QWidget
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import typing
import json

# TODO: Alt mouse wheel always zoom out.
# TODO: Comment and refactor; make stuff look nice.
# TODO: Add remaining locators to example.json.
# TODO: Optimize.
# TODO: Anchors.
# TODO: cursors.
# TODO: Readme.
# TODO: Demo rig.

# region Core
"""
InariCommandInterpreter is the primary comunication bridge between Inari and the host software.
All software bridges needs to provide an InariCommandInterpreter when creating the InariWidget.
The host software is responsible for re-implementing/overriding all functions prefixed with "Host_".
"""
class InariCommandInterpreter():
    # Sets the selection, meaning replacing the existing selection.
    def Host_SetSelection(self, items:typing.List[str]) -> None:
        print(f'Host_SetSelection(items: {items})')

    # Returns an array of strings containing the names of all currently selected objects.
    def Host_GetSelection(self) -> typing.List[str]:
        print(f'Host_GetSelection()')
        return []

    # Sets the position of first item with the specified name.
    def Host_SetPosition(self, item:str, x:float, y:float, z:float, worldSpace:bool=False, relative:bool=True) -> None:
        print(f'Host_SetSelection(item: {item}, x: {x}, y: {y}, z: {z}, worldSpace: {worldSpace}, relative: {relative})')

    # Gets the position of first item with the specified name.
    def Host_GetPosition(self, item:str, worldSpace:bool=False, relative:bool=True) -> typing.List[float]:
        print(f'Host_GetSelection(item: {item}, worldSpace: {worldSpace}, relative: {relative})')
        return [0, 0, 0]


"""
InariScene can be thought as the scene data, providing the necessary functions to alter and manage the items.
For a deeper understand of how this works i suggest reading up on the "Qt Graphics View Framework".
"""
class InariScene(QtWidgets.QGraphicsScene):
    # If false, items won't recieve events and vise-versa.
    shouldPropagateEventsToItems: bool = True
    # The InariCommandInterpreter used for interacting with the host application.
    commandInterpreter:InariCommandInterpreter = None
    # All InariItem in this list will recieve scene/global mouse events.
    _sceneMouseMoveEventListeners:typing.List["InariItem"] = []

    # Constructor
    def __init__(self, parentItem: QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)
        # Register signals
        QtCore.QObject.connect(self, QtCore.SIGNAL("selectionChanged()"), self.selectionChangedSignal)

    # Sets the InariCommandInterpreter used for interacting with the host application.
    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter) -> None:
        self.commandInterpreter = commandInterpreter

    # If false, items won't recieve events and vise-versa.
    def setShouldPropagateEventsToItems(self, shouldPropagateEventsToItems: bool) -> None:
        self.shouldPropagateEventsToItems = shouldPropagateEventsToItems

    # Returns bounding box of the selected items. 
    def selectionItemsBoundingRect(self) -> QtCore.QRectF:
        # Does not take untransformable items into account.
        boundingRect = QtCore.QRectF()
        for item in self.selectedItems():
            boundingRect |= item.sceneBoundingRect()
        return boundingRect

    # Registers an InariItem for receiving scene space/global mouse events.
    def registerSceneMouseMoveEventListener(self, item: "InariItem") -> None:
        self._sceneMouseMoveEventListeners.append(item)

    # Unregisters an InariItem for receiving scene space/global mouse events.
    def unregisterSceneMouseMoveEventListener(self, item: "InariItem") -> None:
        self._sceneMouseMoveEventListeners.remove(item)

    # Overwritten mouse move event handler, please refer to the QT documentation.
    def mouseMoveEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        # Notify all InariItems registered for scene mouse move events.
        for listener in self._sceneMouseMoveEventListeners:
            listener.sceneMouseMoveEvent(event)
    
    # Overwritten master event handler/dispatcher, please refer to the QT documentation.
    def event(self, event: QtCore.QEvent) -> bool:
        # Handle event blocking.
        if self.shouldPropagateEventsToItems:
            return super().event(event)
        else:
            # Mark the event as handled.
            return True

    # Overwritten addItem function, please refer to the QT documentation.
    def addItem(self, item: QtWidgets.QGraphicsItem) -> None:
        super().addItem(item)
        # Recalculate the scene rect size and add a big margin, this allows freer scene movement
        # since camera transformations won't be blocked due to the small default scene size.
        self.setSceneRect(self.itemsBoundingRect().marginsAdded(QtCore.QMarginsF(1024*128, 1024*128, 1024*128, 1024*128)))

    # Connected to the selectionChanged() signal, please refer to the QT documentation.
    def selectionChangedSignal(self) -> None:
        # Tell the host application to update it's selection to match Inari.
        items = [item.itemName for item in self.selectedItems() if isinstance(item, InariLocator)]
        self.commandInterpreter.Host_SetSelection(items)


"""
InariView can be thought as the viewport, there can be mutiple InariViews bound to the same InariScene.
For a deeper understand of how this works i suggest reading up on the "Qt Graphics View Framework".
"""
class InariView(QtWidgets.QGraphicsView):
    # The InariCommandInterpreter used for interacting with the host application.
    commandInterpreter: InariCommandInterpreter = None
    # Internal variables used for camera transformation calculations.
    _lastMouseMovePosition: QtCore.QPoint = None
    _lastRightMousePressPosition:QtCore.QPoint = None
    _lastRightMousePressVerticalScalingFactor:float = None
    _lastRightMousePressHorizontalScalingFactor:float = None

    # Constructor
    def __init__(self, scene: QtWidgets.QGraphicsScene, parent: QtWidgets.QWidget = None):
        super().__init__(scene, parent)
        # Configuration
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setGeometry(0, 0, 300, 300)
        self.setBackgroundBrush(QtGui.QColor(26, 26, 26))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)

    # Sets the InariCommandInterpreter used for interacting with the host application.
    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter):
        self.commandInterpreter = commandInterpreter

    # Frames the selected items within the view bounds, or all of them if no items are selected.
    def frameSelected(self):
        # Find the base selection bound.
        if len(self.scene().selectedItems()) > 0:
            selectionBounds = self.scene().selectionItemsBoundingRect()
        else:
            selectionBounds = self.scene().itemsBoundingRect()
        # Add a margin to avoid creating tangents with the window border.
        selectionBounds = selectionBounds.marginsAdded(QtCore.QMarginsF(64, 64+50, 64, 64))
        self.fitInView(selectionBounds, QtCore.Qt.KeepAspectRatio)

    # Overwritten key press event handler, please refer to the QT documentation.
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyPressEvent(event)

        # Frame selected.
        if event.key() == QtCore.Qt.Key_F:
            self.frameSelected()

        # Camera panning.
        if bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            # Disable box selection and don't propagate events to items until released.
            self.scene().setShouldPropagateEventsToItems(False)
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    # Overwritten key release event handler, please refer to the QT documentation.
    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyReleaseEvent(event)

        # Camera panning.
        if not bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            # Re-enable Re-enable disabled box selection and enable item event propagate again.
            self.scene().setShouldPropagateEventsToItems(True)
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)

    # Overwritten mouse pressed event handler, please refer to the QT documentation.
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(event)

        # Capture necessary data used for camera transformation.
        if event.button() == QtCore.Qt.RightButton:
            self._lastRightMousePressPosition = event.pos()
            # m11() returns the horizontal scaling factor of the transform matrix.
            self._lastRightMousePressHorizontalScalingFactor = self.matrix().m11()
            # m11() returns the vertical scaling factor of the transform matrix.
            self._initialRightMousePressVerticalScalingFactor = self.matrix().m22()

        # Set cursor corresponding to the active transformation state.
        if bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            if bool((event.buttons() & QtCore.Qt.MiddleButton) or (event.buttons() & QtCore.Qt.LeftButton)):
                # Panning.
                self.window().setCursor(QtCore.Qt.SizeAllCursor)
            elif bool(event.buttons() & QtCore.Qt.RightButton):
                # Zooming.
                self.window().setCursor(QtCore.Qt.SizeVerCursor)

    # Overwritten mouse release event handler, please refer to the QT documentation.
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        # Set default cursor; the cursor might have been changed in the when the mouse was pressed.
        self.window().setCursor(QtCore.Qt.ArrowCursor)

    # Overwritten mouse move event handler, please refer to the QT documentation.
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        # If these positions are not set/set to null vector, the later code will cause wired behaviour.
        if self._lastMouseMovePosition == None:
            self._lastMouseMovePosition = event.pos()
        if self._lastRightMousePressPosition == None:
            self._lastRightMousePressPosition = event.pos()

        # Camera transformation logic.
        if bool(QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.KeyboardModifier.AltModifier):
            if bool((event.buttons() & QtCore.Qt.MiddleButton) or (event.buttons() & QtCore.Qt.LeftButton)):
                # Camera panning.
                verticalScrollBar = self.verticalScrollBar()
                horizontalScrollBar = self.horizontalScrollBar()
                delta = event.pos() - self._lastMouseMovePosition
                verticalScrollBar.setValue(verticalScrollBar.value() - delta.y())
                horizontalScrollBar.setValue(horizontalScrollBar.value() - delta.x())
            elif bool(event.buttons() & QtCore.Qt.RightButton):
                """ 
                Camera zooming; this is some freaking messy math, don't judge; it works pretty well! xD
                There is most likely a cleaner way of doing this but i honestly can't bother finding it.
                If this is triggering to you, feel free to hit me with a pull request.
                """
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
                finalHorizontalScalingFactor = min(max(self._lastRightMousePressHorizontalScalingFactor * globalScaleFactor, 0.2), 2)
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
       
        # Capture necessary data used for camera transformation. 
        self._lastMouseMovePosition = event.pos()

    # Overwritten wheel event handler, please refer to the QT documentation.
    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        # Accepting the event stops it from propagating, canceling the default scroll behaviour.
        event.accept()

        # Mouse wheel zooming
        zoomFactor = 1.05
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        if event.angleDelta().y() > 0:
            self.scale(zoomFactor, zoomFactor)
        else:
            self.scale(1 / zoomFactor, 1 / zoomFactor)

"""
InariWidget is the master widget, responsible for creating and managing the InariScene and InariView from a high level.
"""
class InariWidget(QtWidgets.QWidget):
    # The InariCommandInterpreter used for interacting with the host application.
    inariCommandInterpreter:InariCommandInterpreter = InariCommandInterpreter()
    # Path to the currently opened scene file, used for stuff like reloading and saveing scenes.
    currentScenePath: str = None

    # Constructor.
    def __init__(self, parent: QtCore.QObject, commandInterpreter:InariCommandInterpreter):
        super().__init__(parent)
        
        # Configure the widget.
        self.inariCommandInterpreter = commandInterpreter

        # Create and configure the scene.
        self.inariScene = InariScene(self)
        self.inariScene.setCommandInterpreter(self.inariCommandInterpreter)

        # Create and configure the view.
        self.inariView = InariView(self.inariScene, self)
        self.inariView.move(0, 0)
        self.inariView.show()

        # Create and configure the toolbar.
        self.toolbarWidget = InariToolbarWidget(self, Qt.WindowFlags())
        self.toolbarWidget.move(10, 10)
        self.toolbarWidget.show()

    # Sets the active selection from a list of item names.
    # TODO: This should most likely be done with command interpreter.
    def setSelection(self, items:typing.List[str]) -> None:
        # Clear active selection.
        self.inariScene.clearSelection()

        # Set new selection.
        for item in self.inariScene.items():
            if isinstance(item, InariLocator):
                if item.itemName() in items:
                    item.setSelected(True)

    # Removes all scene items and resets the scene path.
    def newScene(self):
        for item in self.inariScene.items():
            self.inariScene.removeItem(item)
        self.currentScenePath = None

    # Opens a scene from path, returns true action was successful.
    def openScene(self, path: str) -> bool:
        # Create new scene and deserialize scene file from the supplied path.
        self.newScene()
        success: bool = self.deserializeSceneFromFile(path)
        if (not success):
            return False

        # Set new current scene path.
        self.currentScenePath = path

        # If this is reached, everything went as planned!
        return True

    # Deserialize scene file from path, returns true action was successful.
    def deserializeSceneFromFile(self, filepath: str) -> bool:
        # Validate filepath
        if filepath == None:
            return False

        if not type(filepath) == str:
            print(f'The "filepath" argument must be of type string. Received type: {type(filepath)}.')
            return False

        if not filepath.endswith('.json'):
            print("Unknown file extension.")
            return False

        # Deserialize items
        try:
            with open(filepath, "r") as file:
                projectObject = json.loads(file.read())
                if "items" in projectObject:
                    # Recursively deserialize items.
                    self.deserializeJsonElementsList(None, projectObject["items"])
        except IOError:
            print(f'Failed to read file from path: {filepath}')
            return False

        # If this is reached, everything went as planned!
        return True

    # Recursively deserialize items from a json object.
    def deserializeJsonElementsList(self, parent:QtWidgets.QGraphicsItem, jsonItems):
        for jsonItem in jsonItems:
                item = None

                # Deserialize type specific item properties.
                if "type" in jsonItem:
                    if jsonItem["type"] == "InariItem":
                        if "imagePath" in jsonItem:
                            item = InariItem(self, str(jsonItem["imagePath"]))
                    elif jsonItem["type"] == "InariLocator":
                        item = InariLocator(self, str(jsonItem["imagePath"]), str(jsonItem["hoverImagePath"]))
                        item.setItemName(str(jsonItem["itemName"]))
                    else:
                        print(f'Unknown item type: {jsonItem["type"]}')
                        continue
                else:
                    print(f'All items need a "type" field')
                    continue 
                    
                # Deserialize generic item properties.
                if jsonItem != None:
                    # Set command interpreter reference.
                    item.setCommandInterpreter(self.inariCommandInterpreter)

                    # Set item position.
                    if "positionX" in jsonItem:
                        item.setX(float(jsonItem["positionX"]))
                    if "positionY" in jsonItem:
                        item.setY(float(jsonItem["positionY"]))

                    # Set item scale.
                    if "scaleX" in jsonItem:
                        if float(jsonItem["scaleX"]) < 0:
                            item.setX(item.x() + (item.boundingRect().width() * abs(float(jsonItem["scaleX"]))))
                        item.setTransform(item.transform().scale(float(jsonItem["scaleX"]), 1))
                    if "scaleY" in jsonItem:
                        if float(jsonItem["scaleY"]) < 0:
                            item.setY(item.y() + (item.boundingRect().height() * abs(float(jsonItem["scaleY"]))))
                        item.setTransform(item.transform().scale(1, float(jsonItem["scaleY"])))

                    # Add item to scene.
                    if parent != None:
                        # setParentItem will add the item to the scene automatically.
                        item.setParentItem(parent)
                    else:
                        self.inariScene.addItem(item)

                    # Deserialize sub-items.
                    if "items" in jsonItem:
                        self.deserializeJsonElementsList(item, jsonItem["items"])

    # Overwritten key press event handler, please refer to the QT documentation.
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyPressEvent(event)

        # F5 to reload the scene.
        if (event.key() == QtCore.Qt.Key_F5):
            self.clearScene()
            self.deserializeSceneFromFile(self.currentScenePath)

    # Overwritten resize event handler, please refer to the QT documentation.
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)

        # Propagate resize to view and toolbar. this should ideally be done with QT layouts.
        self.inariView.resize(self.size().width(), self.size().height())
        self.toolbarWidget.resize(self.size().width()-20, 35)
# endregion

#region Toolbar
"""
InariToolbarPushButton represents a button on the InariToolbarWidget.
"""
class InariToolbarPushButton(QtWidgets.QPushButton):
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

"""
InariToolbarWidget is simply the toolbar widget.
"""
class InariToolbarWidget(QtWidgets.QWidget):
    # A reference to the owning InariWidget.
    inariWidget: "InariWidget" = None

    # Constructor.
    def __init__(self, inariWidget: "InariWidget", f: QtCore.Qt.WindowFlags = None) -> None:
        super().__init__(parent=inariWidget, f=f)
        self.inariWidget = inariWidget
        
        # Calculate general button related variables.
        self.buttonSize = QtCore.QSize(22, 22)
        self.buttonMargin = (self.size().height()-self.buttonSize.height())/2
       
        # Settings Button
        self.settingsButton = InariToolbarPushButton(self, "./assets/v2/Button_Settings.svg", "./assets/v2/Button_Settings_Hover.svg")
        self.settingsButton.resize(self.buttonSize)

        # Open Button
        self.openButton = InariToolbarPushButton(self, "./assets/v2/Button_Open.svg", "./assets/v2/Button_Open_Hover.svg")
        self.openButton.resize(self.buttonSize)
        self.openButton.clicked.connect(self.openButtonPressed)

        # Save Button
        self.saveButton = InariToolbarPushButton(self, "./assets/v2/Button_Save.svg", "./assets/v2/Button_Save_Hover.svg")
        self.saveButton.resize(self.buttonSize)
        
        # New Button
        self.newButton = InariToolbarPushButton(self, "./assets/v2/Button_New.svg", "./assets/v2/Button_New_Hover.svg")
        self.newButton.resize(self.buttonSize)
        self.newButton.clicked.connect(self.newButtonPressed)

        # Terminal Button
        self.terminalButton = InariToolbarPushButton(self, "./assets/v2/Button_Terminal.svg", "./assets/v2/Button_Terminal_Hover.svg")
        self.terminalButton.resize(self.buttonSize)

    # Method connected to the new buttons clicked signal, please refer to the QT documentation.
    def newButtonPressed(self):
        self.inariWidget.newScene()

    # Method connected to the open button clicked signal, please refer to the QT documentation.
    def openButtonPressed(self):
        # Open a file dialog to let the user select the scene to be opened.
        path = QtWidgets.QFileDialog.getOpenFileName(self)[0]

        # Open the scene from path.
        self.inariWidget.openScene(path)

        # Frame the content of the newly opened scene.
        self.inariWidget.inariView.frameSelected()

    # Overwritten paint event handler, please refer to the QT documentation.
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)

        # Create and configure painter.
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw the widget background.
        path = QtGui.QPainterPath()
        path.addRoundedRect(0, 0, self.size().width(), self.size().height(), 10, 10)
        painter.fillPath(path, QtGui.QColor(59, 59, 59))
        
        # Draw the title text.
        painter.setFont(QtGui.QFont('Consolas', 12))
        painter.setPen(QtGui.QColor(156, 156, 156))
        painter.drawText(QtCore.QPointF(14, 22), "Khaos Systems | Inari")
        
        # Stop painting.
        painter.end()

    # Overwritten resize event handler, please refer to the QT documentation.
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)

        # Set the button positions, this would ideally  be done using QT layouts.
        self.buttonMargin = (self.size().height()-self.buttonSize.height())/2
        self.settingsButton.move(self.size().width()-self.buttonSize.width()-self.buttonMargin, self.buttonMargin)
        self.openButton.move(self.size().width()-(self.buttonSize.width()*2)-(self.buttonMargin*2), self.buttonMargin)
        self.saveButton.move(self.size().width()-(self.buttonSize.width()*3)-(self.buttonMargin*3), self.buttonMargin)
        self.newButton.move(self.size().width()-(self.buttonSize.width()*4)-(self.buttonMargin*4), self.buttonMargin)
        self.terminalButton.move(self.size().width()-(self.buttonSize.width()*5)-(self.buttonMargin*5), self.buttonMargin)
#endregion

# region Items
"""
InariItem is the master class for all scene items.
If you want to create an item with custom logic, it needs to inherit from InariItem.
"""
class InariItem(QtWidgets.QGraphicsItem):
    # The owning InariWidget.
    inariWidget: "InariWidget" = None
    # The QSvgRenderer used to render the item. 
    renderer: QtSvg.QSvgRenderer = None
    # The InariCommandInterpreter used for interacting with the host application.
    commandInterpreter: InariCommandInterpreter = None 

    # Constructor.
    def __init__(self, inariWidget: "InariWidget", filepath: str) -> None:
        super().__init__()

        # Configure the item.
        self.inariWidget = InariWidget
        self.renderer = QtSvg.QSvgRenderer(filepath)

    # Sets the InariCommandInterpreter used for interacting with the host application.
    def setCommandInterpreter(self, commandInterpreter: InariCommandInterpreter):
        self.commandInterpreter = commandInterpreter

    # Overwritten boundingRect() method, please refer to the QT documentation.
    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(QtCore.QPointF(0, 0), self.renderer.defaultSize())

    # Overwritten paint method, please refer to the QT documentation.
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
        self.renderer.render(painter, self.boundingRect())

"""
InariLocator is used to control a control object or locator in the host applications scene.
"""
class InariLocator(InariItem):
    # The QSvgRenderer used to render the item when active/selected.
    activeRenderer: QtSvg.QSvgRenderer = None
    # The name of the control object in the host applications scene.
    itemName: str = None
    # Internal variables used for transformation calculations.
    _initialLeftClickPosition: QtCore.QPointF = None
    _initialPosition: QtCore.QPoint = None

    # Constructor.
    def __init__(self, inariWidget: "InariWidget", filepath: str, hoverFilepath: str) -> None:
        super().__init__(inariWidget, filepath)
                
        # Configure the item.
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.AllButtons)
        self.setAcceptHoverEvents(True)

        # Create the active renderer.
        self.activeRenderer = QtSvg.QSvgRenderer(hoverFilepath)

    # Sets the item name.
    def setItemName(self, itemName: str) -> None:
        self.itemName = itemName

    # Overwritten paint method, please refer to the QT documentation.
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: typing.Optional[QtWidgets.QWidget] = ...) -> None:
        # If selected, render using active renderer, else render using normal renderer.
        if self.isSelected():
            self.activeRenderer.render(painter, self.boundingRect())
        else:
            self.renderer.render(painter, self.boundingRect())

    # Overwritten mouse press event handler, please refer to the QT documentation.
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)

        # Start drag translation.
        if (event.button() == QtCore.Qt.LeftButton):
            # The build in Qt mouse event only gets called when the item is hovered.
            self.scene().registerSceneMouseMoveEventListener(self)

             # Capture necessary data for drag translation.
            self._initialLeftClickPosition = event.scenePos()
            pos = self.commandInterpreter.Host_GetPosition(self.itemName, worldSpace=False)
            self._initialPosition = QtCore.QPointF(pos[0], pos[1])
            
        # Calling updates forces a redraw if the item.
        self.update()

    # Overwritten mouse release event handler, please refer to the QT documentation.
    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        # End drag translation.
        if (event.button() == QtCore.Qt.LeftButton):
            self.scene().unregisterSceneMouseMoveEventListener(self)

        # Calling updates forces a redraw if the item.
        self.update()

    # sceneMouseMoveEvent, called by InariScene when registerd to scene mouse move events.
    def sceneMouseMoveEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent) -> None:
        # Drag translation.
        delta = (event.scenePos() - self._initialLeftClickPosition)
        delta.setY(delta.y() * -1)
        delta /= 100
        newPosition = self._initialPosition + delta
        
        # Set the newly calculated object position.
        self.commandInterpreter.Host_SetPosition(self.itemName, newPosition.x(), newPosition.y(), 0, worldSpace=False, relative=False)
# endregion