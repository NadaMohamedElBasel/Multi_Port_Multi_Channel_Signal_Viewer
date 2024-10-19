from PyQt5.QtCore import QTimer


class CustomTimer:
    def __init__(self, parent, mediator, interval):
        """
        Custom reusable timer class.

        :param callback: Function to be called on timeout.
        :param interval: Timer interval in milliseconds.
        :param parent: Parent widget or object (optional).
        """
        self.timer = QTimer(parent)
        self.mediator = mediator
        self.timer.start(interval)  # Start the timer with the given interval

    def stop(self):
        """Stop the timer."""
        self.timer.stop()

    def start(self, interval=None):
        """Restart the timer with an optional new interval."""
        if interval:
            self.timer.setInterval(interval)
        self.timer.start()
  
    def connect(self, callback):
        """Connect a callback function to the timer."""
        self.timer.timeout.connect(callback)