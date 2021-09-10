from os import terminal_size
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QStyleOptionGraphicsItem, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsItem, QFrame, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent, QGraphicsSceneMouseEvent, QGraphicsColorizeEffect, QGraphicsEffect, QGraphicsBlurEffect
from PySide2.QtGui import QIcon, QPainter, QTransform, QBrush, QColor, QWheelEvent, QCursor, QImage, QPixmap, QBitmap
from PySide2.QtCore import Qt, QObject, QPoint, QPointF
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg
import json
import sys

# override decorator for clarity
# TODO: Do propper implementation with error checking and and to KhaosSystemsUtils.py
def override(f):
    return f

class InariGraphicsSvgItem(QGraphicsSvgItem):
    # TODO: Remove posX and posY from constructor, this is TMP api stuff
    def __init__(self, fileName: str):
        super().__init__(fileName)

        self.commandInterpreter = InariCommandInterpreter()
        self.command = None
        self.hovering = False
        self.clicking = False
        self.alphaMask = QImage()
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setAcceptHoverEvents(False)

    def setOnClickCommand(self, command: str) -> None:
        self.command = command
        self.setAcceptedMouseButtons(Qt.MouseButton.AllButtons)
        self.setAcceptHoverEvents(True)

    def setCommandInterpreter(self, commandInterpreter:InariCommandInterpreter) -> None:
        self.commandInterpreter = commandInterpreter

    @override
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget = None) -> None:
        # TODO: There should be a way of rendering the QPixmap without "pixmapPainter", just using "painter" instead...

        # Render a QPixmap from the SVG.
        pixmap = QPixmap(painter.device().width(), painter.device().height())
        pixmap.fill(Qt.transparent)
        pixmapPainter = QtGui.QPainter()
        pixmapPainter.begin(pixmap)
        pixmapPainter.setRenderHint(QtGui.QPainter.Antialiasing)
        pixmapPainter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        self.renderer().render(pixmapPainter)
        pixmapPainter.end()

        # Render self.alphaMask; used by self.verifyHover() and mask for the hover effect.
        # One possible optimization to the hover verification process would be to downsize this mask to a lower resolution.
        self.alphaMask = pixmap.toImage().createAlphaMask(
            QtCore.Qt.ImageConversionFlag.AutoColor)

        # Configure and render pixmap to screen.
        # TODO: Implement color event with QImage::applyColorTransform
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        image = pixmap.toImage()
        painter.drawImage(self.boundingRect(), image)

        # painter.drawImage(self.boundingRect(), self.alphaMask)
        if self.hovering == True:
            # TODO: Make the clipping mask scale with the widget
            """clippingMask = QtGui.QRegion(QtGui.QBitmap().fromImage(self.alphaMask))
            painter.setClipRegion(clippingMask)"""
            if self.clicking == True:
                painter.fillRect(self.boundingRect(),
                                 QtGui.QColor(255, 255, 255, 150))
            else:
                painter.fillRect(self.boundingRect(),
                                 QtGui.QColor(255, 255, 255, 100))

        # DEBUG
        # painter.drawImage(self.boundingRect(), self.alphaMask)
        # painter.drawRect(painter.viewport())

    # region Custom verified mouse events

    def verifiedHoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverMoveEvent(event)

    def verifiedHoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverEnterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def verifiedHoverLeaveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def verifiedMousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if self.command:
            self.commandInterpreter.Run(self.command)

        self.update()

    def verifiedMouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        self.update()
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
            self.clicking = True
            self.verifiedMousePressEvent(event)
        else:
            super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self.verifyHover(event.pos().x(), event.pos().y()):
            self.clicking = False
            self.verifiedMouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)
    # endregion

    # region Helpers
    def verifyHover(self, cursorX: int, cursorY: int) -> bool:
        # the default cursor hovering logic does not include transparency, this function is used to verify the correct hovering state.
        return (self.alphaMask.pixelColor(cursorX, cursorY).red() < 1)
    # endregion

class InariQGraphicsScene(QGraphicsScene):
    def __init__(self, parentItem:QtWidgets.QGraphicsItem) -> None:
        super().__init__(parentItem)

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

    @override
    def wheelEvent(self, event: QWheelEvent):
        if event.delta() > 0:
            self.scale(1.05, 1.05)
        else:
            self.scale(0.95, 0.95)

class InariWidget(QWidget):
    def __init__(self, parent: QObject, commandInterpreter:InariCommandInterpreter):
        super().__init__(parent)

        self.setStyleSheet("background-color: black")
        self.commandInterpreter = commandInterpreter

        self.scene = InariQGraphicsScene(self)
        self.view = InariQGraphicsView(self.scene, self)
        self.view.show()

        layout = QHBoxLayout()
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

                item.setCommandInterpreter(self.commandInterpreter)

                self.scene.addItem(item)

            # calculate scene size and set the starting position
            # for some reason the y axis goes from - to +; thanks QT Group that totally didn't cost me like 20 minutes of confusion?..
            sceneSizePadding = 512
            itemsBoundingRect = self.scene.itemsBoundingRect()
            itemsBoundingRect.setTop(itemsBoundingRect.top() - sceneSizePadding)
            itemsBoundingRect.setBottom(itemsBoundingRect.bottom() + sceneSizePadding)
            itemsBoundingRect.setLeft(itemsBoundingRect.left() - sceneSizePadding)
            itemsBoundingRect.setRight(itemsBoundingRect.right() + sceneSizePadding)
            self.scene.setSceneRect(itemsBoundingRect)
            self.scene.addRect(itemsBoundingRect)
            
            # TODO: set the starting position, unhiding and monitoring the scrollbars might be a good starting point
            self.view.horizontalScrollBar().setRange(0, 1)
            self.view.horizontalScrollBar().setValue(0.5)

class InariCommandInterpreter():
    def __init__(self):
        
