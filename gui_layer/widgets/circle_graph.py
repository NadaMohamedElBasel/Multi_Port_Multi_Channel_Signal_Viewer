import numpy as np
from PyQt5.QtGui import QBrush, QPen, QPainter, QImage
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton, QDialog,QDialogButtonBox,QGroupBox,QButtonGroup,
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit,
                             QScrollBar, QGridLayout, QComboBox, QFileDialog, QColorDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QRect
from mediator_layer.mediator import Mediator

class CircleGraph(QWidget):
    def __init__(self, mediator, name):
        super().__init__()
        self.mediator = mediator
        self.name = name
        self.plot_widget = self
        self.setMinimumSize(400, 400)
        self.data = None  # Placeholder for signal data
        self.angle = 0  # Angle that represents time

    def paintEvent(self, event):
        painter = QPainter(self)

        # Define the center and radius for the circle
        center_x, center_y = self.width() // 2, self.height() // 2
        radius = min(self.width(), self.height()) // 2 - 20

        # Draw the outer circle
        painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        painter.drawEllipse(center_x - radius, center_y - radius, 2 * radius, 2 * radius)

        # Draw a circle border
        pen = QPen(Qt.black, 4, Qt.SolidLine)
        painter.setPen(pen)
        painter.drawEllipse(center_x - radius, center_y - radius, 2 * radius, 2 * radius)

        # Draw concentric circles and radial lines
        painter.setPen(QPen(Qt.gray, 1, Qt.DotLine))  # Set pen for concentric circles
        decrementRadius = radius // 7
        for circularGrids in range(7):
            gridRadius = radius - decrementRadius * circularGrids
            painter.drawEllipse(center_x - gridRadius, center_y - gridRadius, 2 * gridRadius, 2 * gridRadius)

        # Draw radial lines
        num_radial_lines = 12  # Number of radial lines
        for angle in np.linspace(0, 360, num_radial_lines, endpoint=False):
            x = center_x + radius * np.cos(np.radians(angle))
            y = center_y + radius * np.sin(np.radians(angle))
            painter.drawLine(center_x, center_y, int(x), int(y))  # Line from center to edge

        # Plot points with respect to time
        if self.data is not None:
            angles = np.linspace(0, 2 * np.pi, len(self.data))  # Spread points around the circle
            previous_point = None  # To connect lines between points

            # Find the index of the current point based on the angle
            current_index = np.argmax(angles >= self.angle) - 1
            if current_index < 0:
                current_index = 0

            for idx, value in enumerate(self.data):
                if angles[idx] <= self.angle:  # Plot with time
                    point_radius = value  # Scale for plotting
                    x = point_radius * np.cos(angles[idx])
                    y = point_radius * np.sin(angles[idx])

                    # Draw red points
                    painter.setBrush(QBrush(Qt.red))
                    painter.drawEllipse(int(center_x + x) - 2, int(center_y + y) - 2, 4, 4)

                    # Draw lines connecting points
                    if previous_point is not None:
                        painter.setPen(QPen(Qt.red, 0.9))  # Set line color and width
                        painter.drawLine(previous_point[0], previous_point[1], int(center_x + x), int(center_y + y))

                    previous_point = (int(center_x + x), int(center_y + y))  # Update the previous point

                    # Draw amplitude label only for the current detected point
                    if idx == current_index:  # Check if this is the current detected index
                        painter.setPen(QPen(Qt.white, 0.9))
                        painter.drawText(int(center_x + x) + 5, int(center_y + y) - 5, f"{value:.1f}")
    def update_circular_graph(self):
        self.angle += np.pi / 90  # Update the angle at a fixed rate
        if self.angle >= 2 * np.pi:
            self.angle = 0  # Reset the angle after completing the circle
        self.update()  # Trigger a repaint
   