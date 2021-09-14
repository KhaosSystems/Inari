import sys
from PySide2.QtWidgets import QApplication, QPushButton

def func():
 print("func has been called!")

app = QApplication(sys.argv)
button = QPushButton("Call func")
button.clicked.connect(func)
button.show()

sys.exit(app.exec_())