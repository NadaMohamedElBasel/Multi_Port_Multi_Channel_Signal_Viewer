import sys
from PyQt5.QtWidgets import QApplication
from gui_layer.main_window import MainWindow
from mediator_layer.mediator import Mediator
from logic_layer.logic_handler import LogicHandler

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())