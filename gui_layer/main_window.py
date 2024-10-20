import sys
import numpy as np
import pandas as pd
import time
import functools
import os
import requests
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QBrush, QPen, QPainter, QImage, QColor
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton, QDialog,QDialogButtonBox,QGroupBox,QButtonGroup,
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit,
                             QScrollBar, QGridLayout, QFileDialog, QComboBox, QColorDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QRect
import pyqtgraph as pg
from pyqtgraph import exporters
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from datetime import datetime
from mediator_layer.mediator import Mediator
from gui_layer.widgets.custom_plot_widget import CustomPlotWidget
from gui_layer.widgets.custom_circular_plot_widget import CustomCircularPlotWidget
from gui_layer.widgets.custom_timer import CustomTimer
from gui_layer.widgets.circle_graph import CircleGraph
from logic_layer.logic_handler import LogicHandler

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
   
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.logic = LogicHandler()
        self.mediator = Mediator(self, self.logic)
        self.start_point = None
        self.selection_mode_enabled = False  # Flag to track selection mode
        self.current_rectangle_index = 0  # Track which rectangle is currently being drawn
        self.connected_signal = False
        self.initUI()
        self.linked=False

        # Connect existing scrollbars to their respective methods

        self.timer = QTimer(self)

        # Create a timer for updating graphs
        self.graphs_timer = CustomTimer(self, self.mediator, self.logic.timer_interval)
        self.graphs_timer.connect(self.update_interval_gui)  # Connect update_graphs to this timer
        self.graphs_timer.start(int(self.logic.timer_interval))  # Start the timer


        self.signal_data = {
            'Graph 1': None,
            'Graph 2': None,
            'Glued Signals': None,
            'Graph 3': None
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

    def update_interval_gui(self):
        if self.connected_signal:
            self.mediator.update_real_time_graphs()
            self.connect_to_signal()
        else:
            self.mediator.update_graphs()
        self.update_circular_graph()

    def initUI(self):
        # Layout for the entire window
        mainLayout = QVBoxLayout()
        self.selected_rectangles = []

        # Top Row: Open, Connect, and Text Field for signal source
        topLayout = QHBoxLayout()
        openBtn = QPushButton('Open')
        self.connectBtn = QPushButton('Connect')
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
        topLayout.addWidget(self.connectBtn)
        topLayout.addWidget(self.signalInput)
        topLayout.addWidget(plotComboBox)

        mainLayout.addLayout(topLayout)
        self.plotComboBox = plotComboBox
        self.plotComboBox.setCurrentIndex(1)  # Set default to "Graph 1"

        self.graphLayout = QGridLayout()

        # Initialize graphs
        self.graphs = [None]*4
        self.graphs[0] = CustomPlotWidget(self.mediator, 'Graph 1')
        self.graphs[1] = CustomPlotWidget(self.mediator, 'Graph 2')
        self.graphs[2] = CustomPlotWidget(self.mediator, 'Glued Signals')
        self.graphs[3] = CircleGraph(self.mediator, 'Graph 3')

        # Add widgets to the grid layout
        self.graphLayout.addWidget(self.graphs[0], 1, 1)
        self.graphLayout.addWidget(self.graphs[1], 1, 3)
        self.graphLayout.addWidget(self.graphs[2], 4, 1)
        self.graphLayout.addWidget(self.graphs[3], 4, 3)

        # Set the layout for the main window
        mainLayout.addLayout(self.graphLayout)

        # Create the new vertical layout for the 4 objects next to gluedGraph
        gluedOptionsLayout = QVBoxLayout()

        # Add the buttons and input boxes
        disableSelectedBtn = QPushButton('Enable Selected Mode')
        disableSelectedBtn.setFixedWidth(160)  # Set a custom width
        disableSelectedBtn.clicked.connect(self.toggle_selection_mode)
        self.selection_button = disableSelectedBtn

        plotConcatenatedBtn = QPushButton('Plot Concatenated Signals')
        plotConcatenatedBtn.setFixedWidth(160)  # Set a custom width
        plotConcatenatedBtn.clicked.connect(self.plot_concatenated_signals) 
        plotConcatenatedBtn.setEnabled(False)
        self.plot_button = plotConcatenatedBtn

        self.gapInput = QLineEdit()
        self.gapInput.setPlaceholderText('gap')
        self.gapInput.setFixedWidth(90)  # Set a custom width for the input box

        self.interpolationInput = QLineEdit()
        self.interpolationInput.setPlaceholderText('interpolation')
        self.interpolationInput.setFixedWidth(90)  # Set a custom width for the input box

        gluedOptionsLayout.addWidget(disableSelectedBtn)
        gluedOptionsLayout.addWidget(plotConcatenatedBtn)
        gluedOptionsLayout.addWidget(self.gapInput)
        gluedOptionsLayout.addWidget(self.interpolationInput)

        # Add the new layout next to gluedGraph in the grid
        self.graphLayout.addLayout(gluedOptionsLayout, 4, 2)
        mainLayout.addLayout(gluedOptionsLayout)

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
        openBtn.clicked.connect(self.open_file)
        self.connectBtn.clicked.connect(self.toggle_connect_signal)  # Connect the connect button to the method
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

    def open_file(self):
        selected_graph_name = self.plotComboBox.currentText()
        selected_graph = next((graph for graph in self.graphs if graph.name == selected_graph_name), None)
        if selected_graph_name == 'Graph 3':
            self.mediator.open_circular_plot_file(selected_graph)
            self.start_cine_mode()
        else:
            self.mediator.open_plot_file(selected_graph)
            self.playPauseBtn.setText('Pause')
            self.toggle_play_pause()

    def toggle_selection_mode(self, Window):
        is_enabled = self.mediator.toggle_subplot_selection_mode()
        self.selection_button.setText("Disable Selection Mode" if is_enabled else "Enable Selection Mode")
        CustomPlotWidget.selection_mode_enabled = is_enabled
        self.update()  # Trigger a repaint

    def toggle_connect_signal(self):
        if not self.connected_signal:
            selected_graph = self.plotComboBox.currentText()  # Get the selected graph from the combo box
            graph = next((graph for graph in self.graphs if graph.name == selected_graph), None)
            graph.enable_auto_range(not self.connected_signal)
        self.connected_signal = not self.connected_signal
        self.connectBtn.setText("Disconnect" if self.connected_signal else "Connect")
        self.update()  # Trigger a repaint

    def plot_concatenated_signals(self):
        # Get user inputs for gap/overlap and interpolation order
        gap_overlap = float(self.gapInput.text()) if self.gapInput.text() else 0
        interpolation_order = int(self.interpolationInput.text()) if self.interpolationInput.text() else 1
        # Concatenate the two selected signal arrays based on gap/overlap
        concatenated_signals = self.logic.glue_signals(gap_overlap, interpolation_order)

        self.plot_conc(concatenated_signals)

    def plot_conc(self, concatenated_signals):
        graph = self.graphs[2]
        x_vals = [conc[0] for conc in concatenated_signals]
        y_vals = [conc[1] for conc in concatenated_signals]
        print(y_vals, x_vals)
        graph.plot_widget.plot(x_vals, y_vals, pen='b')

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
                self.mediator.move_signal(source_graph, destination_graph)  

    def update_timer_interval(self):
        speed = self.cineSpeedSlider.value()  # Get the current value of the slider
        self.logic.timer_interval = 1000 / speed  # Calculate the new timer interval
        self.graphs_timer.start(int(self.logic.timer_interval))  # Update the timer with the new interval

    def connect_to_signal(self):
        selected_graph = self.plotComboBox.currentText()  # Get the selected graph from the combo box
        url = self.signalInput.text().strip()  # Get URL from input field and trim whitespace
        self.mediator.connect_to_signal(selected_graph, url)  # Connect to the selected signal
                
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
            self.graphs[3].clear()
            self.graphs[3].plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen=color)

    def toggle_signal_visibility(self):
        """Toggle the visibility of the selected graph's signal."""
        selected_graph = self.plotComboBox.currentText()
         #######linking 
        if self.linked==True &((selected_graph=="Graph 1")or(selected_graph=="Graph 2")):
         if self.is_playing_graph["Graph 1"] and self.is_playing_graph["Graph 2"]:
            if "Graph 1" in self.hidden_signals or "Graph 2" in self.hidden_signals:
                self.hidden_signals["Graph 1"] = not self.hidden_signals["Graph 1"]
                self.hidden_signals["Graph 2"] = not self.hidden_signals["Graph 2"]
        #if selected_graph in self.hidden_signals:
        else:        
         if selected_graph in self.hidden_signals:
            self.hidden_signals[selected_graph] = not self.hidden_signals[selected_graph]
       

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
        self.mediator.toggle_play_pause(selected_graph)
        # Handle linking for Graph 1 and Graph 2
        self.mediator.handle_linked_graphs(selected_graph)
        
    
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
            return self.graphs[3].viewRange()[0]

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
        self.graphs[3].setXRange(*new_range)

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
        if self.graphs[3].data is not None:
            self.graphs[3].update_circular_graph()  # Update graph for the current index
        else:
            self.stop_cine_mode()  # Stop if there is no data

    def start_cine_mode(self):
        if self.data is not None:
            self.timer.start(100)  # Update every 100 ms

    def stop_cine_mode(self):
        self.timer.stop()

    def take_snapshot(self):
        plot_item = self.graphs[2].plot_widget.plotItem
        snapshot_filename = self.mediator.take_snapshot(plot_item)

        # Show success message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Snapshot saved successfully!")
        msg.setInformativeText(f"Saved to: {snapshot_filename}")
        msg.setWindowTitle("Snapshot Success")
        msg.exec_()

    def export_report(self):
        plot_item = self.graphs[2].plot_widget.plotItem
        report_filename = self.mediator.export_report(plot_item)
        QMessageBox.information(self, "Export Report", f"Report saved as {report_filename}.")

    def update_plot_selection(self, selected_rectangles):
        self.selected_rectangles = selected_rectangles
        self.update()

    # def paintEvent(self, event):
    #     # Create a QPainter instance
    #     painter = QPainter(self)
    #     for rect in self.selected_rectangles:
    #         painter.setBrush(QColor(200, 200, 255))  # Light blue
    #         painter.drawRect(rect)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())