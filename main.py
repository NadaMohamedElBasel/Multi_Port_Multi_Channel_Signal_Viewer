import sys
import numpy as np
import pandas as pd
import time
import os
import requests
from PyQt5.QtCore import pyqtSignal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.platypus import Table
from PyQt5.QtGui import QBrush, QPen, QPainter, QImage
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton, QDialog,QDialogButtonBox,QGroupBox,QButtonGroup,
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit,
                             QScrollBar, QGridLayout, QComboBox, QFileDialog, QColorDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QRect
import pyqtgraph as pg
from pyqtgraph import exporters
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from datetime import datetime

class Signal:
    def __init__(self, file_name, file_path, data, color, graph, show):
        self.name = file_name
        self.path = file_path
        self.data = data
        self.color = color
        self.graph = graph
        self.show = show
        self.last_index = 0  # Initialize last index to 0

    def __str__(self):
        return (f"Name: {self.name}, Path: {self.path}, Data: {self.data}, Color: {self.color}, Graph: {self.graph}, "
                f"Show: {self.show}")

class MoveDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Move Signal")
        layout = QVBoxLayout()

        # Group 1: Source selection
        self.source_group = QGroupBox("Select source graph")
        source_layout = QVBoxLayout()
        self.source_buttons = QButtonGroup(self)
        
        self.source_radiobuttons = {
            'graph1': QRadioButton("Graph 1"),
            'graph2': QRadioButton("Graph 2"),
            'glued_signal': QRadioButton("Glued Signal"),
            'graph3': QRadioButton("Graph 3")
        }

        for i, (key, rb) in enumerate(self.source_radiobuttons.items()):
            source_layout.addWidget(rb)
            self.source_buttons.addButton(rb, i)

        self.source_group.setLayout(source_layout)
        layout.addWidget(self.source_group)

        # Group 2: Destination selection
        self.destination_group = QGroupBox("Select destination graph")
        destination_layout = QVBoxLayout()
        self.destination_buttons = QButtonGroup(self)

        self.destination_radiobuttons = {
            'graph1': QRadioButton("Graph 1"),
            'graph2': QRadioButton("Graph 2"),
            'glued_signal': QRadioButton("Glued Signal"),
            'graph3': QRadioButton("Graph 3")
        }

        for i, (key, rb) in enumerate(self.destination_radiobuttons.items()):
            destination_layout.addWidget(rb)
            self.destination_buttons.addButton(rb, i)

        self.destination_group.setLayout(destination_layout)
        layout.addWidget(self.destination_group)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_selected_graphs(self):
        source_graph = None
        destination_graph = None

        for key, rb in self.source_radiobuttons.items():
            if rb.isChecked():
                source_graph = key

        for key, rb in self.destination_radiobuttons.items():
            if rb.isChecked():
                destination_graph = key

        return source_graph, destination_graph





