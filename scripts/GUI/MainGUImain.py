"""
The purpose of this script is to initiate the main GUI

***
built as part of the Russell Ray Lab Breathing And Physiology Analysis Pipeline
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

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDir
import sys
import os
import threading
import logging
import MainGui
from multiprocessing import freeze_support

def main():
    root = os.path.dirname(os.path.abspath(__file__))        
    QDir.addSearchPath('resources', root)
    app = QApplication(sys.argv)
    window = MainGui.Plethysmography()
    print('GUI thread id', threading.get_ident()) 
    print("GUI process id", os.getpid())
    window.show()
    app.exec_()

    logging.basicConfig(
        level = logging.INFO,
        format = 'PID %(process)5s %(name)18s: %(message)s',
        stream = sys.stderr
    )

if __name__ == "__main__": 
    freeze_support()
    main()
