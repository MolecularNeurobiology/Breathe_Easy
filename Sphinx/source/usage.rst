Installation
================
Packaged Program Install
---------------------------
#. For our most recently released version, visit our `GitHub release page <https://www.GitHub.com/MolecularNeurobiology/BASSPRO-STAGG/releases>`_.
#. Select our most recent release.
#. In the asset section, download the packaged zip file. 
#. Once the file is downloaded, unzip the file.

Source Install
-------------------
Install Python3
^^^^^^^^^^^^^^^^^^^^
`Install python here <https://www.python.org/downloads/>`_.

Install Python Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Activate Python virtual environment to help manage package installation.

.. code-block::

        #Posix
        python3 -m venv <venv>
        source <venv>/bin/activate
        
        #Windows
        python3 -m venv <venv>
        <venv>/Scripts/activate.bat
        
2. Install dependencies; a list of all dependencies can also be found below.

.. code-block::

        pip install -r requirements.txt
   
.. list-table:: Python Dependencies
   :widths: 30 60 30
   :header-rows: 1
   
   * - Package 
     - Application
     - Program Module Utilization
   * - argparse
     - This library collects arguments that are provided in the command line when executing the script so that they can be easily accessed as variables
     - BASSPRO
   * - csv
     - This library assists with reading in data from csv files such as the metadata and auto_criteria settings files
     - BASSPRO
   * - datetime
     - This library provides a data structure for handling dates and times and applying mathematic operations to them - this is used as part of the logging system for tracking events through the execution of the script
     - BASSPRO
   * - logging
     - This library aids in generating contextualized logging feedback to the console as well as the log file
     - BASSPRO  
   * - lmxl
     - This package is used in the ReadMe word document generation to access content within configuration .csv files.
     - GUI
   * - math
     - This library provides additional functions for numerical operations and is currently used to aid in verifying if N/A values are present
     - BASSPRO
   * - numpy
     - This library includes several classes and functions that are used including arrays for storing values as well as mathematic and filtering generating functions
     - BASSPRO, GUI
   * - os
     - This library provides access to functions for file i/o and filepath creationg and parsing
     - BASSPRO
   * - pandas
     - This library is used for its DataFrame class that is used to store several variables including the input signals and the detected breaths and their derived parameters. Several methods that act upon DataFrame are utilized for filtering and applying calculations to the data.
     - BASSPRO, GUI
   * - pyodbc
     - This library provides methods and utilities for accessing ODBC databases in Python
     - GUI
   * - PyQt5
     - This library is used for rendering graphics and GUI components like buttons and input boxes. It also manages processes that run parallel to the main GUI thread.
     - GUI
   * - PyQt5-Qt5
     - This library is a subset of a Qt installation that is required by PyQt5
     - GUI
   * - PyQt5-sip
     - This library provides Python bindings for C/C++ in support of PyQt5
     - GUI
   * - python-dateutil
     - This library extends the Python native package *datetime* with extra utilities for working with dates and times
     - GUI
   * - python-docx
     - This library is used to render word documents that summarize user selections for STAGG runs.
     - GUI
   * - pytz
     - This library provides Olson timezone calculations
     - GUI
   * - re
     - This library is used for regular expression parsing of text strings and is used for parsing MUID and PlyUID information
     - BASSPRO
   * - scipy
     - This library provides functions used for signal processing including high and low pass filters that are used to reduce noise in the derived flow signal. Additionally, this library's ``linregress`` function is used for the creation of calibration curves (O2 and CO2 concentrations vs. voltages).
     - BASSPRO, GUI
   * - six
     - This library provides smooth compatibility between libraries written for both Python 2 and Python 3
     - GUI
   * - statistics
     - This library is used to provide access to statistical functions such as median
     - BASSPRO
   * - sys
     - This library is used to connect the systems stdout to logging functions, used for displaying logging messages in the console
     - BASSPRO
   * - tkinter
     - This library is used to provide a minimal GUI when running the BASSPRO script separately from the GUI
     - BASSPRO 

Install R
^^^^^^^^^^^^^^^^^^^^
`Install R here <https://cran.r-project.org/bin/windows/base/>`_.

Install R Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^     
1. All required packages and dependencies for R are automatically downloaded and installed upon the first run of STAGG. 
2.  Manual package installation can be done inside of the R terminal using

``install.packages("<package_name>", dependencies = TRUE)``

or each individual package can be installed through the command line via `CRAN <https://cran.r-project.org/>`_ with

.. code-block::
   
   wget https://cran.r-project.org/src/contrib/<package_name_and_version>.tar.gz
   R CMD INSTALL <package_name_and_version>.tar.gz

    
.. note::
    
   Note that the latter method does not automatically install package dependencies. The list of 
   required packages is below.

3.  Producing the R markdown also requires an installation of pandocs; instructions can be found `here <https://pandoc.org/installing.html>`_.

.. list-table:: R Dependencies
   :widths: 30 60
   :header-rows: 1
   
   * - Package 
     - Application
   * - argparser
     - Allows for operation of the R module, STAGG, from the command line terminal
   * - data.table
     - Reformatting of data tables in preparation for manipulations
   * - ggpubr
     - Graphing and data visualization
   * - ggthemes
     - Additional settings and configurations for graphing
   * - kableExtra
     - Builds common complex tables and manipulates table styles
   * - lme4
     - Fits linear and generalized linear mized-effects models
   * - lmerTest
     - Provides p-values for linear mixed-effects models
   * - magrittr
     - Improves readability and intuitiveness of code
   * - multcomp
     - Fits linear mixed-effects models and multiple comparisons
   * - openxlsx
     - Reads, writes, and edits xlsx files
   * - pandoc
     - Used for R markdown rendering
   * - RColorBrewer
     - Generates colors for graphing
   * - reshape2
     - Used to transform data table formats for some optional graphs
   * - rjson
     - Allows import of JSON formatted files
   * - rmarkdown
     - Produces html summary file with all .svg output files in one page
   * - svglite
     - Produces user-friendly editable .svg image files
   * - tidyselect
     - Allows verbiage consistency between packages
   * - tidyverse
     - Data management and formatting; include dplyr and ggplot2 packages
   * - xtable
     - Generates tables from functional outputs

Launching Breathe Easy
===========================
From packaged version
-------------------------
#. Inside the unzipped file, you'll find a folder named ``BASSPRO-STAGG_QUIPPL``.
#. Double click the ``launcher.bat`` file in this folder to launch the GUI.
  
    #. The ``launcher.bat`` file can be moved to your Desktop or another easily accessible location 
       on your computer to make the program easy to access later.

From source
--------------------
.. code-block::

        #Posix
        source venv/bin/activate
        python3 scripts/GUI/MainGUImain.py
        
        #Windows
        <venv>/Scripts/activate.bat
        python3 scripts/GUI/MainGUImain.py
