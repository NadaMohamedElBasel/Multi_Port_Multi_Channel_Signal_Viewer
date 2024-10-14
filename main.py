import sys
import numpy as np
import pandas as pd
import time
import os
import requests
from PyQt5.QtGui import QBrush, QPen, QPainter, QImage
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton,
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit,
                             QScrollBar, QGridLayout, QComboBox, QFileDialog, QColorDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
from pyqtgraph import exporters
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from datetime import datetime


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
        self.initUI()

        # Define sampling rate
        self.sampling_rate = 50
        self.timer_interval = int(1000 / self.sampling_rate)  # Convert to integer

        self.timer = QTimer()
        self.timer.timeout.connect(self.connect_to_signal)
        self.timer.timeout.connect(self.update_circular_graph)                      #-------------------------------------------
        self.timer.start(self.timer_interval)  # Start timer with calculated interval
        # self.timer.start(1000)  # Set interval to 1000 ms (1 second), adjust as needed

        self.signal_data = {
            'Graph 1': None,
            'Graph 2': None,
            'Glued Signals': None,
            'Graph 3': None
        }
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
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 1, 0)  # Scroll for graph 1
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 2, 1)  # Scroll for graph 1

        graphLayout.addWidget(self.graph2, 1, 3)
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 1, 2)  # Scroll for graph 2
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 2, 3)  # Scroll for graph 2

        graphLayout.addWidget(gluedLabel, 3, 1)
        graphLayout.addWidget(self.gluedGraph, 4, 1)
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 4, 0)  # Scroll for glued signals
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 5, 1)  # Scroll for glued signals

        graphLayout.addWidget(graph3Label, 3, 3)
        graphLayout.addWidget(self.graph3, 4, 3)
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 4, 2)  # Scroll for graph 3
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 5, 3)  # Scroll for graph 3

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
        playPauseBtn = QPushButton('Play / Pause')
        rewindBtn = QPushButton('Rewind')
        zoomInBtn = QPushButton('Zoom In')

        bottomLayout.addWidget(zoomOutBtn)
        bottomLayout.addWidget(linkBtn)
        bottomLayout.addWidget(showHideBtn)
        bottomLayout.addWidget(playPauseBtn)
        bottomLayout.addWidget(rewindBtn)
        bottomLayout.addWidget(zoomInBtn)

        moveBtn = QPushButton('Move')
        colorBtn = QPushButton('Color')
        snapshotBtn = QPushButton('Snapshot')
        exportReportBtn = QPushButton('Export Report')

        bottomLayout.addWidget(moveBtn)
        bottomLayout.addWidget(colorBtn)
        bottomLayout.addWidget(snapshotBtn)
        bottomLayout.addWidget(exportReportBtn)

        mainLayout.addLayout(bottomLayout)

        # Connect buttons
        openBtn.clicked.connect(self.openFile)
        connectBtn.clicked.connect(self.connect_to_signal)  # Connect the connect button to the method
        colorBtn.clicked.connect(self.openColorDialog)
        snapshotBtn.clicked.connect(self.take_snapshot)
        exportReportBtn.clicked.connect(self.export_report)

        # Set main layout
        self.setLayout(mainLayout)
        self.setWindowTitle('Signal Viewer')
        self.show()

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
                            else:
                                # Append new data to existing data
                                existing_time, existing_signal = self.signal_data[selected_graph]
                                self.signal_data[selected_graph] = (np.concatenate((existing_time, time)),
                                                                    np.concatenate((existing_signal, selected_signal)))

                        # Clear previously plotted data for the selected graph
                        self.plotted_data[selected_graph] = ([], [])
                        # Update the graph with the newly loaded signal
                        self.update_graphs()

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
                self.update_graphs()  # Update graphs with new data

            else:
                print("Error: 'price' key not found in the response.")

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to signal: {e}")
        except ValueError as e:
            print(f"Error parsing JSON: {e}")

    def update_graphs(self):
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


    def update_circular_graph(self):
        if self.graph3.data is not None:
            self.graph3.update_circular_graph()  # Update graph for the current index
        else:
            self.stop_cine_mode()  # Stop if there is no data
    def openColorDialog(self):
        color = QColorDialog.getColor()

    def start_cine_mode(self):
        if self.data is not None:
            self.timer.start(100)  # Update every 100 ms

    def stop_cine_mode(self):
        self.timer.stop()

    def rewind(self):
        self.graphWidget.angle = 0  # Reset to the beginning
        self.graphWidget.update()


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
        report_filename = f"reports/report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"

        # Create a canvas object
        c = canvas.Canvas(report_filename, pagesize=letter)
        width, height = letter

        # Add images and text
        c.drawImage("images/uni-logo.png", width - 150, height - 50, width=100, height=50)
        c.drawImage("images/sbme-logo.jpg", 50, height - 50, width=100, height=50)
        
        # Title in the middle
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2, height - 70, "Signal Report")

        # Take snapshot of "Glued Signals" graph
        snapshot_path = f"snapshots/snapshot_{now.strftime('%Y%m%d_%H%M%S')}.png"
        exporter = pg.exporters.ImageExporter(self.gluedGraph.plotItem)  # Adjust this to your actual reference
        exporter.export(snapshot_path)

        # Add the snapshot to the PDF
        c.drawImage(snapshot_path, 50, height - 200, width=500, height=200)  # Adjust positioning and size

        # Finalize the PDF
        c.showPage()
        c.save()

        # Show success message
        QMessageBox.information(self, "Export Report", f"Report saved as {report_filename}.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())