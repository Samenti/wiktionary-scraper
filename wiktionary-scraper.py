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


def scrape_declension_table(word, wtype="Noun", language="Finnish", tabletype="same_"):
	"""
	Scrape the declension table data from Wiktionary for "word".
	
	"wtype" can be "Noun", "Proper noun", "Adjective", "Numeral" or "Pronoun".
	"tabletype" can be "same_" or "other_", the latter meaning that the table should
	be scraped by the method used for the table type not usually associated with the "wtype".
	
	Output is a list of nominal forms in the scheme (for nouns): 
	'<nominative singular', '<genitive plural>',
	('<accusative-nom singular>', '<accusative-gen singular>'),
	'<partitive singular>', '<illative singular>',
	... <ine, all, ade, ela, abl, ess, abe, tra, ins, com> ...,
	'<nominative plural>', '<genitive plural>',
	... '<comitative plural>'
	In case there are multiple correct forms at a certain case,
	a tuple of strings is used (see accusative singular).
	Output is similar for other wtypes.
	"""

	# return empty list if wtype is invalid
	valid_wtypes = {
	"Noun", "noun", "Proper noun", "proper noun", "Adjective", "adjective", "Numeral", "numeral", "Pronoun", "pronoun"
	}
	if wtype not in valid_wtypes:
		print("type '" + wtype + "' is not a valid word type")
		return []
	elif wtype == "noun":
		wtype = "Noun"
	elif wtype == "proper noun":
		wtype = "Proper noun"
	elif wtype == "pronoun":
		wtype = "Pronoun"
	elif wtype == "numeral":
		wtype = "Numeral"
	elif wtype == "adjective":
		wtype = "Adjective"
	
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
			# print("wtype:", wtype, "next_elem:", next_elem[0].xpath('.//text()'))
			if wtype in next_elem[0].xpath('.//text()'):
				wtype_elem = next_elem[0]
				break
		# if search finds next h2 element, probably the next language's section, return empty list
		elif next_elem[0].tag == "h2":
			print("scraper couldn't find type '" + wtype + "' in language '" + language + "'")
			return []
		curr_elem = next_elem

	invalid_cell_cont = {
	'', '\n', 'rare', 'rare\n', '—', '—\n', '\u2014', '\u2014\n', '–', '–\n', '\u2013', '\u2013\n'
	}
	dashes = {
	'—', '—\n', '\u2014', '\u2014\n', '–', '–\n', '\u2013', '\u2013\n'
	}
	to_strip = '\n ()*'
	

	# articles about nouns and adjectives usually have the same type of table on the Wiktionary
	if wtype in {"Noun", "Proper noun", "Adjective"} or tabletype == "other_":
		table = wtype_elem[0].xpath('./following::table[@class="inflection-table fi-decl vsSwitcher"]')
		# print("table:", table)
		col_sg = []
		col_pl = []
		curr_row = table[0].xpath('./tbody/tr[@class="vsHide"][1]')
		# if the first row contains data and not headings, handle that:
		if curr_row[0].xpath('./td') != []:
			cell_cont = curr_row[0].xpath('./td[1]//text()')
			strings = []
			# handle the case when multiple correct forms are delineated with commas
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				# exclude strings that are not valid word forms
				if string not in invalid_cell_cont:
					# strip starting and trailing whitespaces, linebreaks and other invalid characters
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					# dash always means no valid form
					word_forms.append('')
			# add to singulars column, add as tuple if there were multiple valid strings
			if len(word_forms) == 1:
				col_sg.append(word_forms[0])
			elif len(word_forms) > 1:
				col_sg.append(tuple(word_forms))
			
			cell_cont = curr_row[0].xpath('./td[2]//text()')
			strings = []
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				if string not in invalid_cell_cont:
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					word_forms.append('')
			# add to plurals column, add as tuple if there were multiple valid strings
			if len(word_forms) == 1:
				col_pl.append(word_forms[0])
			elif len(word_forms) > 1:
				col_pl.append(tuple(word_forms))

		# iterate over every row in the table
		while True:
			next_row = curr_row[0].xpath('./following-sibling::tr[@class="vsHide"][1]')

			# quit loop if there are no more rows
			if len(next_row) == 0:
				break

			# if there are no data cells in row, skip to next
			if next_row[0].xpath('./td') == []:
				curr_row = next_row
				continue
			
			cell_cont = next_row[0].xpath('./td[1]//text()')
			strings = []
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				if string not in invalid_cell_cont:
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					word_forms.append('')
			if len(word_forms) == 1:
				col_sg.append(word_forms[0])
			elif len(word_forms) > 1:
				col_sg.append(tuple(word_forms))
			
			cell_cont = next_row[0].xpath('./td[2]//text()')
			strings = []
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				if string not in invalid_cell_cont:
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					word_forms.append('')
			if len(word_forms) == 1:
				col_pl.append(word_forms[0])
			elif len(word_forms) > 1:
				col_pl.append(tuple(word_forms))

			curr_row = next_row

		# the genitive looking form of accusative singular is in a separate row,
		# but we need it in a tuple together with the nominative looking form
		acc_gen = col_sg.pop(2)
		col_sg[1] = (col_sg[1], acc_gen)

		answer_table = []
		# this mapping helps rearrange the output of the scraper to be the input of FDTT
		mapping = (0, 2, 1, 3, 6, 4, 9, 7, 5, 8, 10, 13, 11, 12, 14)
		for col in (col_sg, col_pl):
			for idx in mapping:
				answer_table.append(col[idx])

		return answer_table

	# articles about pronouns and numerals tend to have the same type of table on the Wiktionary
	elif wtype in {"Pronoun", "Numeral"} or tabletype == "other_":
		table = wtype_elem[0].xpath('./following::table[1]')
		col_sg = []
		col_pl = []
		table = table[0].xpath('.//table[1]')
		if table == []:
			return []
		
		curr_row = table[0].xpath('./tbody/tr[1]')
		if curr_row[0].xpath('./td') != []:
			cell_cont = curr_row[0].xpath('./td[2]//text()')
			strings = []
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				if string not in invalid_cell_cont:
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					word_forms.append('')
			if len(word_forms) == 1:
				col_sg.append(word_forms[0])
			elif len(word_forms) > 1:
				col_sg.append(tuple(word_forms))
			
			cell_cont = curr_row[0].xpath('./td[2]//text()')
			strings = []
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				if string not in invalid_cell_cont:
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					word_forms.append('')
			if len(word_forms) == 1:
				col_pl.append(word_forms[0])
			elif len(word_forms) > 1:
				col_pl.append(tuple(word_forms))

		while True:
			next_row = curr_row[0].xpath('./following-sibling::tr[1]')

			if len(next_row) == 0:
				break

			if next_row[0].xpath('./td') == []:
				curr_row = next_row
				continue
			
			cell_cont = next_row[0].xpath('./td[2]//text()')
			strings = []
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				if string not in invalid_cell_cont:
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					word_forms.append('')
			if len(word_forms) == 1:
				col_sg.append(word_forms[0])
			elif len(word_forms) > 1:
				col_sg.append(tuple(word_forms))
			
			cell_cont = next_row[0].xpath('./td[3]//text()')
			strings = []
			for string in cell_cont:
				strings.extend(string.split(', '))
			word_forms = []
			for string in strings:
				if string not in invalid_cell_cont:
					bare = string.strip(to_strip)
					if bare not in invalid_cell_cont:
						word_forms.append(bare)
				elif string in dashes:
					word_forms.append('')
			if len(word_forms) == 1:
				col_pl.append(word_forms[0])
			elif len(word_forms) > 1:
				col_pl.append(tuple(word_forms))

			curr_row = next_row


		answer_table = []
		# this mapping helps rearrange the output of the scraper to be the input of FDTT
		mapping = (0, 1, 3, 2, 6, 4, 9, 7, 5, 8, 10, 13, 11, 12, 14)
		for col in (col_sg, col_pl):
			for idx in mapping:
				answer_table.append(col[idx])

		return answer_table



