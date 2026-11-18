import threading

class PeriodicTimer:
    """Runs given callback function in loop of interval seconds.
    Stops when stop method is called.
    """
    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback
        self.stop_event = threading.Event()

    def start(self):
        while not self.stop_event.is_set():
            self.callback()
            self.stop_event.wait(self.interval)

    def stop(self):
        self.stop_event.set()
