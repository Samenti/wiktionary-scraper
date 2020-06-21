# coding: utf-8

"""
Wiktionary Scraper for FDTT
---------------------------
This is Python 3 program using lxml and requests libraries to scrape
declension table data from Wiktionary.org.
"""

# Max line length w/ --- w/o flowing text blocks (PEP 8 style guide): 72 --- 79

import io
import requests
from lxml import html
import json

URL_PREFIX = 'https://en.wiktionary.org/wiki/'


def scrape_declension_table(word, wtype="Noun", language="Finnish"):
	"""
	Scrape the declension table data from Wiktionary for 'word'.
	'wtype' can be "Noun", "Adjective", "Numeral" or "Pronoun".
	
	Output is a list of nominal forms in the scheme: 
	'<nominative singular', '<nominative plural>', 
	'<accusative-nominative singular>', '<accusative plural>', 
	'<accusative-genitive singular>',
	'<genitive singular>', '<genitive plural>',
	'<partitive singular>', '<partitive plural>', etc.
	In case there are multiple correct forms at a certain case,
	a tuple of strings is used.
	"""

	# return empty list if wtype is invalid
	valid_wtypes = {
	"Noun", "noun", "Adjective", "adjective", "Numeral", "numeral", "Pronoun", "pronoun"
	}
	if wtype not in valid_wtypes:
		print("type '" + wtype + "' is not a valid word type")
		return []
	
	response = requests.get(URL_PREFIX + word)
	tree = html.fromstring(response.content)

	# select all h2 elements that have text 'language' downstream
	lang_on_page = tree.xpath('//h2//*[text()="' + language + '"]')
	# return empty list if the page doesn't have the required language
	if lang_on_page == []:
		print("scraper couldn't find language '" + language + "' at location " + URL_PREFIX + word)
		return []
	
	lang_h2 = lang_on_page[0].xpath('./..')
	
	# select the next h2 sibling, probably the next language's section heading
	next_lang_h2 = lang_h2[0].xpath('./following-sibling::h2[1]')
	if next_lang_h2 == []:
		next_lang_text = ""
	else: 
		next_lang_text = next_lang_h2[0].xpath('.//text()')

	curr_elem = lang_h2
	while True:
		next_elem = curr_elem[0].xpath('./following-sibling::*[1]')
		# if there are no more siblings, end search
		if next_elem == []:
			break
		if next_elem[0].tag in ["h3", "h4", "h5", "h6"]:
			# if the desired word class is found, end search
			if wtype in next_elem[0].xpath('.//text()'):
				wtype_elem = next_elem[0]
				break
		# if search finds next h2 element, probably the next language's section, return empty list
		elif next_elem[0].tag == "h2":
			print("scraper couldn't find type '" + wtype + "' in language '" + language + "'")
			return []
		curr_elem = next_elem

	table = wtype_elem[0].xpath('./following::table[1]')
	# print("table:", table)
	if wtype in {"Noun", "noun"}:
		raw_table_data = table[0].xpath('./tbody/tr[@class="vsHide"]/td//text()')
		# print("raw_table_data:", raw_table_data)
		table_data = []
		for raw_data in raw_table_data:
			if raw_data == '\u2014\n':
				table_data.append('')
			elif raw_data != '\n':
				table_data.append(raw_data)
		table_data[2] = (table_data[2], table_data[4])
		table_data.pop(4)
		# print("table_data:", table_data)
		return table_data

	elif wtype in {"Pronoun", "pronoun"}:
		return
	elif wtype in {"Adjective", "adjecive"}:
		return
	elif wtype in {"Numeral", "numeral"}:
		return


words = []
with io.open("nominals.txt", mode='rt', encoding='utf-8') as words_file:
	for line in words_file:
		if line != '\n':
			word = line.strip('\n').split(',')
			if len(word) == 1:
				words.append( (word[0].strip(), "Noun", "Finnish") )
			elif len(word) == 2:
				if word[1].strip() in ["Noun", "Pronoun", "Numeral", "Adjective"]:
					words.append( (word[0].strip(), word[1].strip(), "Finnish") )
				else:
					words.append( (word[0].strip(), "Noun", word[1].strip()) )
			else:
				words.append( (word[0].strip(), word[1].strip(), word[2].strip()) )

print("words:", words)

tables = {}
for word in words:
	response = requests.get(URL_PREFIX + word[0])
	tree = html.fromstring(response.content)
	tables[word[0]] = scrape_declension_table(word[0], word[1], word[2])

with io.open('tables.txt', mode='w', encoding="utf-8") as tables_file:
    json.dump(tables, tables_file)
