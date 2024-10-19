import os
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QRect
import pyqtgraph as pg
from pyqtgraph import exporters
from reportlab.lib import colors
from logic_layer.logic_handler import LogicHandler

class Mediator:
    def __init__(self, main_window, logic: LogicHandler):
        self.logic = logic  # Store a reference to the logic handler
        self.main_window = main_window  # Store a reference to the main window

    def notify_start_rectangle(self, start_point):
        """Handle starting rectangle selection."""
        return self.logic.add_rectangle(start_point)

    def notify_update_rectangle(self, end_point):
        """Handle updating the rectangle size."""
        return self.logic.update_rectangle(end_point)

    def notify_finalize_rectangle(self, graph):
        """Finalize rectangle selection."""
        return self.logic.finalize_rectangle(graph)

    def update_main_window(self, selected_rectangles):
        """Notify the main window about the selected rectangles."""
        self.main_window.update_plot_selection(selected_rectangles)
        if len(selected_rectangles) == 2:
            self.main_window.selection_button.setEnabled(False)  # Disable button to prevent further selections
            self.main_window.plot_button.setEnabled(True)  # Enable plot button after selection


    def open_circular_plot_file(self, selected_graph):
        """Open a circular plot file."""
        file_name, _ = QFileDialog.getOpenFileName(self.main_window, "Open File", "", "Text Files (*.txt);;All Files (*)")
        if not file_name:
            return
        selected_graph.data = self.logic.load_circular_data(file_name)

    def toggle_play_pause(self, selected_graph):
        is_playing_graph = self.logic.is_playing_graph
        playPauseBtn = self.main_window.playPauseBtn
        if selected_graph in is_playing_graph:
            is_playing_graph[selected_graph] = not is_playing_graph[selected_graph]

            if is_playing_graph[selected_graph]:
                # Start the timer for the selected graph
                self.main_window.graphs_timer.start(int(self.logic.timer_interval))
                playPauseBtn.setText('Pause')
            else:
                # Stop the timer for the selected graph
                self.main_window.graphs_timer.stop()
                playPauseBtn.setText('Play')

    def handle_linked_graphs(self, selected_graph):
        is_playing_graph = self.logic.is_playing_graph
        if self.logic.linked and (selected_graph == "Graph 1" or selected_graph == "Graph 2"):
            graph1_playing = is_playing_graph["Graph 1"]
            graph2_playing = is_playing_graph["Graph 2"]

            # If either graph is playing, stop both
            if graph1_playing or graph2_playing:
                self.logic.is_graph_playing("Graph 1", False)
                self.logic.is_graph_playing("Graph 2", False)
                self.main_window.graphs_timer.stop()
                self.playPauseBtn.setText('Play')
            else:
                self.logic.is_graph_playing("Graph 1", True)
                self.logic.is_graph_playing("Graph 2", True)
                self.main_window.graphs_timer.start(int(self.logic.timer_interval))
                self.playPauseBtn.setText('Pause')

    def open_plot_file(self, selected_graph):
        # Load the data from the file
        file_name, _ = QFileDialog.getOpenFileName(self.main_window, "Open File", "", "CSV Files (*.csv);;All Files (*)")
        if not file_name:
            return
        selected_graph_name = selected_graph.name
        self.logic.load_signal_data(selected_graph_name, file_name)
        self.logic.is_graph_playing(selected_graph_name, True)
        print(self.logic.signal_data)
        self.plot_signal(selected_graph)
        self.main_window.playPauseBtn.setText('Pause') 
        self.main_window.toggle_play_pause()

    def update_graphs(self):
        """Update all graphs with their respective ECG data."""
        signal_data = self.logic.signal_data
        time_index = self.logic.time_index
        is_playing_graph = self.logic.is_playing_graph
        for graph in self.main_window.graphs:
            graph_name = graph.name
            if graph_name not in signal_data.keys():
                continue
            if signal_data[graph_name] is not None and is_playing_graph[graph_name]:
                time, signal = signal_data[graph_name]  # Unpack the tuple
                current_index = time_index[graph_name]
          
                if current_index < len(signal):
                    self.logic.update_plotted_data(graph_name, time[current_index], signal[current_index])

                # Plot the full line so far
                self.plot_signal(graph)
                self.logic.set_time_index(graph_name, time_index[graph_name] + 1)


    def update_real_time_graphs(self):
        """Update all graphs with their respective ECG data."""
        graphs = self.main_window.graphs
        for graph in graphs:
            graph_name = graph.name
            if self.logic.signal_data[graph_name] is not None:
                time, signal = self.logic.signal_data[graph_name]  # Unpack the tuple
                graph.plot_widget.clear()
                # Set y-axis limits based on signal range
                min_signal = min(signal)  # Find the minimum value in the signal
                max_signal = max(signal)  # Find the maximum value in the signal
                
                padding = 0.1  # Adjust this value as needed for better visibility
                graph.plot_widget.setYRange(min_signal - padding, max_signal + padding)  # Set y-axis limits
                
                graph.plot_widget.plot(time, signal, pen='r')  # Use a white pen for better visibility

    
    def plot_signal(self, graph):
        """Plot the signal on the appropriate graph."""
        graph_name = graph.name
        self.logic.time_index[graph_name] += 1
        plotted_data = self.logic.plotted_data
        graph.plot_widget.clear()
        if self.logic.hidden_signals[graph_name]:
            return

        color = self.logic.graph_colors[graph_name]  # Get the current color for the graph
        graph.plot_widget.plot(plotted_data[graph_name][0], plotted_data[graph_name][1], pen=color)

    def move_signal(self, source, destination): 
        if source != destination and self.logic.is_playing_graph[source.name]: 
            signal_data = self.logic.signal_data[source.name]  # Get the current signal data for the source
            if signal_data is not None:
                signal_data[destination.name] = signal_data
                signal_data[source.name] = None  # Clear source graph data
                self.clear_plot(source)
                self.refresh_plot(destination)
                self.logic.is_playing_graph[destination.name] = True  # Start playing on the destination graph
                self.logic.is_playing_graph[source.name] = False  # Stop playing on the source graph
                self.plot_signal(destination)

    def refresh_plot(self, graph):
        """Refresh the plot by replotting data for the given graph."""
        plotted_data = self.logic.plotted_data
        graph.plot_widget.plot(plotted_data[graph.name][0], plotted_data[graph.name][1], clear=True)

    def clear_plot(self, graph):
        """Clear the selected graph."""
        graph.plot_widget.plot([], [], clear=True)

    def take_snapshot(self, plot_item):
        # Specify the directory where the snapshots will be saved
        snapshot_dir = "snapshots"
        os.makedirs(snapshot_dir, exist_ok=True)  # Create the directory if it doesn't exist
        # Define the filename with date and time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = os.path.join(snapshot_dir, f"snapshot_{timestamp}.png")
        # Access the "Glued Signals" graph
        glued_signals_plot = plot_item  # Adjust this if necessary to get the correct graph
        # Take the snapshot
        exporter = pg.exporters.ImageExporter(glued_signals_plot)
        exporter.export(snapshot_filename)
        return snapshot_filename

    def export_report(self, plot_item):
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
        exporter = pg.exporters.ImageExporter(plot_item)  # Adjust this to your actual reference
        exporter.export(snapshot_path)
        # Add the snapshot to the PDF
        snapshot_y_position = height - logo_height - 100  # Adjust this to place it below the title
        c.drawImage(snapshot_path, 50, snapshot_y_position - 200, width=500, height=200)  # Adjust positioning and size
        # Gather data from the gluedGraph (assuming it’s a PyQtGraph plot with data)
        # Extract the data from the graph for statistics calculation
        plot_data = plot_item.listDataItems()[0].getData()  # Assuming the first data item
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
        return report_filename

    def connect_to_signal(self, signal_name, url):
        self.logic.connect_to_signal(signal_name, url, self.update_real_time_graphs)
        
    def toggle_subplot_selection_mode(self):
        self.logic.selection_mode_enabled = not self.logic.selection_mode_enabled
        self.logic.current_rectangle_index = 0  # Reset to first rectangle
        self.logic.selected_rectangles = [QRect(), QRect()]  # Reset rectangles
        self.logic.selected_signals = [[], []]  # Reset selected signals
        return self.logic.selection_mode_enabled