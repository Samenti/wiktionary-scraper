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
			words.append(line.strip('\n'))

print "words:", words
response = requests.get(URL_PREFIX + words.pop())
tree = html.fromstring(response.content)

# content = tree.xpath('//table[contains(@class, "fi-decl")]//tr[@class="vsHide"]//span//text()|//table[contains(@class, "fi-decl")]//tr[@class="vsHide"]//td[not(*)]/text()')
# num_elem = len(tree.xpath('//*'))
# num_tr = len(tree.xpath('//table[contains(@class, "fi-decl")]//tr[@class="vsHide"]//span//text()|//table[contains(@class, "fi-decl")]//tr[@class="vsHide"]//td[not(*)]/text()'))
# print content, num_elem, num_tr

def scrape_declension_table(word, wtype="Noun", language="Finnish"):
	"""
	Scrape the declension table data from Wiktionary for 'word'.
	'wtype' can be "Noun", "Adjective", "Numeral" or "Pronoun".
	
	Output is a list of nominal forms in the scheme: 
	'<nominative singular', '<nominative plural>', 
	'<accusative-nominative singular>', '<accusative plural>', 
	'<accusative-genitive singular>',
	'<genitive singular>', '<genitive plural>',
	'<partitive singular>', '<partitive plural>', <etc.>
	"""
	response = requests.get(URL_PREFIX + word)
	tree = html.fromstring(response.content)

	lang_on_page = tree.xpath('//h2//*[text()="' + language + '"]')    # select all h2 elements that have text 'language' downstream
	# return empty list if the page doesn't have the required language
	if lang_on_page == []:
		return []
	print "lang_on_page[0]:", lang_on_page[0], "text:", lang_on_page[0].xpath('.//text()')
	
	lang_h2 = lang_on_page[0].xpath('./..')
	print "lang_h2:", lang_h2, "text:", lang_h2[0].xpath('.//text()')

	# outer_div = lang_on_page[0].xpath('./ancestor::h2/parent::div')    # select the div element that is the parent of the above h2
	# print "outer_div:", outer_div
	
	next_lang_h2 = lang_on_page[0].xpath('./ancestor::h2/following-sibling::h2')    # select the next h2 sibling, probably the next language's section heading
	next_lang_h2 = lang_h2[0].xpath('./following-sibling::h2[1]')
	if next_lang_h2 == []:
		next_lang_text = ""
	else: 
		next_lang_text = next_lang_h2[0].xpath('.//text()')
	print "next_lang_h2:", next_lang_h2, "next_lang_text:", next_lang_text

	
	curr_elem = lang_h2
	while True:
		next_elem = curr_elem[0].xpath('./following-sibling::*[1]')
		if next_elem == []:    # if there are no more siblings, end search
			break
		# print "next_elem[0]:", next_elem[0]
		if next_elem[0].tag in ["h3", "h4", "h5", "h6"]:
			if wtype in next_elem[0].xpath('.//text()'):    # if the desired word class is found, end search
				# print "Found " + wtype + " in sibling " + next_elem[0].tag + "!"
				wtype_elem = next_elem[0]
				break
			# else:
			# 	print next_elem[0].xpath('.//text()')
			# 	print "Haven't found " + wtype + " in sibling " + next_elem[0].tag + ".."
		elif next_elem[0].tag == "h2":    # if search finds next h2 element, probably the next language's section, end search
			# print "No sibling element with " + wtype + " type. Searched " + str(counter) + " elements."
			break
		curr_elem = next_elem

	print "wtype_elems:", wtype_elem, "text:", wtype_elem[0].xpath('.//text()')

	table = wtype_elem[0].xpath('./following::table[1]')
	print "table:", table
	if wtype == "Noun":
		raw_table_data = table[0].xpath('./tbody/tr[@class="vsHide"]/td//text()')
		print "raw_table_data:", raw_table_data
		table_data = []
		for raw_data in raw_table_data:
			if raw_data == u'\u2014\n':
				table_data.append(u'')
			elif raw_data != '\n':
				table_data.append(raw_data)
		table_data[2] = (table_data[2], table_data[4])
		table_data.pop(4)
		print "table_data:", table_data

	elif wtype == "Pronoun":
		return




scrape_declension_table(u'äiti')
