Markdown Color Formatter
=======

A Logging.Formatter instance used to modify the Python Logging Facility to add color and formatting using a Markdown-like syntax.

Inspired by `Mistune <https://github.com/lepture/mistune>`_.


Features
--------

* **Written in Python**. Only tested with Python 2.7+
* **Features** Font color (foreground and background), italics, bold, underline, reverse, and strikethrough


Installation
------------

Copy the markdown_color_formatter.py into your Python code directory


Basic Usage
-----------

Render a markdown-like formatted text to the console:

.. code:: python

	import sys
	import logging

	from markdown_color_formatter import MarkdownColorFormatter

	class ColorFormatter(logging.Formatter):
		def __init__(self, use_color=True):
			self.markdown_formatter = MarkdownColorFormatter.Formatter(use_color)
			logging.Formatter.__init__(self, self.markdown_formatter.log_format)

		def format(self, record):
			modified_record, self._fmt = self.markdown_formatter.format(record, self._fmt)
			return logging.Formatter.format(self, modified_record)

	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	handler = logging.StreamHandler(sys.stdout)
	handler.setFormatter(ColorFormatter())
	logger.addHandler(handler)

	log = logging.getLogger('Logging Color Formatter Test')
	log.info('I am using **{{red}}Markdown Color Formatter{{red}}**')
	# output: <p>I am using <strong><fonti color="red">Markdown Color Formatter</font></strong></p>


Bugs
----
Kindly report bugs `here <https://github.com/davidmroth/markdown_color_formatter/issues>`_.
