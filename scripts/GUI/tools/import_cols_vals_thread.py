"""
import_cols_vals_thread
created as a component of Breathe Easy

***
Breathe Easy - an automated waveform analysis pipeline
Copyright (C) 2022  
Savannah Lusk, Andersen Chang, 
Avery Twitchell-Heyne, Shaun Fattig, 
Christopher Scott Ward, Russell Ray.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
***
"""

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