class CircleGraph(QWidget):
    def __init__(self):
        super().__init__()
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
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
         # Create scrollbars for each graph
        self.graph1_vertical_scroll = QScrollBar(Qt.Vertical)
        self.graph1_horizontal_scroll = QScrollBar(Qt.Horizontal)
        self.graph2_vertical_scroll = QScrollBar(Qt.Vertical)
        self.graph2_horizontal_scroll = QScrollBar(Qt.Horizontal)
        self.glued_vertical_scroll = QScrollBar(Qt.Vertical)
        self.glued_horizontal_scroll = QScrollBar(Qt.Horizontal)
        self.graph3_vertical_scroll = QScrollBar(Qt.Vertical)
        self.graph3_horizontal_scroll = QScrollBar(Qt.Horizontal)
        #Initialize previous values for scrollbars
        self.prev_graph1_x_scroll = 0
        self.prev_graph1_y_scroll = 0
        self.prev_graph2_x_scroll = 0
        self.prev_graph2_y_scroll = 0
        self.prev_glued_x_scroll = 0
        self.prev_glued_y_scroll = 0
        self.prev_graph3_x_scroll = 0
        self.prev_graph3_y_scroll = 0


        self.initUI()

        # Connect existing scrollbars to their respective methods
        self.graph1_horizontal_scroll.setPageStep(10)    # Adjust step size
        self.graph1_horizontal_scroll.setSingleStep(1)   # Fine-tune step size
        self.graph1_horizontal_scroll.valueChanged.connect(self.graph1_x_scroll_moved)
        self.graph1_vertical_scroll.valueChanged.connect(self.graph1_y_scroll_moved)

        self.graph2_horizontal_scroll.setPageStep(10)    # Adjust step size
        self.graph2_horizontal_scroll.setSingleStep(1)   # Fine-tune step size
        self.graph2_horizontal_scroll.valueChanged.connect(self.graph2_x_scroll_moved)
        self.graph2_vertical_scroll.valueChanged.connect(self.graph2_y_scroll_moved)

        self.glued_horizontal_scroll.setPageStep(10)    # Adjust step size
        self.glued_horizontal_scroll.setSingleStep(1)   # Fine-tune step size
        self.glued_horizontal_scroll.valueChanged.connect(self.glued_x_scroll_moved)
        self.glued_vertical_scroll.valueChanged.connect(self.glued_y_scroll_moved)

        self.graph3_horizontal_scroll.setPageStep(10)    # Adjust step size
        self.graph3_horizontal_scroll.setSingleStep(1)   # Fine-tune step size
        self.graph3_horizontal_scroll.valueChanged.connect(self.graph3_x_scroll_moved)
        self.graph3_vertical_scroll.valueChanged.connect(self.graph3_y_scroll_moved)
        self.is_playing = False 
        self.linked=False

        self.timer = QTimer(self)

        self.sampling_rate = 50
        self.timer_interval = int(1000 / self.sampling_rate)  # Convert to integer

        # Define sampling rates
        self.update_graphs_sampling_rate = self.timer_interval  # 900 ms for graph updates
        self.real_time_sampling_rate = 500      # 1000 ms for real-time updates
        self.circular_graph_sampling_rate = 700  # 1300 ms for circular graph updates

        # Create a timer for updating graphs
        self.update_graphs_timer = QTimer(self)
        self.update_graphs_timer.timeout.connect(self.update_graphs)  # Connect update_graphs to this timer
        self.update_graphs_timer.start(self.update_graphs_sampling_rate)  # Start with 900 ms interval

        # Create a timer for real-time updates
        self.real_time_timer = QTimer(self)
        self.real_time_timer.timeout.connect(self.update_real_time_graphs)
        self.real_time_timer.timeout.connect(self.connect_to_signal)
        self.real_time_timer.start(self.real_time_sampling_rate)  # Start with 1000 ms interval

        # Create a timer for circular graph updates
        self.circular_graph_timer = QTimer(self)
        self.circular_graph_timer.timeout.connect(self.update_circular_graph)
        self.circular_graph_timer.start(self.circular_graph_sampling_rate)  # Start with 1300 ms interval


        self.signal_data = {
            'Graph 1': None,
            'Graph 2': None,
            'Glued Signals': None,
            'Graph 3': None
        }
        # Create separate timers for each graph
        self.timers = {
            'Graph 1': QTimer(self),
            'Graph 2': QTimer(self),
            'Glued Signals': QTimer(self),
            'Graph 3': QTimer(self)
        }
        
        for timer in self.timers.values():
            timer.timeout.connect(self.update_graphs)

        self.time_index = {
            'Graph 1': 0,
            'Graph 2': 0,
            'Glued Signals': 0,
            'Graph 3': 0
        }

        # Store the full plotted data for each graph
        self.plotted_data = {
            'Graph 1': ([], []),
            'Graph 2': ([], []),
            'Glued Signals': ([], []),
            'Graph 3': ([], [])
        }
        self.time_index = {key: 0 for key in self.signal_data.keys()}
        self.plotted_data = {key: ([], []) for key in self.signal_data.keys()}

        # Initialize graph colors
        self.graph_colors = {
            'Graph 1': 'r',
            'Graph 2': 'g',
            'Glued Signals': 'b',
            'Graph 3': 'y'
    }
        self.hidden_signals = {
            'Graph 1': False,
            'Graph 2': False,
            'Glued Signals': False,
            'Graph 3': False
    }
        self.is_playing_graph = {
        'Graph 1': False,
        'Graph 2': False,
        'Glued Signals': False,
        'Graph 3': False
    }
        self.plotComboBox.setCurrentIndex(1)  # Set default to first item

    def initUI(self):
        # Layout for the entire window
        mainLayout = QVBoxLayout()

        # Top Row: Open, Connect, and Text Field for signal source
        topLayout = QHBoxLayout()
        openBtn = QPushButton('Open')
        connectBtn = QPushButton('Connect')
        self.signalInput = QLineEdit('Enter address of a realtime signal source')
        self.graph1Radio = QRadioButton('Graph 1')
        self.graph2Radio = QRadioButton('Graph 2')
        self.gluedRadio = QRadioButton('Glued Signals')
        self.graph3Radio = QRadioButton('Graph 3')

        # Set the first radio button as checked by default
        self.graph1Radio.setChecked(True)
        plotComboBox = QComboBox()
        plotComboBox.addItem("Select Plot")  # Default text
        plotComboBox.addItem("Graph 1")
        plotComboBox.addItem("Graph 2")
        plotComboBox.addItem("Glued Signals")
        plotComboBox.addItem("Graph 3")

        topLayout.addWidget(openBtn)
        topLayout.addWidget(connectBtn)
        topLayout.addWidget(self.signalInput)
        topLayout.addWidget(plotComboBox)

        mainLayout.addLayout(topLayout)
        self.plotComboBox = plotComboBox
        self.plotComboBox.setCurrentIndex(1)  # Set default to "Graph 1"

        graphLayout = QGridLayout()

        # Editable labels for renaming graphs
        graph1Label = QLineEdit('Graph 1')
        graph2Label = QLineEdit('Graph 2')
        gluedLabel = QLineEdit('Glued Signals')
        graph3Label = QLineEdit('Graph 3')

        # Initialize graphs
        self.graph1 = pg.PlotWidget()
        self.graph1.showGrid(x=True, y=True)
        self.graph1.setLimits(xMin=0)

        self.graph2 = pg.PlotWidget()
        self.graph2.showGrid(x=True, y=True)
        self.graph2.setLimits(xMin=0)

        self.gluedGraph = pg.PlotWidget()
        self.gluedGraph.showGrid(x=True, y=True)
        self.gluedGraph.setLimits(xMin=0)

        self.graph3 = CircleGraph()

        # Set sizes for the graphs
        self.graph1.setFixedSize(400, 300)
        self.graph2.setFixedSize(400, 300)
        self.gluedGraph.setFixedSize(400, 300)
        self.graph3.setFixedSize(400, 300)

        graphLayout.addWidget(graph1Label, 0, 1)
        graphLayout.addWidget(graph2Label, 0, 3)

        graphLayout.addWidget(self.graph1, 1, 1)
        # graphLayout.addWidget(QScrollBar(Qt.Vertical), 1, 0)  # Scroll for graph 1
        # graphLayout.addWidget(QScrollBar(Qt.Horizontal), 2, 1)  # Scroll for graph 1
        graphLayout.addWidget(self.graph1_vertical_scroll, 1, 0)
        graphLayout.addWidget(self.graph1_horizontal_scroll, 2, 1)

        graphLayout.addWidget(self.graph2, 1, 3)
        # graphLayout.addWidget(QScrollBar(Qt.Vertical), 1, 2)  # Scroll for graph 2
        # graphLayout.addWidget(QScrollBar(Qt.Horizontal), 2, 3)  # Scroll for graph 2
        graphLayout.addWidget(self.graph2_vertical_scroll, 1, 2)
        graphLayout.addWidget(self.graph2_horizontal_scroll, 2, 3)


        graphLayout.addWidget(gluedLabel, 3, 1)
        graphLayout.addWidget(self.gluedGraph, 4, 1)
        # graphLayout.addWidget(QScrollBar(Qt.Vertical), 4, 0)  # Scroll for glued signals
        # graphLayout.addWidget(QScrollBar(Qt.Horizontal), 5, 1)  # Scroll for glued signals
        graphLayout.addWidget(self.glued_vertical_scroll, 4, 0)
        graphLayout.addWidget(self.glued_horizontal_scroll, 5, 1)

        graphLayout.addWidget(graph3Label, 3, 3)
        graphLayout.addWidget(self.graph3, 4, 3)
       # graphLayout.addWidget(QScrollBar(Qt.Vertical), 4, 2)  # Scroll for graph 3
        # graphLayout.addWidget(QScrollBar(Qt.Horizontal), 5, 3)  # Scroll for graph 3
        graphLayout.addWidget(self.graph3_vertical_scroll, 4, 2)
        graphLayout.addWidget(self.graph3_horizontal_scroll, 5, 3)


        mainLayout.addLayout(graphLayout)

        # Cine Speed Slider
        cineSpeedLayout = QHBoxLayout()
        cineSpeedLabel = QLabel('Cine Speed:')
        self.cineSpeedSlider = QSlider(Qt.Horizontal)
        self.cineSpeedSlider.setRange(1, 100)  # Set range for speed (1ms to 100ms)
        self.cineSpeedSlider.setValue(10)  # Default speed value (10ms)
        self.cineSpeedSlider.valueChanged.connect(self.update_timer_interval)  # Connect slider to function
        cineSpeedLayout.addWidget(cineSpeedLabel)
        cineSpeedLayout.addWidget(self.cineSpeedSlider)

        mainLayout.addLayout(cineSpeedLayout)

        # Bottom Controls
        bottomLayout = QHBoxLayout()
        zoomOutBtn = QPushButton('Zoom Out')
        linkBtn = QPushButton('Link')
        showHideBtn = QPushButton('Show / Hide')
        self.playPauseBtn = QPushButton('Play / Pause')
        rewindBtn = QPushButton('Rewind')
        zoomInBtn = QPushButton('Zoom In')

        bottomLayout.addWidget(zoomOutBtn)
        bottomLayout.addWidget(linkBtn)
        bottomLayout.addWidget(showHideBtn)
        bottomLayout.addWidget(self.playPauseBtn)
        bottomLayout.addWidget(rewindBtn)
        bottomLayout.addWidget(zoomInBtn)

        moveBtn = QPushButton('Move')
        colorBtn = QPushButton('Color')
        snapshotBtn = QPushButton('Snapshot')
        exportReportBtn = QPushButton('Export Report')

        bottomLayout.addWidget(moveBtn)
        bottomLayout.addWidget(colorBtn)
        bottomLayout.addWidget(self.signalInput)
        bottomLayout.addWidget(snapshotBtn)
        bottomLayout.addWidget(exportReportBtn)
        bottomLayout.addWidget(showHideBtn)


        mainLayout.addLayout(bottomLayout)

        # Connect buttons
        openBtn.clicked.connect(self.openFile)
        connectBtn.clicked.connect(self.connect_to_signal)  # Connect the connect button to the method
        colorBtn.clicked.connect(self.openColorDialog)
        snapshotBtn.clicked.connect(self.take_snapshot)
        exportReportBtn.clicked.connect(self.export_report)
        rewindBtn.clicked.connect(self.rewind)
        self.playPauseBtn.clicked.connect(self.toggle_play_pause)
        zoomInBtn.clicked.connect(self.zoom_in)
        zoomOutBtn.clicked.connect(self.zoom_out)
        linkBtn.clicked.connect(self.linkGraphs)
        showHideBtn.clicked.connect(self.toggle_signal_visibility)
        moveBtn.clicked.connect(self.show_move_dialog)


        # Set main layout
        self.setLayout(mainLayout)
        self.setWindowTitle('Signal Viewer')
        self.show()

    def graph1_x_scroll_moved(self):
        """Handle horizontal scrolling for graph1."""
        current_value = self.graph1_horizontal_scroll.value()
        difference = current_value - self.prev_graph1_x_scroll
        
        if difference != 0:
            self.update_graph_view(self.graph1, 'x', difference)
        
        # Update the previous value to the current value
        self.prev_graph1_x_scroll = current_value

    def graph1_y_scroll_moved(self):
        """Handle vertical scrolling for graph1."""
        current_value = self.graph1_vertical_scroll.value()
        difference = current_value - self.prev_graph1_y_scroll
        
        if difference != 0:
            self.update_graph_view(self.graph1, 'y', difference)
        
        # Update the previous value to the current value
        self.prev_graph1_y_scroll = current_value

    def graph2_x_scroll_moved(self):
        current_value = self.graph2_horizontal_scroll.value()
        difference = current_value - self.prev_graph2_x_scroll
        
        if difference != 0:
            self.update_graph_view(self.graph2, 'x', difference)
        
        self.prev_graph2_x_scroll = current_value

    def graph2_y_scroll_moved(self):
        current_value = self.graph2_vertical_scroll.value()
        difference = current_value - self.prev_graph2_y_scroll
        
        if difference != 0:
            self.update_graph_view(self.graph2, 'y', difference)
        
        self.prev_graph2_y_scroll = current_value

    def glued_x_scroll_moved(self):
        current_value = self.glued_horizontal_scroll.value()
        difference = current_value - self.prev_glued_x_scroll
        
        if difference != 0:
            self.update_graph_view(self.gluedGraph, 'x', difference)
        
        self.prev_glued_x_scroll = current_value

    def glued_y_scroll_moved(self):
        current_value = self.glued_vertical_scroll.value()
        difference = current_value - self.prev_glued_y_scroll
        
        if difference != 0:
            self.update_graph_view(self.gluedGraph, 'y', difference)
        
        self.prev_glued_y_scroll = current_value

    def graph3_x_scroll_moved(self):
        current_value = self.graph3_horizontal_scroll.value()
        difference = current_value - self.prev_graph3_x_scroll
        
        if difference != 0:
            self.update_graph_view(self.graph3, 'x', difference)
        
        self.prev_graph3_x_scroll = current_value

    def graph3_y_scroll_moved(self):
        current_value = self.graph3_vertical_scroll.value()
        difference = current_value - self.prev_graph3_y_scroll
        
        if difference != 0:
            self.update_graph_view(self.graph3, 'y', difference)
        
        self.prev_graph3_y_scroll = current_value
    
    def update_graph_view(self, graph, axis, difference):
        """Update graph's view range based on scroll movement."""
        current_range = graph.viewRange()  # Get the current view range

        # Scaling factor to control scroll sensitivity
        scaling_factor = 0.1

        if axis == 'x':
            # Adjust X-axis range based on scroll difference (scaled down)
            new_x_min = current_range[0][0] + difference * scaling_factor
            new_x_max = current_range[0][1] + difference * scaling_factor
            graph.setXRange(new_x_min, new_x_max, padding=0)
        elif axis == 'y':
            # Adjust Y-axis range based on scroll difference
            new_y_min = current_range[1][0] + difference
            new_y_max = current_range[1][1] + difference
            graph.setYRange(new_y_min, new_y_max, padding=0)


    def show_move_dialog(self):
        dialog = MoveDialog()
        if dialog.exec_() == QDialog.Accepted:
            source_graph, destination_graph = dialog.get_selected_graphs()
            
            # Standardize graph names based on their keys
            graph_names = {
                'graph1': 'Graph 1',
                'graph2': 'Graph 2',
                'glued_signal': 'Glued Signals',
                'graph3': 'Graph 3'
            }

            # Ensure valid selection
            source_graph = graph_names.get(source_graph, None)
            destination_graph = graph_names.get(destination_graph, None)
            
            if source_graph and destination_graph:
                self.move_signal(source_graph, destination_graph)  
    def refresh_plot(self, graph_name):
        # Refresh the plot by replotting data for the given graph
        if graph_name == 'Graph 1':
            self.graph1.plot(self.plotted_data['Graph 1'][0], self.plotted_data['Graph 1'][1], clear=True)
        elif graph_name == 'Graph 2':
            self.graph2.plot(self.plotted_data['Graph 2'][0], self.plotted_data['Graph 2'][1], clear=True)
        elif graph_name == 'Glued Signals':
            self.gluedGraph.plot(self.plotted_data['Glued Signals'][0], self.plotted_data['Glued Signals'][1], clear=True)
        elif graph_name == 'Graph 3':
            self.graph3.plot(self.plotted_data['Graph 3'][0], self.plotted_data['Graph 3'][1], clear=True)
            ########################## move signal with dynamic display but starting from the beginning ################ 
    def move_signal(self, source, destination): 
        if source != destination and self.is_playing_graph[source]: 
            # Retrieve the entire signal data from the source
            signal_data = self.signal_data[source]  # Get the current signal data for the source
            
            # Check if there's any signal data to move
            if signal_data is not None:
                # Copy the signal data to the destination graph
                self.signal_data[destination] = signal_data

                # Clear the source data after moving
                self.signal_data[source] = None  # Clear source graph data

                # Clear the plot on the source graph
                self.clear_plot(source)

                # Refresh both source and destination plots
                #self.refresh_plot(source)
                self.refresh_plot(destination)

                # Update playing states
                self.is_playing_graph[destination] = True  # Start playing on the destination graph
                self.is_playing_graph[source] = False  # Stop playing on the source graph

                # Plot the updated signal on the destination graph
                self.plot_signal(destination)
            
                
                self.update_graphs()  # Update all graphs

    def clear_plot(self, graph_name):
        # Clear the plot by setting its data to empty lists
        if graph_name == 'Graph 1':
            self.graph1.plot([], [], clear=True)  # Clear Graph 1
        elif graph_name == 'Graph 2':
            self.graph2.plot([], [], clear=True)  # Clear Graph 2
        elif graph_name == 'Glued Signals':
            self.gluedGraph.plot([], [], clear=True)  # Clear Glued Signals
        elif graph_name == 'Graph 3':
            self.graph3.plot([], [], clear=True)  # Clear Graph 3



    

    def update_timer_interval(self):
        speed = self.cineSpeedSlider.value()  # Get the current value of the slider
        self.timer_interval = 1000 / speed  # Calculate the new timer interval
        self.timer.start(int(self.timer_interval))  # Update the timer with the new interval

    def openFile(self):
                if self.plotComboBox.currentText() == 'Graph 3':
                    # Open a file dialog to browse the PC to select a signal file
                    file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                               "Text Files (*.txt);;All Files (*)")
                    if file_name:
                        self.data = np.loadtxt(file_name)  # Load the data from the file
                        self.graph3.data = self.data  # Pass the data to the graph widget
                        self.graph3.angle = 0  # Reset the angle for radar mode

                        # Start displaying the signal in cine mode
                        self.start_cine_mode()

                else :
                    file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                               "CSV Files (*.csv);;All Files (*)")
                    if file_name:
                        # Load the data from the file
                        time, selected_signal = self.load_signal_data(file_name)
                        selected_graph = self.plotComboBox.currentText()

                        # Store the loaded signal in the corresponding graph's entry
                        if selected_graph in self.signal_data:
                            # Check if the current signal is already loaded; If not, initialize it
                            if self.signal_data[selected_graph] is None:
                                self.signal_data[selected_graph] = (time, selected_signal)
                                self.time_index[selected_graph] = 0

                            else:
                                # Append new data to existing data
                                existing_time, existing_signal = self.signal_data[selected_graph]
                                self.signal_data[selected_graph] = (np.concatenate((existing_time, time)),
                                                                    np.concatenate((existing_signal, selected_signal)))

                        # Clear previously plotted data for the selected graph
                        self.plotted_data[selected_graph] = ([], [])
                        # Update the graph with the newly loaded signal
                        self.update_graphs()
                        # Set the graph to play after loading
                        self.is_playing_graph[selected_graph] = True
                        self.playPauseBtn.setText('Pause') 
                        self.toggle_play_pause()


    def load_signal_data(self, file_name):
        if self.plotComboBox.currentText() != 'Graph 3':
            """Load ECG data from a CSV file."""
            data = pd.read_csv(file_name, header=None)
            time = data[0].to_numpy()
            amplitude = data[1].to_numpy()
            return time, amplitude

    def connect_to_signal(self):
        url = self.signalInput.text().strip()  # Get URL from input field and trim whitespace

        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return  # Do nothing if URL is invalid or empty

        try:
            response = requests.get(url)  # Send a request to the API
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()  # Parse JSON response

            # Check for 'price' in the response
            if 'price' in data:
                price = float(data['price'])  # Extract price as a float

                current_time = time.time()  # Get the current time for plotting
                selected_graph = self.plotComboBox.currentText()  # Get the selected graph from the combo box
                if self.signal_data[selected_graph] is None:
                    self.signal_data[selected_graph] = ([], [])  # Initialize if None

                # Append the new data to your signal data
                self.signal_data[selected_graph][0].append(current_time)  # Time data
                self.signal_data[selected_graph][1].append(price)  # Price data

                print(f"Current Price: {price}")  # For debugging

                # Update the graphs after adding new data
                self.update_real_time_graphs()  # Update graphs with new data

            else:
                print("Error: 'price' key not found in the response.")

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to signal: {e}")
        except ValueError as e:
            print(f"Error parsing JSON: {e}")

    def update_graphs(self):
        """Update all graphs with their respective ECG data."""
        for graph_name in self.signal_data.keys():
              if self.signal_data[graph_name] is not None and self.is_playing_graph[graph_name]:
                time, signal = self.signal_data[graph_name]  # Unpack the tuple
                current_index = self.time_index[graph_name]
          
                if current_index < len(signal):
                # Append the new data point for plotting
                 self.plotted_data[graph_name][0].append(time[current_index])
                 self.plotted_data[graph_name][1].append(signal[current_index])

                # Plot the full line so far
                self.plot_signal(graph_name)
                self.time_index[graph_name] += 1  # Increment time index for this graph

    def update_real_time_graphs(self):
        """Update all graphs with their respective ECG data."""
        for graph_name in self.signal_data.keys():
            if self.signal_data[graph_name] is not None:
                time, signal = self.signal_data[graph_name]  # Unpack the tuple
                
                # Clear the existing plot and plot new data
                if graph_name == 'Graph 1':
                    self.graph1.clear()
                    
                    # Set y-axis limits based on signal range
                    min_signal = min(signal)  # Find the minimum value in the signal
                    max_signal = max(signal)  # Find the maximum value in the signal
                    
                    padding = 0.1  # Adjust this value as needed for better visibility
                    self.graph1.setYRange(min_signal - padding, max_signal + padding)  # Set y-axis limits
                    
                    self.graph1.plot(time, signal, pen='r')  # Use a white pen for better visibility

                elif graph_name == 'Graph 2':
                    self.graph2.clear()
                    
                    min_signal = min(signal)
                    max_signal = max(signal)
                    
                    padding = 0.1
                    self.graph2.setYRange(min_signal - padding, max_signal + padding)
                    
                    self.graph2.plot(time, signal, pen='r')

                elif graph_name == 'Glued Signals':
                    self.gluedGraph.clear()
                    
                    min_signal = min(signal)
                    max_signal = max(signal)
                    
                    padding = 0.1
                    self.gluedGraph.setYRange(min_signal - padding, max_signal + padding)
                    
                    self.gluedGraph.plot(time, signal, pen='r')

                elif graph_name == 'Graph 3':
                    self.graph3.clear()
                    
                    min_signal = min(signal)
                    max_signal = max(signal)
                    
                    padding = 0.1
                    self.graph3.setYRange(min_signal - padding, max_signal + padding)
                    
                    self.graph3.plot(time, signal, pen='r')

                
    def plot_signal(self, graph_name):
        """Plot the signal on the appropriate graph."""
        if self.hidden_signals[graph_name]:
            # If the signal is hidden, clear the graph and return
            if graph_name == "Graph 1":
                self.graph1.clear()
            elif graph_name == "Graph 2":
                self.graph2.clear()
            elif graph_name == "Glued Signals":
                self.gluedGraph.clear()
        
            return  # Don't plot anything if hidden

        color = self.graph_colors[graph_name]  # Get the current color for the graph
        if graph_name == "Graph 1":
            self.graph1.clear()
            self.graph1.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen=color)
        elif graph_name == "Graph 2":
            self.graph2.clear()
            self.graph2.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen=color)
        elif graph_name == "Glued Signals":
            self.gluedGraph.clear()
            self.gluedGraph.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen=color)
        elif graph_name == "Graph 3":
            self.graph3.clear()
            self.graph3.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen=color)

    def toggle_signal_visibility(self):
        """Toggle the visibility of the selected graph's signal."""
        selected_graph = self.plotComboBox.currentText()
         #######linking 
        if self.linked==True &((selected_graph=="Graph 1")or(selected_graph=="Graph 2")):
         if self.is_playing_graph["Graph 1"] and self.is_playing_graph["Graph 2"]:
            if "Graph 1" in self.hidden_signals or "Graph 2" in self.hidden_signals:
                self.hidden_signals["Graph 1"] = not self.hidden_signals["Graph 1"]
                self.hidden_signals["Graph 2"] = not self.hidden_signals["Graph 2"]
                self.update_graphs() 
        #if selected_graph in self.hidden_signals:
        else:        
         if selected_graph in self.hidden_signals:
            self.hidden_signals[selected_graph] = not self.hidden_signals[selected_graph]
        self.update_graphs()  # Refresh the graph to apply visibility changes
       

    def rewind(self):
      """Rewind the selected graph to the beginning."""
      selected_graph = self.plotComboBox.currentText()
      if selected_graph in self.signal_data:
        # Reset time index for the selected graph
        self.time_index[selected_graph] = 0
        # Clear the plotted data
        self.plotted_data[selected_graph] = ([], [])
        # Clear the graph
        self.plot_signal(selected_graph)  # Refresh the graph  
         ################### linking working ################
      if self.linked==True &((selected_graph=="Graph 1")or(selected_graph=="Graph 2")):
         if self.is_playing_graph["Graph 1"] and self.is_playing_graph["Graph 2"]:
            self.time_index["Graph 1"] = 0
            self.time_index["Graph 2"] = 0
            self.plotted_data["Graph 1"] = ([], [])
            self.plotted_data["Graph 2"] = ([], [])
            self.plot_signal("Graph 1")
            self.plot_signal("Graph 2")

    def toggle_play_pause(self):
     """Toggle between play and pause."""
     selected_graph = self.plotComboBox.currentText()

     # Toggle the selected graph's play/pause state
     if selected_graph in self.is_playing_graph:
        self.is_playing_graph[selected_graph] = not self.is_playing_graph[selected_graph]

        if self.is_playing_graph[selected_graph]:
            # Start the timer for the selected graph
            self.timers[selected_graph].start(int(self.timer_interval))
            self.playPauseBtn.setText('Pause')
        else:
            # Stop the timer for the selected graph
            self.timers[selected_graph].stop()
            self.playPauseBtn.setText('Play')

      # Handle linking for Graph 1 and Graph 2
     if self.linked and (selected_graph == "Graph 1" or selected_graph == "Graph 2"):
        graph1_playing = self.is_playing_graph["Graph 1"]
        graph2_playing = self.is_playing_graph["Graph 2"]

        # If either graph is playing, stop both
        if graph1_playing or graph2_playing:
            self.is_playing_graph["Graph 1"] = False
            self.is_playing_graph["Graph 2"] = False
            self.timers["Graph 1"].stop()
            self.timers["Graph 2"].stop()
            self.playPauseBtn.setText('Play')
        else:
            # If both are paused, start both
            self.is_playing_graph["Graph 1"] = True
            self.is_playing_graph["Graph 2"] = True
            self.timers["Graph 1"].start(int(self.timer_interval))
            self.timers["Graph 2"].start(int(self.timer_interval))
            self.playPauseBtn.setText('Pause')

    
    def zoom_in(self):
      selected_graph = self.plotComboBox.currentText()
      if selected_graph in self.signal_data and self.signal_data[selected_graph] is not None:
        current_view = self.get_current_view(selected_graph)
        new_range = (
            max(current_view[0] + (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds(selected_graph)[0]),
            min(current_view[1] - (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds(selected_graph)[1])
        )
        self.set_view_range(selected_graph, new_range)
       ############### Linking working #############
      if self.linked==True &((selected_graph=="Graph 1")or(selected_graph=="Graph 2")):
         if self.is_playing_graph["Graph 1"] and self.is_playing_graph["Graph 2"]:
            current_view = self.get_current_view("Graph 1")
            new_range = (
                max(current_view[0] + (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds("Graph 1")[0]),
                min(current_view[1] - (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds("Graph 2")[1])
            )
            self.set_view_range("Graph 1", new_range)
            self.set_view_range("Graph 2", new_range)
  

    def zoom_out(self):
       selected_graph = self.plotComboBox.currentText()
       if selected_graph in self.signal_data and self.signal_data[selected_graph] is not None:
        current_view = self.get_current_view(selected_graph)
        new_range = (
            max(current_view[0] - (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds(selected_graph)[0]),
            min(current_view[1] + (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds(selected_graph)[1])
        )
        self.set_view_range(selected_graph, new_range) 

         ############### Linking working #############
       if self.linked==True &((selected_graph=="Graph 1")or(selected_graph=="Graph 2")):
         if self.is_playing_graph["Graph 1"] and self.is_playing_graph["Graph 2"]:
            current_view = self.get_current_view("Graph 1")
            new_range = (
                max(current_view[0] - (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds("Graph 1")[0]),
                min(current_view[1] + (current_view[1] - current_view[0]) * 0.25, self.get_signal_bounds("Graph 1")[1])
            )
            self.set_view_range("Graph 1", new_range) 
            self.set_view_range("Graph 2", new_range)

    def recenter_view(self, graph_name):
     """Recenter the view to focus on the latest data point."""
     if graph_name in self.plotted_data and self.plotted_data[graph_name][0]:
        # Focus on the latest point added
        last_time = self.plotted_data[graph_name][0][-1]
        view_range = self.get_current_view(graph_name)
        
        # Adjust the view range to keep it centered around the last time point
        new_range = (
            max(last_time - (view_range[1] - view_range[0]) / 2, self.get_signal_bounds(graph_name)[0]),
            min(last_time + (view_range[1] - view_range[0]) / 2, self.get_signal_bounds(graph_name)[1])
        )
        self.set_view_range(graph_name, new_range)

    def get_signal_bounds(self, graph_name):
     if graph_name in self.signal_data and self.signal_data[graph_name] is not None:
        time, _ = self.signal_data[graph_name]
        return time[0], time[-1]  # Return the min and max time
     return 0, 1  # Default bounds if no data   

    def get_current_view(self, graph_name):
        if graph_name == "Graph 1":
            return self.graph1.viewRange()[0]
        elif graph_name == "Graph 2":
            return self.graph2.viewRange()[0]
        elif graph_name == "Glued Signals":
            return self.gluedGraph.viewRange()[0]
        elif graph_name == "Graph 3":
            return self.graph3.viewRange()[0]

    def set_view_range(self, graph_name, new_range):
     min_bound, max_bound = self.get_signal_bounds(graph_name)
     new_range = (max(new_range[0], min_bound), min(new_range[1], max_bound))
    
     if graph_name == "Graph 1":
        self.graph1.setXRange(*new_range)
     elif graph_name == "Graph 2":
        self.graph2.setXRange(*new_range)
     elif graph_name == "Glued Signals":
        self.gluedGraph.setXRange(*new_range)
     elif graph_name == "Graph 3":
        self.graph3.setXRange(*new_range)

    def openColorDialog(self):
       """Open a color dialog to change the color of the selected graph."""
       selected_graph = self.plotComboBox.currentText()
       color = QColorDialog.getColor()

       if color.isValid():
        # Update the color for the selected graph
        self.graph_colors[selected_graph] = color.name()  # Store the color name
        self.plot_signal(selected_graph)  # Re-plot the graph with the new color
         ############# linking working #############
       if self.linked==True &((selected_graph=="Graph 1")or(selected_graph=="Graph 2")):
         if self.is_playing_graph["Graph 1"] and self.is_playing_graph["Graph 2"]:
            self.graph_colors["Graph 1"] = color.name() 
            self.graph_colors["Graph 2"] = color.name() 
            self.plot_signal("Graph 1")
            self.plot_signal("Graph 2")
     
    def linkGraphs(self):
        if self.linked:
            # Unlink graph1 and graph2
            self.graph1.setXLink(None)
            self.graph2.setXLink(None)
            self.linked = False
        else:
            # Link graph1 and graph2
            self.graph1.setXLink(self.graph2)
            x_range = self.graph1.viewRange()[0]
            self.graph2.setXRange(x_range[0], x_range[1])
            self.linked = True  
               
    def update_circular_graph(self):
        if self.graph3.data is not None:
            self.graph3.update_circular_graph()  # Update graph for the current index
        else:
            self.stop_cine_mode()  # Stop if there is no data


    def start_cine_mode(self):
        if self.data is not None:
            self.timer.start(100)  # Update every 100 ms

    def stop_cine_mode(self):
        self.timer.stop()

    def take_snapshot(self):
        # Specify the directory where the snapshots will be saved
        snapshot_dir = "snapshots"
        os.makedirs(snapshot_dir, exist_ok=True)  # Create the directory if it doesn't exist

        # Define the filename with date and time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = os.path.join(snapshot_dir, f"snapshot_{timestamp}.png")

        # Access the "Glued Signals" graph
        glued_signals_plot = self.gluedGraph.plotItem  # Adjust this if necessary to get the correct graph

        # Take the snapshot
        exporter = pg.exporters.ImageExporter(glued_signals_plot)
        exporter.export(snapshot_filename)

        # Show success message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Snapshot saved successfully!")
        msg.setInformativeText(f"Saved to: {snapshot_filename}")
        msg.setWindowTitle("Snapshot Success")
        msg.exec_()

    def export_report(self):
        # Create the PDF file name based on the current date and time
        now = datetime.now()
        report_filename = f"reports/report_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"

        # Create a canvas object
        c = canvas.Canvas(report_filename, pagesize=letter)
        width, height = letter

        # Add images and text
        logo_height = 70  # height of the logo in the header
        c.drawImage("images/uni-logo.png", width - 150, height - logo_height - 40, width=100, height=logo_height)  # right side
        c.drawImage("images/sbme-logo.jpg", 50, height - logo_height - 40, width=100, height=logo_height)  # left side
        
        # Title in the middle
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width / 2, height - 90, "Biological Signal Report")

        # Take snapshot of "Glued Signals" graph
        snapshot_path = f"snapshots/snapshot_{now.strftime('%Y%m%d_%H%M%S')}.png"
        exporter = pg.exporters.ImageExporter(self.gluedGraph.plotItem)  # Adjust this to your actual reference
        exporter.export(snapshot_path)

        # Add the snapshot to the PDF
        snapshot_y_position = height - logo_height - 100  # Adjust this to place it below the title
        c.drawImage(snapshot_path, 50, snapshot_y_position - 200, width=500, height=200)  # Adjust positioning and size

        # Gather data from the gluedGraph (assuming it’s a PyQtGraph plot with data)
        # Extract the data from the graph for statistics calculation
        plot_data = self.gluedGraph.plotItem.listDataItems()[0].getData()  # Assuming the first data item
        y_data = plot_data[1]  # Get the y-values for statistics

        # Calculate statistics
        mean = np.mean(y_data)
        median = np.median(y_data)
        std_dev = np.std(y_data)
        min_val = np.min(y_data)
        max_val = np.max(y_data)

        # Create the table data
        table_data = [
            ['Statistic', 'Value'],
            ['Mean', f'{mean:.5f}'],
            ['Median', f'{median:.5f}'],
            ['Std_dev', f'{std_dev:.5f}'],
            ['Min', f'{min_val:.5f}'],
            ['Max', f'{max_val:.5f}'],
        ]

        # Create the table
        table = Table(table_data, colWidths=[200, 200])

        # Add style to the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)

        # Convert table into a canvas element
        table.wrapOn(c, width, height)
        table.drawOn(c, 103, snapshot_y_position - 370)  # Adjust positioning based on where you want the table


        # Finalize the PDF
        c.showPage()
        c.save()

        # Show success message
        QMessageBox.information(self, "Export Report", f"Report saved as {report_filename}.")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())