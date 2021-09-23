import weakref

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtGui, QtWidgets, QtCore 

import typing
import Inari
import importlib

importlib.reload(Inari)

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

class InariMayaCommandInterpreter(Inari.InariCommandInterpreter):
    def Select(self, item:str):
        cmds.select(str(item), add=True)

    def Deselect(self, item: str):
        cmds.select(str(item), deselect=True)

    def DeselectAll(self):
        cmds.select(cl=True)

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

        inariWidget = Inari.InariWidget(self, InariMayaCommandInterpreter())
        inariWidget.Load("C:/Dev/Inari/example.json")

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