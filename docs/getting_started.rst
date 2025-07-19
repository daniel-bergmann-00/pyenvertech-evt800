Getting Started
===============

Install
*******
PyEnvertechEVT800 is available on `pypi`_ and can be installed using pip.

.. code-block:: console
   
   pip install pyenvertechevt800

.. _pypi: https://pypi.org/project/pyenvertechevt800/


Create SMA instance
*******************

The :class:`~pyenvertechevt800.EnvertechEVT800` class requires an IP Address and a PORT.

.. code-block:: python3

    ip = "127.0.0.1"
    port = "14889"
    
    sma = pyenvertechevt800.EnvertechEVT800(ip, port)

Complete Example
****************

A full example can be found in the `Github repository`_

.. _Github repository: https://github.com/daniel-bergmann-00/pyenvertechevt800/blob/master/example.py
