import sys
from PyQt5.QtCore import QThread, pyqtSignal

from tools.columns_and_values_tools import columns_and_values_from_jsons

class ColValImportThread(QThread):
    progress = pyqtSignal(str)

    def __init__(self, json_paths):
        super().__init__()
        self.json_paths = json_paths
        self._quit = False
        self.output = None

    def run(self):
        """
        Loop through yielded progress messages
        Catch return value as StopIteration value
        Break early if `quit()` has been called
        """

        # Get an iterator from the function call
        it = columns_and_values_from_jsons(self.json_paths)

        while True:
            # Exit if quit flag is set
            if self._quit:
                self.progress.emit("Thread terminated")
                break

            try:
                # Process code up to next yielded message
                progress_message = next(it)

                # Emit the message
                self.progress.emit(progress_message)

            # Get return value
            except StopIteration as e:
                self.output = e.value
                break

    def quit(self):
        """
        Set `_quit` boolean to true, for exit on iterator loop
        """
        self._quit = True