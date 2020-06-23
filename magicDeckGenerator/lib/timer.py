# timer.py

import time
from .log import Log

log = Log("Timer", 0).log

class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""

class Timer:
    name = None
    text: str = "Elapsed time: {:0.4f} seconds"
    _start_time = None

    def __init__(self, name):
        self.name = name

    def start(self) -> None:
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        # Calculate elapsed time
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None

        # Report elapsed time
        log(0, f"{self.name}: {elapsed_time}")
        return elapsed_time

    def __enter__(self):
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(self, *exc_info):
        """Stop the context manager timer"""
        self.stop()