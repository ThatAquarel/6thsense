import multiprocessing

from abc import ABC, abstractmethod


class Process(ABC):
    def __init__(self):
        self.input_queue, self.output_queue = (
            multiprocessing.Queue(),
            multiprocessing.Queue(),
        )
        self.parent_connection, self.child_connection = multiprocessing.Pipe()

        self.process = multiprocessing.Process(
            target=self._get_process_function(),
            args=(self.child_connection, self.input_queue, self.output_queue),
        )
        self.process.start()

    @abstractmethod
    def _get_process_function(self):
        raise NotImplementedError()

    @abstractmethod
    def call(self, *args, **kwargs):
        raise NotImplementedError()

    latest_data = None

    def latest(self):
        if not self.output_queue.empty():
            self.latest_data = self.output_queue.get()
        return self.latest_data

    def stop(self):
        self.process.terminate()
