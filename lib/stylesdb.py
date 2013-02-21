#    This file is part of GThemer.
#
#    GThemer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GThemer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
"""
stylesdb is the database that contains all the styles information for the 
GThemer application.
"""

import sys
import os
import sqlite3

from gi.repository import GtkSource

CREATE_TABLE_LANGUAGES = """
CREATE TABLE languages
	(scheme TEXT,
	 title TEXT,
	 lang_seq_id INTEGER PRIMARY KEY AUTOINCREMENT
	);
CREATE UNIQUE INDEX languages_index ON languages (scheme);
"""

CREATE_TABLE_STYLE_SCHEMES = """
CREATE TABLE style_schemes
	(lang_seq_id INTEGER,
	 style TEXT,
	 style_seq_id INTEGER PRIMARY KEY AUTOINCREMENT
	);
CREATE UNIQUE INDEX style_schemes_index ON style_schemes (style, lang_seq_id);
"""

CREATE_TABLE_FORMATS = """
CREATE TABLE formats
	(style_seq_id INTEGER NOT NULL,
	 foreground TEXT,
	 background TEXT,
	 bold INTEGER,
	 italic INTEGER,
	 strikethrough INTEGER,
	 underline INTEGER
	);
CREATE UNIQUE INDEX format_index ON formats (style_seq_id);
"""

CREATE_TABLE_GLOBALS = """
CREATE TABLE globals
	(scheme TEXT,
	 background TEXT,
	 foreground TEXT,
	 bold INTEGER,
	 italic INTEGER,
	 strikethrough INTEGER,
	 underline INTEGER
	);
CREATE UNIQUE INDEX globals_index ON globals (scheme);
"""

