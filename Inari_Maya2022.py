import weakref

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtGui, QtWidgets, QtCore 

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
            print("maya")
            print(self.command)

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
    def __init__(self, parent: QObject):
        super().__init__(parent)

        self.setStyleSheet("background-color: black")

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
                    item = InariGraphicsSvgItem("C:/Dev/Inari/" + element["imagePath"])
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

def dock_window(dialog_class):
    try:
        cmds.deleteUI(dialog_class.CONTROL_NAME)
        logger.info('removed workspace {}'.format(dialog_class.CONTROL_NAME))

    except:
        pass

    # building the workspace control with maya.cmds
    main_control = cmds.workspaceControl(dialog_class.CONTROL_NAME, ttc=["AttributeEditor", -1],iw=300, mw=True, wp='preferred', label = dialog_class.DOCK_LABEL_NAME)
    
    # now lets get a C++ pointer to it using OpenMaya
    control_widget = omui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    # conver the C++ pointer to Qt object we can use
    control_wrap = wrapInstance(int(control_widget), QtWidgets.QWidget)
    
    # control_wrap is the widget of the docking window and now we can start working with it:
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    win = dialog_class(control_wrap)
    
    # after maya is ready we should restore the window since it may not be visible
    cmds.evalDeferred(lambda *args: cmds.workspaceControl(main_control, e=True, rs=True))

    # will return the class of the dock content.
    return win.run()


class MyDockingUI(QtWidgets.QWidget):

    instances = list()
    CONTROL_NAME = 'my_workspcae_control'
    DOCK_LABEL_NAME = 'Khaos Systems | Inari'

    def __init__(self, parent=None):
        super(MyDockingUI, self).__init__(parent)

        # let's keep track of our docks so we only have one at a time.    
        MyDockingUI.delete_instances()
        self.__class__.instances.append(weakref.proxy(self))

        self.window_name = self.CONTROL_NAME
        self.ui = parent
        self.main_layout = parent.layout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)

        # here we can start coding our UI
        #self.my_label = QtWidgets.QLabel('hello world!')
        #self.main_layout.addWidget(self.my_label)   
        # 
        inariWidget = InariWidget(self)
        inariWidget.Load("C:\Dev\Inari\example.json")

        self.main_layout.setMargin(0)
        self.main_layout.addWidget(inariWidget)
        self.show()
 

    @staticmethod
    def delete_instances():
        for ins in MyDockingUI.instances:
            logger.info('Delete {}'.format(ins))
            try:
                ins.setParent(None)
                ins.deleteLater()
            except:
                # ignore the fact that the actual parent has already been deleted by Maya...
                pass

            MyDockingUI.instances.remove(ins)
            del ins

    def run(self):
        return self

# this is where we call the window
my_dock = dock_window(MyDockingUI)