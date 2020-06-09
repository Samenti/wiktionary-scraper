# coding: utf-8

"""
Wiktionary Scraper for FDTT
---------------------------
This is Python 2.7 program using lxml and requests libraries to scrape
declension table data from Wiktionary.org.
"""

# Max line length w/ --- w/o flowing text blocks (PEP 8 style guide): 72 --- 79

import io
import requests
from lxml import html

URL_PREFIX = u'https://en.wiktionary.org/wiki/'

words = []
with io.open("nominals.txt", mode="rt", encoding="utf-8") as words_file:
	for line in words_file:
		if line != u'\n':
			words.append(line.rstrip('\n'))