class GThemerDB:

	# global_styles - List of all appropriate global styles keys that can
	# exist in the current GtkSourceView styles definition. Currently I can't
	# figure out how to retrieve these values using the pygobject api...
	# so this list will have to be static. GRR.
	global_styles = ('text', 'selection', 'selection-unfocused', 'cursor',
	'cursor-secondary', 'current-line', 'line-numbers', 'draw-spaces', 'bracket-match',
	'bracket-mismatch', 'right-margin', 'search-match')
	
	def __init__(self, filename):
		'''
		Initialize database `filename`. Initialize the database, detect the
		schemes from GtkSource and insert them into the database.
		
		*filename* (``str``) is the filename of the sqlite database.
		'''
		created = os.path.exists(filename)
		self.conn = sqlite3.connect(filename)
		self.conn.row_factory = sqlite3.Row
		self.cursor = self.conn.cursor()
		if not created:
			self.cursor.executescript(CREATE_TABLE_LANGUAGES)
			self.cursor.executescript(CREATE_TABLE_STYLE_SCHEMES)
			self.cursor.executescript(CREATE_TABLE_FORMATS)
			self.cursor.executescript(CREATE_TABLE_GLOBALS)
			self.conn.commit()
			self._init_globals()
			self._init_default()
			
	def _init_globals(self):
		'''
		When a new database is created, initialize the global style schemes.
		'''
		for style in self.global_styles:
			self.new_global(style)
	
	def _init_default(self):
		'''
		When a new database is created, intialize it with the styles defined in
		GtkSource.
		'''
		manager = GtkSource.LanguageManager()
		languages = manager.get_language_ids()
		for lang in languages:
			lang_config = {}
			style_ids = manager.get_language(lang).get_style_ids()
			name = manager.get_language(lang).get_name()
			if name == "" or style_ids == []:
				print("**GThemer Warning: could not add language: {} with style_ids: {}".format(repr(name), repr(style_ids)))
				continue
			self.new_language(lang, name)
			for style in style_ids:
				print "Adding style: {}\r".format(repr(style)), 
				sys.stdout.flush()
				self.new_style(lang, style)
				self.new_format(lang, style)
		print
		self.conn.commit()

	def new_language(self, language, language_title):
		'''
		Add a language to the database.
		
		*language* (``str``) is the language to add.
		
		*language_title* (``str``) is the proper name of the language.
		'''
		query = """
		INSERT INTO languages
			(scheme,
			 title
			)
		VALUES (?, ?);
		"""
		self.cursor.execute(query, (language, language_title))
	
	def new_style(self, language, style_name):	
		'''
		Add scheme `scheme_name` to the database with `style_title`.
		
		*language* (``str``) is the language to add a style scheme to.
		
		*style_name* (``str``) is the name of a style scheme.
		'''
		query = """
		INSERT INTO style_schemes
			(lang_seq_id,
			 style
			)
		VALUES
			((SELECT DISTINCT lang_seq_id FROM languages WHERE languages.scheme = {}), ?);
		""".format(repr(language))
		self.cursor.execute(query, (style_name,))
	
	def new_global(self, scheme):
		'''
		Add global `scheme` to the database with `global_config`.
		
		*scheme* (``str``) is the name of a global scheme.
		
		*global_config* (``dict``) is settings for the global themes.		
		'''
		query = """
		INSERT INTO globals
			(scheme)
		VALUES (?);
		"""
		self.cursor.execute(query, (scheme,))
		
	def new_format(self, language, style_name):
		'''
		Add new style scheme to the database.
		
		*language* (``str``) is the language the style is a part of.
		
		*style_name* (``str``) is the name of the style to add a format to.
		
		*format_config* (``dict``) is a mapping of the values to format.
		'''
		query = """
		INSERT INTO formats
			(style_seq_id)
		SELECT DISTINCT style_seq_id 
			 	FROM style_schemes
			 	LEFT JOIN languages
			 		ON style_schemes.lang_seq_id = languages.lang_seq_id
			 WHERE languages.scheme = {} AND style_schemes.style = {};
		""".format(repr(language), repr(style_name))
		self.cursor.execute(query)

	def update_format(self, language, style_name, format_config):
		'''
		Update a current scheme in the database.
		
		*language* (``str``) is the language the style is a part of.
		
		*style_name* (``str``) is the name of the style to add a format to.
		
		*format_config* (``dict``) is a mapping of the values to format.
		'''
		set_clause = ""
		for key, value in format_config.iteritems():
			set_clause += ", {key} = {value}".format(key=key, value=repr(value))
		set_clause = set_clause.strip().lstrip(',')
					
		query = """
		UPDATE formats
		SET {set_clause}
		WHERE formats.style_seq_id IN (
			SELECT DISTINCT style_schemes.style_seq_id 
				FROM style_schemes
				LEFT JOIN languages
					ON languages.lang_seq_id = style_schemes.lang_seq_id
				WHERE languages.scheme = '{lang}'
				  AND style_schemes.style = '{style}');
		""".format(set_clause=set_clause,
		           lang=language,
		           style=style_name)
		print query
		self.cursor.execute(query)
		self.conn.commit()
			
	def update_global(self, scheme, global_config):
		'''
		Update a global style scheme in the database.
		
		*scheme* (``str``) is the global style scheme to update.
		
		*global_config* (``dict``) is a mapping of the global values to format.
		'''
		set_clause = ""
		for key, value in global_config.iteritems():
			set_clause += ", {key} = {value}".format(key=key, value=repr(value))
		set_clause = set_clause.strip().lstrip(',')
		
		query = """
		UPDATE globals
		SET {set_clause}
		WHERE scheme = ?
		""".format(set_clause=set_clause)
		
		self.cursor.execute(query, (scheme,))
		self.conn.commit()
		
	def iter_globals(self):
		'''
		Yield global style schemes.
		'''
		query = "SELECT * FROM globals"
		self.cursor.execute(query)
		for record in self.cursor.fetchall():
			yield dict(zip(record.keys(), record))

	def iter_styles(self, language=None):
		'''
		Yield styles, optionally filtering for a specific language
		
		*language* (``str``) is the language to filter.
		'''
		where_clause = "WHERE languages.scheme = {}".format(repr(language)) if language is not None else ""
		query = """
		SELECT  style_schemes.style,
	 			formats.foreground,
	 			formats.background,
	 			formats.bold,
	 			formats.italic,
	 			formats.strikethrough,
	 			formats.underline
		FROM formats
			LEFT JOIN style_schemes
			ON style_schemes.style_seq_id = formats.style_seq_id
			LEFT JOIN languages
			ON style_schemes.lang_seq_id = languages.lang_seq_id
		{where_clause}
		""".format(where_clause=where_clause)
		
		self.cursor.execute(query)
		for record in self.cursor.fetchall():
			yield dict(zip(record.keys(), record))

	def iter_languages(self):
		'''
		Yield languages and their proper names
		'''
		query = """SELECT scheme, 
						  title 
				   FROM languages;"""
		self.cursor.execute(query)
		for record in self.cursor.fetchall():
			yield (record['scheme'], record['title'])


if __name__ == '__main__':
	db = GThemerDB('test.db')
	#print("Languages:")
	#for lang in db.iter_languages():
	#	print(lang)
	
	#print("\nStyles:")
	#for style in db.iter_styles():
	#	print(style)
	
	#print("\nGlobals:")
	#for style in db.iter_globals():
	#	print(style)
	
	test_lang = None
	for lang in db.iter_languages():
		test_lang = lang
		break
	test_style = None
	for style in db.iter_styles():
		test_style = style['style']
		break
	
	print("Updating Format: lang: {}, style: {}".format(test_lang, test_style))
	test_config = {
		'foreground': "Green",
		'background': "Black",
	}
	db.update_format(test_lang, test_style, test_config)
	
	test_global = db.global_styles[0]
	db.update_global(test_global, test_config)	
		


		
		
		
		
		
		
		
		
		
		
		
		
		