words = []
with io.open("nominals.txt", mode='rt', encoding='utf-8') as words_file:
	for line in words_file:
		if line != '\n':
			word = line.strip('\n').split(',')
			for idx in range(len(word)):
				word[idx] = word[idx].strip()

			if "other_" in word:
				other_table = "other_"
				word.remove("other_")
			else:
				other_table = "same_"

			if len(word) == 2:
				words.append( (word[0], "Noun", "Finnish", other_table, word[-1]) )
			elif len(word) == 3:
				if word[1].strip() in {
					"Noun", "noun", "Proper noun", "proper noun", "Adjective",
					"adjective", "Numeral", "numeral", "Pronoun", "pronoun"
					}:
					words.append( (word[0], word[1], "Finnish", other_table, word[-1]) )
				else:
					words.append( (word[0], "Noun", word[1], other_table, word[-1]) )
			elif len(word) > 3:
				words.append( (word[0], word[1], word[2], other_table, word[-1]) )

print("words:", words)

tables = []
for word in words:
	response = requests.get(URL_PREFIX + word[0])
	tree = html.fromstring(response.content)
	declensions = scrape_declension_table(word[0], word[1], word[2], word[3])
	declensions.append(word[4])
	print("declensions:", declensions)
	tables.append(declensions)

with io.open('tables.txt', mode='w', encoding="utf-8") as tables_file:
    json.dump(tables, tables_file)
