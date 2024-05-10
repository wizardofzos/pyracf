Installation
============

Becuase pyRACF is hosted at
`pypi.org <https://pypi.org/project/pyracf/%5D>`__ you can install it
easily via

::

   pip install pyracf

If you’d rather install from source you need to clone this repository
then run the setup.py as follows

::

   git clone https://github.com/wizardofzos/pyracf.git
   cd pyracf
   python setup.py install

Full control installation
-------------------------

If you did not install git on your system, or you need full control over the location of the install directories for pyRACF, you can do the following.

#. Go to `the github repository <https://github.com/wizardofzos/pyracf>`__, click the green ``< > code`` push button, and select ``Download ZIP``.

#. Open the ZIP file, it contains one directory ``pyracf-main``.  Extract this directory, for example, to your Documents folder.  When you explore this folder, the executable files can be found in ``Documents/pyracf-main/src/pyracf``.  This ``pyracf`` directory is referred to as the ``pyracf module``.

#. Add the new directory to your PYTHONPATH, before starting python

   ::

      export PYTHONPATH=/home/your-id/Documents/pyracf-main/src/:$PYTHONPATH

   If you don't have a command prompt because, for example, your start Jupyter Notebook from the desktop, you can add the path containing the pyracf module to the python path with python commands

   ::

      import sys
      new_path = '/home/your-id/Documents/pyracf-main/src/'
      sys.path.append(new_path)

#. If this worked, you should be able to load the main class with

   ::

      from pyracf import RACF

   To inspect the list of libraries python uses, type
   
   ::
   
      import sys
      sys.path

Using this mechanism, you could also switch between different versions of the pyracf module easily, without having to learn about ``venv``.  Just remember to restart your python kernel, so you get a new path and fresh modules.

If you're stuck in the python command prompt, you can exit by typing `exit()`.

Jupyter Notebook
----------------

The python (or python3) command presents you with a command prompt where you enter a python command and press Enter to see the result.  The cursor-up key retrieves previous commands that you can modify before running them again.  These commands are saved across sessions too.  You can also scroll up and down through the command output using the scroll bar at the right edge of your screen.  However, the command prompt is not really an editor.

Jupyter Notebook allows you to enter commands into *cells*, you execute a cell by pressing shift-Enter  You leave the code in the previous cells just where it is, and enter extra lines in the next empty cell.  And in fact, you can review output from those previous cells without having to re-run them.

Notebooks can be saved, look for the floppy disk icon.  You can archive a notebook, by saving it under another name, you can duplicate notebooks from the notebook directory page.  You might say, notebook are to the python command prompt what a desktop environment is to the DOS command prompt.

.. image:: _static/pictures/Jupyter%20initial.png
  :width: 1000
  :alt: Jupyter notebook

Read more `here <https://www.geeksforgeeks.org/install-jupyter-notebook-in-windows/>`__ or `here <https://docs.jupyter.org/en/latest/install/notebook-classic.html>`__.
