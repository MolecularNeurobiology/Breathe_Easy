#%%
#region Libraries
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
import threading
import logging
import MainGui
from multiprocessing import freeze_support

#endregion

#region Main
def main():
    root = os.path.dirname(os.path.abspath(__file__))        
    QDir.addSearchPath('resources', root)
    app = QApplication(sys.argv)
    window = MainGui.Plethysmography()
    print(window.signals)
    print('GUI thread id',threading.get_ident()) 
    print("GUI process id",os.getpid())
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
#endregion
# %%
