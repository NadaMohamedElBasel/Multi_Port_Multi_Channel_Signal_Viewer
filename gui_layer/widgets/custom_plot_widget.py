from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton, QDialog,QDialogButtonBox,QGroupBox,QButtonGroup,
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit,
                             QScrollBar, QGridLayout, QComboBox, QFileDialog, QColorDialog, QMessageBox)
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from mediator_layer.mediator import Mediator

class PlotWidget(pg.PlotWidget):
    """Custom plot widget to display signals."""
    def __init__(self, mediator, name):
        self.mediator = mediator
        self.name = name
        self.start_point = None
        super().__init__()
    
    def mousePressEvent(self, event):
        if CustomPlotWidget.selection_mode_enabled and event.button() == Qt.LeftButton:
            self.start_point = event.pos()  # Get starting point
            if self.mediator.notify_start_rectangle(self.start_point):
                print(f"Rectangle started at: {self.start_point}")
                self.update()  # Trigger a repaint
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if CustomPlotWidget.selection_mode_enabled and self.start_point is not None:
            # Update the rectangle's size based on the current mouse position
            self.mediator.notify_update_rectangle(event.pos())
            self.update()  # Trigger a repaint
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if CustomPlotWidget.selection_mode_enabled and event.button() == Qt.LeftButton:
            selected_rectangles = self.mediator.notify_finalize_rectangle(self)
            if selected_rectangles:
                # Notify the mediator about the selection
                self.mediator.update_main_window(selected_rectangles)
            self.start_point = None  # Reset start point
            self.update()  # Trigger a repaint
        else:
            super().mouseReleaseEvent(event)

class CustomPlotWidget(QWidget):
    """Custom plot widget to display signals."""
    
    selection_mode_enabled = False  # Flag to track selection mode

    def __init__(self, mediator: Mediator, name: str):
        super().__init__()
        self.mediator = mediator
        self.name = name
        # Create a vertical layout for the widget
        self.layout = QGridLayout(self)

        # Create the plot label
        self.label = QLabel(name)
        self.label.setFont(QFont("Arial", 12, QFont.Bold))

        # Create the plot widget
        self.plot_widget = PlotWidget(mediator=mediator, name=name)
        self.plot_widget.enableAutoRange(axis='x', enable=False)
        self.plot_widget.setFixedSize(400, 300)
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLimits(xMin=0)

        # Create the scroll bars
        self.graph_vertical_scroll = QScrollBar(Qt.Vertical)
        self.graph_horizontal_scroll = QScrollBar(Qt.Horizontal)

        # Connect the scroll bars to the respective functions
        self.graph_horizontal_scroll.valueChanged.connect(self.graph_x_scroll_moved)
        self.graph_vertical_scroll.valueChanged.connect(self.graph_y_scroll_moved)

        # Add the plot and scroll bars to the grid layout
        self.layout.addWidget(self.label, 0, 1)  # Label at (0, 0)
        self.layout.addWidget(self.plot_widget, 1, 1)  # Plot at (0, 0)
        self.layout.addWidget(self.graph_horizontal_scroll, 2, 1)  # Horizontal scroll at (1, 0)
        self.layout.addWidget(self.graph_vertical_scroll, 1, 0)  # Vertical scroll at (0, 1)

        # Set the layout for the widget
        self.setLayout(self.layout)

        # Initialize previous scroll values
        self.prev_graph_x_scroll = 0
        self.prev_graph_y_scroll = 0

    def graph_x_scroll_moved(self):
        """Handle horizontal scrolling for graph1."""
        current_value = self.graph_horizontal_scroll.value()
        difference = current_value - self.prev_graph_x_scroll
        
        if difference != 0:
            self.update_graph_view(self, 'x', difference)
        
        # Update the previous value to the current value
        self.prev_graph_x_scroll = current_value

    def graph_y_scroll_moved(self):
        """Handle vertical scrolling for graph1."""
        current_value = self.graph_vertical_scroll.value()
        difference = current_value - self.prev_graph_y_scroll
        
        if difference != 0:
            self.update_graph_view(self, 'y', difference)
        
        # Update the previous value to the current value
        self.prev_graph_y_scroll = current_value

    def update_graph_view(self, graph, axis, difference):
        """Update graph's view range based on scroll movement."""
        current_range = self.plot_widget.viewRange()  # Get the current view range

        # Scaling factor to control scroll sensitivity
        scaling_factor = 0.1
        if axis == 'x':
            # Adjust X-axis range based on scroll difference (scaled down)
            new_x_min = current_range[0][0] + difference * scaling_factor
            new_x_max = current_range[0][1] + difference * scaling_factor
            self.plot_widget.setXRange(new_x_min, new_x_max, padding=0)
        elif axis == 'y':
            # Adjust Y-axis range based on scroll difference
            new_y_min = current_range[1][0] + difference
            new_y_max = current_range[1][1] + difference
            self.plot_widget.setYRange(new_y_min, new_y_max, padding=0)

    def enable_auto_range(self, enabled):
        """Enable auto range for the given axis."""
        self.plot_widget.enableAutoRange(axis='x', enable=enabled)