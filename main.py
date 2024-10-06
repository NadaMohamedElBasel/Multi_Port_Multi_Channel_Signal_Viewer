import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QRadioButton, 
                             QVBoxLayout, QHBoxLayout, QSlider, QLineEdit, 
                             QScrollBar, QFrame, QGridLayout, QComboBox, QFileDialog, QColorDialog)
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Layout for the entire window
        mainLayout = QVBoxLayout()

        # Top Row: Open, Connect, and Text Field for signal source
        topLayout = QHBoxLayout()
        openBtn = QPushButton('Open')
        connectBtn = QPushButton('Connect')
        signalInput = QLineEdit('Enter address of a realtime signal source')

        # the combo box is used to choose between plots on the same graph which eas selected by the the radio button
        plotComboBox = QComboBox()
        plotComboBox.addItem("Select Plot")  # Default text

        topLayout.addWidget(openBtn)
        topLayout.addWidget(connectBtn)
        topLayout.addWidget(signalInput)
        topLayout.addWidget(plotComboBox)  

        
        mainLayout.addLayout(topLayout)

        
        graphLayout = QGridLayout()

        # Radio Buttons to choose between graphs which one to controll if they weren't linked 
        graph1Radio = QRadioButton()
        graph2Radio = QRadioButton()
        gluedRadio = QRadioButton()
        graph3Radio = QRadioButton()

        # Editable labels (text fields) for renaming graphs
        graph1Label = QLineEdit('Graph 1')
        graph2Label = QLineEdit('Graph 2')
        gluedLabel = QLineEdit('Glued Signals')
        graph3Label = QLineEdit('Graph 3')

        # Placeholder for charts using PyQtGraph with grids and numbered axes
        graph1 = pg.PlotWidget()
        graph1.showGrid(x=True, y=True)
        #graph1.setTitle("Graph 1")
        graph1.setLimits(xMin=0)  # Limit x-axis minimum

        graph2 = pg.PlotWidget()
        graph2.showGrid(x=True, y=True)
        #graph2.setTitle("Graph 2")
        graph2.setLimits(xMin=0)  # Limit x-axis minimum

        gluedGraph = pg.PlotWidget()
        gluedGraph.showGrid(x=True, y=True)
        #gluedGraph.setTitle("Glued Signals")
        gluedGraph.setLimits(xMin=0)  # Limit x-axis minimum

        graph3 = pg.PlotWidget()
        graph3.showGrid(x=True, y=True)
        #graph3.setTitle("Graph 3")
        graph3.setLimits(xMin=0)  # Limit x-axis minimum

        # Set size of the graphs to fill most of the screen relatively equally
        graph1.setFixedSize(400, 300)
        graph2.setFixedSize(400, 300)
        gluedGraph.setFixedSize(400, 300)
        graph3.setFixedSize(150, 150)

        
        graphLayout.addWidget(graph1Radio, 0, 0)
        graphLayout.addWidget(graph1Label, 0, 1)
        graphLayout.addWidget(graph2Radio, 0, 2)
        graphLayout.addWidget(graph2Label, 0, 3)

        # Adjusting spacing 
        graphLayout.setRowMinimumHeight(0, 30)  

        # Adding the graphs and scroll bars
        graphLayout.addWidget(graph1, 1, 1)
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 1, 0)  # Left vertical scroll for graph 1
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 2, 1)  # Horizontal scroll for graph 1

        graphLayout.addWidget(graph2, 1, 3)
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 1, 2)  # Left vertical scroll for graph 2
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 2, 3)  # Horizontal scroll for graph 2

        # Adjusting the space 
        graphLayout.addWidget(gluedRadio, 3, 0)
        graphLayout.addWidget(gluedLabel, 3, 1)
        graphLayout.addWidget(gluedGraph, 4, 1)
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 4, 0)  # Left vertical scroll for glued signals
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 5, 1)  # Horizontal scroll for glued signals

        # adjusting spaces
        graphLayout.setRowMinimumHeight(3, 30)  
        graphLayout.setRowMinimumHeight(4, 30)  

        # Adding graph 3
        graphLayout.addWidget(graph3Radio, 3, 2)
        graphLayout.addWidget(graph3Label, 3, 3)
        graphLayout.addWidget(graph3, 4, 3)
        graphLayout.addWidget(QScrollBar(Qt.Vertical), 4, 2)  # Left vertical scroll for graph 3
        graphLayout.addWidget(QScrollBar(Qt.Horizontal), 5, 3)  # Horizontal scroll for graph 3

        
        mainLayout.addLayout(graphLayout)

        # Cine Speed Slider
        cineSpeedLayout = QHBoxLayout()
        cineSpeedLabel = QLabel('Cine Speed:')
        cineSpeedSlider = QSlider(Qt.Horizontal)  # Horizontal orientation
        cineSpeedLayout.addWidget(cineSpeedLabel)
        cineSpeedLayout.addWidget(cineSpeedSlider)

        mainLayout.addLayout(cineSpeedLayout)

        # Bottom Controls: Zoom Out, Link, Show/Hide, Play/Pause, Rewind, Zoom In
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

        # Adding the bottom control buttons move , color , snapshot , export report 
        moveBtn = QPushButton('Move')
        colorBtn = QPushButton('Color')
        snapshotBtn = QPushButton('Snapshot')
        exportReportBtn = QPushButton('Export Report')

        
        bottomLayout.addWidget(moveBtn)
        bottomLayout.addWidget(colorBtn)
        bottomLayout.addWidget(snapshotBtn)
        bottomLayout.addWidget(exportReportBtn)

        mainLayout.addLayout(bottomLayout)

        # Connect the Open button to a file dialog
        openBtn.clicked.connect(self.openFile)
        
        # Connect the Export Report button to the export function
        exportReportBtn.clicked.connect(self.exportReport)

        # Connect the Color button to the color selection function
        colorBtn.clicked.connect(self.openColorDialog)

        # Set main layout
        self.setLayout(mainLayout)
        self.setWindowTitle('Signal Viewer')
        self.show()

    def openFile(self):
        # Open a file dialog to browse the pc to select a file
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if file_name:
            print(f"Selected file: {file_name}")  # For demonstration, print the selected file

    def openColorDialog(self):
        color = QColorDialog.getColor()  # Open color dialog

    def exportReport(self):
        # Create a PDF file
        pdf_file_name, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if pdf_file_name:
            pdf = canvas.Canvas(pdf_file_name, pagesize=letter)
            width, height = letter  # Page dimensions

            
            images = [ ]  # to be replaced with actual image paths
            page_count = len(images)

            for i in range(page_count):
                
                img_path = images[i]
                pdf.drawImage(img_path, 50, height - 200, width=5*inch, height=4*inch)  # Image position

                # Create a table next to the image
                table_x = 50 + 5 * inch + 20  # Adjust the x position for the table
                table_y = height - 200

                # Draw the table header
                pdf.setFillColor(colors.black)
                pdf.drawString(table_x, table_y + 20, "Min")
                pdf.drawString(table_x + 100, table_y + 20, "Max")
                pdf.drawString(table_x + 200, table_y + 20, "Mean")
                pdf.drawString(table_x + 300, table_y + 20, "Std. Dev.")
                pdf.drawString(table_x + 400, table_y + 20, "Duration")
                pdf.drawString(table_x + 500, table_y + 20, "Sampling Rate")

                # Draw empty cells for data entry
                for j in range(1, 6):  # Create 5 empty rows
                    pdf.drawString(table_x, table_y - j * 20, "")
                    pdf.drawString(table_x + 100, table_y - j * 20, "")
                    pdf.drawString(table_x + 200, table_y - j * 20, "")
                    pdf.drawString(table_x + 300, table_y - j * 20, "")
                    pdf.drawString(table_x + 400, table_y - j * 20, "")
                    pdf.drawString(table_x + 500, table_y - j * 20, "")

                # Move to the next page if not the last image
                if i < page_count - 1:
                    pdf.showPage()

            # Save the PDF
            pdf.save()
            print(f"Report saved as: {pdf_file_name}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())





