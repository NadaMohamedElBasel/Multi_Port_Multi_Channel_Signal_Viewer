import numpy as np
import pandas as pd
import requests
import time

from PyQt5.QtCore import QRect


class LogicHandler:
    def __init__(self):
        self.selection_mode_enabled = False
        self.selected_signals = [[], []]  # Two arrays to store the selected signal coordinates
        self.selected_rectangles = [QRect() for _ in range(2)]
        self.current_rectangle_index = 0
        self.signal_data = {
            'Graph 1': None,
            'Graph 2': None,
            'Glued Signals': None,
            'Graph 3': None
        }
        self.plotted_data = {
            'Graph 1': ([], []),
            'Graph 2': ([], []),
            'Glued Signals': ([], []),
            'Graph 3': ([], [])
        }
        self.linked=False
        self.time_index = {key: 0 for key in self.signal_data.keys()}
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
        
        self.sampling_rate = 50
        self.timer_interval = int(1000 / self.sampling_rate)  # Convert to integer

    def toggle_selection_mode(self):
        """Toggle the selection mode for rectangles."""
        self.current_rectangle_index = 0
        self.selected_rectangles = [QRect() for _ in range(2)]

    def is_plot_concatenation_enabled(self):
        """Check if selection mode is enabled."""
        return self.current_rectangle_index >= 2

    def load_circular_data(self, file_name):
        """Read circular data from a file."""
        # Load the data from the file
        return np.loadtxt(file_name)

    def load_signal_data(self, selected_graph_name, file_name):
        """Load ECG data from a CSV file."""
        data = pd.read_csv(file_name, header=None)
        print(data)
        time = data[0].to_numpy()
        amplitude = data[1].to_numpy()
        print(time, amplitude)
        self.reset_signal_data(selected_graph_name)
        self.update_signal_data(selected_graph_name, time, amplitude)

    def update_signal_data(self, selected_graph_name, time, amplitude):
        if selected_graph_name in self.signal_data:
            # Check if the current signal is already loaded; If not, initialize it
            self.signal_data[selected_graph_name] = (time, amplitude)
            self.time_index[selected_graph_name] = 0
        # Clear previously plotted data for the selected graph
        self.plotted_data[selected_graph_name] = ([], [])
    
    def is_graph_playing(self, graph_name, is_playing):
        self.is_playing_graph[graph_name] = is_playing

    def set_time_index(self, graph_name, time_index):
        self.time_index[graph_name] = time_index

    def update_plotted_data(self, graph_name, time, signal):
        """Update the plotted data for the given graph."""
        self.plotted_data[graph_name][0].append(time)
        self.plotted_data[graph_name][1].append(signal)

    def get_real_time_data(self, graph_name):
        """Get real-time ECG data for the given graph."""
        time, signal = self.signal_data[graph_name]
        min_signal = min(signal)
        max_signal = max(signal)
        padding = 0.1
        min_y = min_signal - padding
        max_y = max_signal + padding
        return time, signal, min_y, max_y

    def add_rectangle(self, start_point):
        """Initialize a rectangle starting from the given point."""
        if self.current_rectangle_index < 2:
            self.selected_rectangles[self.current_rectangle_index] = QRect(
                start_point, start_point)
            return True
        return False

    def update_rectangle(self, end_point):
        """Update the current rectangle with the new endpoint."""
        if self.current_rectangle_index < 2:
            self.selected_rectangles[self.current_rectangle_index] = QRect(
                self.selected_rectangles[self.current_rectangle_index].topLeft(), end_point).normalized()
            return True
        return False

    def finalize_rectangle(self, graph):
        """Finalize the current rectangle selection."""
        if self.current_rectangle_index < 2:
            self.extract_signal_in_rectangle(graph)
            self.current_rectangle_index += 1
            # Return selected rectangles
            return self.selected_rectangles[:self.current_rectangle_index]
        return None

    def reset(self):
        """Reset rectangle selections for new drawings."""
        self.selected_rectangles = [QRect() for _ in range(2)]
        self.current_rectangle_index = 0

    def reset_signal_data(self, selected_graph_name):
        """Reset the signal data for the selected graph."""
        self.signal_data[selected_graph_name] = ([], [])
        self.plotted_data[selected_graph_name] = ([], [])
        self.time_index[selected_graph_name] = 0

    def connect_to_signal(self, selected_graph, url, update_method):
        """Connect the selected graph to the signal."""
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
                if self.signal_data[selected_graph] is None:
                    self.signal_data[selected_graph] = ([], [])  # Initialize if None

                # Append the new data to your signal data
                self.signal_data[selected_graph][0].append(current_time)  # Time data
                self.signal_data[selected_graph][1].append(price)  # Price data

                print(f"Current Price: {price}")  # For debugging

                # Update the graphs after adding new data
                update_method()  # Update graphs with new data

            else:
                print("Error: 'price' key not found in the response.")

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to signal: {e}")
        except ValueError as e:
            print(f"Error parsing JSON: {e}")

    def glue_signals(self, gap_overlap, interpolation_order):
        signal1 = self.selected_signals[0]
        signal2 = self.selected_signals[1]
        if not signal1 or not signal2:
            return []

        # User-defined interpolation order

        # Threshold for y-coordinate proximity
        threshold = 20  # Adjust as needed

        # Step 1: Store the last point of signal1 and first point of signal2
        last_point_signal1 = signal1[-1]
        first_point_signal2 = signal2[0]

        # Step 2: Create the glued signal, start with signal1
        glued_signal = signal1.copy()

        # Step 3: Add gap/overlap adjustment (positive gap or negative overlap)
        shift_x = last_point_signal1[0] + gap_overlap

        # Step 4: Interpolate between the last point of signal1 and first point of signal2
        if interpolation_order > 0 and abs(last_point_signal1[1] - first_point_signal2[1]) > threshold:
            x_interp = np.linspace(last_point_signal1[0], shift_x, num=interpolation_order)
            y_interp = np.linspace(last_point_signal1[1], first_point_signal2[1], num=interpolation_order)
            for i in range(len(x_interp)):
                glued_signal.append((x_interp[i], y_interp[i]))

        # Step 5: Shift the second signal's x-values by the gap/overlap and append it to the glued signal
        for x, y in signal2:
            glued_signal.append((x - first_point_signal2[0] + shift_x, y))
        print(glued_signal, signal1, signal2)
        return glued_signal

    def extract_signal_in_rectangle(self, graph):
        # Get the coordinates of the selection rectangle
        x_min = int(self.selected_rectangles[self.current_rectangle_index].left())
        x_max = int(self.selected_rectangles[self.current_rectangle_index].right())
        y_min = int(self.selected_rectangles[self.current_rectangle_index].top())
        y_max = int(self.selected_rectangles[self.current_rectangle_index].bottom())
        # Iterate through the signal data and collect points inside the selection rectangle
        signal_data = self.signal_data[graph.name]
        print("FETCHED DATA:", signal_data)
        x_list, y_list = signal_data
        for i, _ in enumerate(x_list):
            x = x_list[i]
            y = y_list[i]
            acc_x, acc_y = self.convert_coordinates(x, y, graph)
            if x_min <= acc_x <= x_max and y_min <= acc_y <= y_max:
                self.selected_signals[self.current_rectangle_index].append((x, y))
        
    def convert_coordinates(self, graph_x, graph_y, graph):
        # Get the view range (data limits) of the graph
        x_range = graph.viewRange()[0]  # x limits (min, max)
        y_range = graph.viewRange()[1]  # y limits (min, max)

        # Calculate pixel coordinates based on graph limits
        graph_width = graph.width()
        graph_height = graph.height()

        # Convert graph coordinates to pixel coordinates
        pixel_x = (graph_x - x_range[0]) / (x_range[1] - x_range[0]) * graph_width
        pixel_y = graph_height - (graph_y - y_range[0]) / (y_range[1] - y_range[0]) * graph_height
        return pixel_x, pixel_y
