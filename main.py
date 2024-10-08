import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton, 
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit, 
                             QScrollBar, QGridLayout, QComboBox, QFileDialog, QColorDialog)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
         
    # Define sampling rate 
        self.sampling_rate = 50
        self.timer_interval = int(1000 / self.sampling_rate)  # Convert to integer

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.timer.start(self.timer_interval)  # Start timer with calculated interval

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
        signalInput = QLineEdit('Enter address of a realtime signal source')
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
        topLayout.addWidget(signalInput)
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

        self.graph3 = pg.PlotWidget()
        self.graph3.showGrid(x=True, y=True)
        self.graph3.setLimits(xMin=0)

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
        cineSpeedSlider = QSlider(Qt.Horizontal)
        cineSpeedLayout.addWidget(cineSpeedLabel)
        cineSpeedLayout.addWidget(cineSpeedSlider)

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
        exportReportBtn.clicked.connect(self.exportReport)
        colorBtn.clicked.connect(self.openColorDialog)

        # Set main layout
        self.setLayout(mainLayout)
        self.setWindowTitle('Signal Viewer')
        self.show()


    def openFile(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;All Files (*)")
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
        """Load ECG data from a CSV file."""
        data = pd.read_csv(file_name, header=None)
        time = data[0].to_numpy()
        amplitude = data[1].to_numpy()
        return time, amplitude

    def update_graphs(self):
      """Update all graphs with their respective ECG data."""
      for graph_name in self.signal_data.keys():
        if self.signal_data[graph_name] is not None:
            time, signal = self.signal_data[graph_name]  # Unpack the tuple
            current_index = self.time_index[graph_name]

            if current_index < len(signal):
                # Append the new data point for plotting
                self.plotted_data[graph_name][0].append(time[current_index])
                self.plotted_data[graph_name][1].append(signal[current_index])

                # Plot the full line so far
                self.plot_signal(graph_name)                   
                self.time_index[graph_name] += 1  # Increment time index
            
    def plot_signal(self, graph_name):
        """Plot the signal on the appropriate graph."""
        if graph_name == "Graph 1":
            self.graph1.clear()
            self.graph1.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen='r')
        elif graph_name == "Graph 2":
            self.graph2.clear()
            self.graph2.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen='g')
        elif graph_name == "Glued Signals":
            self.gluedGraph.clear()
            self.gluedGraph.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen='b')
        elif graph_name == "Graph 3":
            self.graph3.clear()
            self.graph3.plot(self.plotted_data[graph_name][0], self.plotted_data[graph_name][1], pen='y')
        
    def openColorDialog(self):
        color = QColorDialog.getColor()

    def exportReport(self):
        pdf_file_name, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if pdf_file_name:
            pdf = canvas.Canvas(pdf_file_name, pagesize=letter)
            width, height = letter

            images = []  # Add image paths if needed
            page_count = len(images)

            for i in range(page_count):
                img_path = images[i]
                pdf.drawImage(img_path, 50, height - 200, width=5*inch, height=4*inch)

                # Draw a table next to the image
                table_x = 50 + 5 * inch + 20
                table_y = height - 200

                # Draw table header
                pdf.setFillColor(colors.black)
                pdf.drawString(table_x, table_y + 20, "Min")
                pdf.drawString(table_x + 100, table_y + 20, "Max")
                pdf.drawString(table_x + 200, table_y + 20, "Mean")
                pdf.drawString(table_x + 300, table_y + 20, "Std. Dev.")
                pdf.drawString(table_x + 400, table_y + 20, "Duration")
                pdf.drawString(table_x + 500, table_y + 20, "Sampling Rate")

                # Draw empty cells for data entry
                for j in range(1, 6):
                    pdf.drawString(table_x, table_y - j * 20, "")
                    pdf.drawString(table_x + 100, table_y - j * 20, "")
                    pdf.drawString(table_x + 200, table_y - j * 20, "")
                    pdf.drawString(table_x + 300, table_y - j * 20, "")
                    pdf.drawString(table_x + 400, table_y - j * 20, "")
                    pdf.drawString(table_x + 500, table_y - j * 20, "")

                if i < page_count - 1:
                    pdf.showPage()

            pdf.save()
            print(f"Report saved as: {pdf_file_name}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())