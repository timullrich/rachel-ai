from threading import Thread
from typing import Any, Iterator, List


class StreamSplitter:
    """
        A class to split a stream of data into chunks that can be consumed by multiple consumers.

        This class reads an iterator-based data stream (e.g., API responses that arrive in real-time)
        and stores the data chunks internally. It allows multiple consumers to access the same stream
        of data without consuming it directly from the source, ensuring that all consumers have access
        to the entire stream.

        Attributes:
            stream (Iterator[Any]): The input data stream that will be processed.
            chunks (List[Any]): A list to store the chunks of data as they are read from the stream.
            finished (bool): A flag indicating whether the reading of the stream has finished.

        Methods:
            start():
                Starts reading the stream in a separate thread and stores each chunk in the chunks list.
            get() -> Iterator[Any]:
                Yields chunks of data from the list as they become available, allowing multiple
                consumers to access the same data in real-time.
    """
    def __init__(self, stream: Iterator[Any]):
        self.stream = stream
        self.chunks: List[Any] = []
        self.finished = False

    def start(self):
        """Starts reading the stream and feeding it into the list."""
        def _read_stream():
            for chunk in self.stream:
                self.chunks.append(chunk)
            self.finished = True

        Thread(target=_read_stream, daemon=True).start()

    def get(self) -> Iterator[Any]:
        """Yields items from the chunks list as they are read from the stream."""
        index = 0
        while not self.finished or index < len(self.chunks):
            if index < len(self.chunks):
                yield self.chunks[index]
                index += 1
            else:
                continue  # Wait until more chunks are available or finished

