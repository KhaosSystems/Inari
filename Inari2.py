from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import typing
import sys
import array

class InariWidget(QtWidgets.QWidget):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget]) -> None:
        super().__init__(parent)

        self.scene = InariScene(self)
        self.scene.addItem(InariSelectableItem())
        item = InariSelectableItem()
        item.setX(100)
        self.scene.addItem(item)
        self.view = InariSceneView(self.scene, self)
        self.view.show()

        layout = QtWidgets.QHBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.view)
        self.setLayout(layout)

class InariScene(QtWidgets.QGraphicsScene):
    _selectedItems:typing.List['InariSelectableItem'] = []

    def __init__(self, parentItem:QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)

    # overridden from QGraphicsScene
    def addItem(self, item: QtWidgets.QGraphicsItem) -> None:
        item.setInariScene(self)
        return super().addItem(item)

    def addItemToSelectedItems(self, item:'InariSelectableItem'):
        self._selectedItems.append(item)

    def selectedItems(self) -> typing.List['InariSelectableItem']:
        return self._selectedItems

    def clearSelectedItems(self) -> None:
        tmp = self._selectedItems.copy()
        self._selectedItems.clear()

        # this don't work
        for selectedItem in tmp:
            selectedItem.update()
        
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_Escape:
            self.clearSelectedItems()

class InariSceneView(QtWidgets.QGraphicsView):
    def __init__(self, scene: InariScene, parent: QtWidgets.QWidget = None):
        super().__init__(scene, parent)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QColor(45, 45, 45))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

class InariSceneItem(QtWidgets.QGraphicsItem):
    _useComplexHoverCollision:bool = False
    _hovering:bool = False
    _clicking:bool = False
    _inariScene:InariScene = None
    
    def __init__(self, parent: typing.Optional[QtWidgets.QGraphicsItem]=None) -> None:
        super().__init__(parent)

    def hovering(self) -> bool:
        return self._hovering

    def clicking(self) -> bool:
        return self._clicking

    def setInariScene(self, inariScene:InariScene) -> None:
        if inariScene == None:
            raise ValueError
        self._inariScene = inariScene

    def inariScene(self) -> InariScene:
        return self._inariScene

    # overridden from QGraphicsItem
    def boundingRect(self) -> QtCore.QRectF:
        raise NotImplementedError

    # region Methods related to (verified) mouse events; you can override these :)
    def setAcceptMouseEvents(self, enabled:bool) -> bool:
        if enabled:
            self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.AllButtons)
            self.setAcceptHoverEvents(True)
        else:
            self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
            self.setAcceptHoverEvents(False)

    def verifyQtHoverEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> bool:
        if self._useComplexHoverCollision:
            raise NotImplementedError
        else:
            return True

    def verifiedHoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        pass

    def verifiedHoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        pass

    def verifiedHoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        pass

    def verifiedMousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        pass

    def verifiedMouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        pass
    # endregion

    # region We'll fire you if you override these methods.
    # Currently the mouse move event wont get fired if a mouse button in down, this is a QT thing that I might fix in the future.
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
            super().mouseReleaseEvent(event)
    # endregion

class InariGraphicsSvgItem(InariSceneItem):
    _graphicsFilepath:str = None
    _svgRenderer:QtSvg.QSvgRenderer = QtSvg.QSvgRenderer()
    _highlighted:bool = False
    _highlightStrength:float = 0.5 # 0-1

    def __init__(self, parent: typing.Optional[InariSceneItem]=None, filepath:typing.Optional[str]=None) -> None:
        super().__init__(parent)

        self.setAcceptMouseEvents(False)
        
        if filepath != None:
            self.setGraphicsFilepath(filepath)

    def setGraphicsFilepath(self, filepath:str):
        self._svgRenderer.load(filepath)

    def setHighlight(self, enabled:bool, highlightStrength:typing.Optional[float]=None, update:typing.Optional[bool]=False) -> None:
        self._highlighted = enabled

        if highlightStrength:
            self._highlightStrength = highlightStrength

        if update:
            self.update()

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(QtCore.QPointF(0.0, 0.0), self._svgRenderer.defaultSize())

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget = None) -> None:
        self._svgRenderer.render(painter, self.boundingRect())
        print("paint")
        if self._highlighted:
            painter.fillRect(self.boundingRect(), QtGui.QColor(255, 255, 255, int(255*self._highlightStrength)))

class InariSelectableItem(InariGraphicsSvgItem):
    _selected = False
    
    def __init__(self, parent: typing.Optional[InariSceneItem]=None) -> None:
        super().__init__(parent)

        self.setAcceptMouseEvents(True)
        self.setGraphicsFilepath("./assets/eyebrow.svg")

    def isSelected(self) -> bool:
        return (self in self.inariScene().selectedItems())

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget) -> None:
        if self.clicking():
            self.setHighlight(True, 0.5, False)
        elif self.isSelected() or self.hovering():
            self.setHighlight(True, 0.3, False)
        else:
            self.setHighlight(enabled=False, update=False)

        super().paint(painter, option, widget=widget)

    # Overridden from InariSceneItem
    def verifiedHoverEnterEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self.update()

    # Overridden from InariSceneItem
    def verifiedHoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self.update()

    # Overridden from InariSceneItem
    def verifiedMousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        self.update()

    # Overridden from InariSceneItem
    def verifiedMouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        self.update()

# TMP
class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Khaos System | Inari")
        self.setGeometry(300, 50, 766, 980)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        inariWidget = InariWidget(self)
        #inariWidget.Load("./example.json")

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
