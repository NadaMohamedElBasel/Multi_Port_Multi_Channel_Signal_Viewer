import numpy as np
from PyQt5.QtGui import QBrush, QPen, QPainter, QImage, QFont
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton, QDialog,QDialogButtonBox,QGroupBox,QButtonGroup,
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit,
                             QScrollBar, QGridLayout, QComboBox, QFileDialog, QColorDialog, QMessageBox)
from PyQt5.QtCore import Qt
from mediator_layer.mediator import Mediator
from gui_layer.widgets.circle_graph import CircleGraph

class CustomCircularPlotWidget(QWidget):
    def __init__(self, mediator: Mediator, name: str):
        super().__init__()
        self.mediator = mediator
        self.name = name
        self.layout = QGridLayout(self)
        self.plot_widget = CircleGraph(mediator)
        self.plot_widget.setFixedSize(400, 300)
        
        # Create the plot label
        self.label = QLabel(name)
        self.label.setFont(QFont("Arial", 12, QFont.Bold))
        # Add the plot and scroll bars to the grid layout
        self.layout.addWidget(self.label, 0, 0)  # Label at (0, 0)
        self.layout.addWidget(self.plot_widget, 1, 0)  # Plot at (0, 0)

        # Set the layout for the widget
        self.setLayout(self.layout)