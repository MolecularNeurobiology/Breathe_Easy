# BASSPRO-STAGG
# REFACTOR README

resources folder for  gui refactor and code review projects
Ray Lab Project: PM154_PJ_GUI_Refactoring

Project Schemas: 
*general user experience workflow
...
X:\Projects\PM154_PJ_GUI_Refactoring\Schema

*architecture (named components of the GUI)
...

Datasets for Testing: 


-----
#Style Guide
**Improve Readability, Improve Reliabilty**
The general style is to follow the guidelines as described out in PEP8
https://peps.python.org/pep-0008/

Examples
*modules
*Classes()
*variables
*functions()
*methods()
*CONSTANTS

Notes 
Descriptive naming is preferred (ideally what it does, not how it does it)
if multiple words are needed to be descriptive then underscores_are_preferred. Classes can use CamelCase.
Avoid using python or library related reserved words for names https://realpython.com/lessons/reserved-keywords/ 
-----
**Make it easier to tell where things come from**
Avoid:
from [module] import *

Preferred:
import [module]
or
from [module] import [part1], [part2]

-----
Documenting Functions, Methods, and Classes
Use Docstrings for all functions, methods and classes
If the code is changed, the Docstring needs to be updated
Avoid leaving a ‘lie’ for the next person to work on the code

Example:
def sum_two_numbers(number1,number2):
    """
    This function returns the sum of two numbers
    Parameters
    ----------
    number1 : float
        A number to be added
    number2 : float
        Another number to be added

    Returns
    -------
    output : float
        the sum of number1 and number2.
    """
    output = arg1+arg2
    return output





