#encoding: utf-8
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
This module contains the underlying data structure that is used convert between
theme styles xml file and the gthemer application. This structure will contain
an API that makes it easy to interact with the data structure.
"""

__author__ = "Wesley Hansen"
__date__ = "11/03/2012 07:17:14 PM"
__version__ = "0.1"
__status__ = "Prototype"

import pprint

from gi.repository import GtkSource
from lxml import etree

class GThemerStyles:
	'''
	Underlying data structure used by GThemer to create a custom theme (xml file)
	'''
	# global_styles - List of all appropriate global styles keys that can
	# exist in the current GtkSourceView styles definition. Currently I can't
	# figure out how to retrieve these values using the pygobject api...
	# so this list will have to be static. GRR.
	global_styles = ('text', 'selection', 'selection-unfocused', 'cursor',
	'cursor-secondary', 'current-line', 'line-numbers', 'draw-spaces', 'bracket-match',
	'bracket-mismatch', 'right-margin', 'search-match')
	
	# style_attrs - List of all style attributes that can be applied to a language
	# style. This applies to both global and language styles.
	style_attrs = ('foreground', 'background', 'italic', 'bold', 'underline', 'strikethrough')
	
	# globals_key - The key at which the globals styles are located in the styles structure
	globals_key = "__globals"
	
	def __init__(self):
		'''
		Retrieve the languages and ids from the GtkSource, and build the initial
		shape of the data structure.
		'''
		self.styles = {}
		self.author = ""
		self.name = ""
		self.scheme_id = ""
		self.version = "1.0"
		self.description = ""
		self._init_styles()
		self._init_globals()
		self.language_map = dict(zip([lang.get('name', blah) for blah, lang in self.styles.iteritems()],[lang for lang in self.styles]))
		
		pprint.pprint(self.styles)
		
	def _init_globals(self):
		'''
		Add the globals config structure to the underlying data structure.
		'''
		self.styles[self.globals_key] = {}
		for style in self.global_styles:
			global_style = {attr: None for attr in self.style_attrs}
			self.styles[self.globals_key].update({style:global_style})
		
	def _init_styles(self):
		'''
		Determine the available languages and styles from GtkSource language manager
		and build the initial underlying data structure
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
			style_dict = None
			for style in style_ids:
				#print("Scheme: {}".format(style))
				style_dict = {attr:None for attr in self.style_attrs}
				lang_config[style] = style_dict
			self.styles[lang] = {
				'styles': lang_config,
				'name': name,
				'scheme': lang,
			}

	def set_style(self, language, style_name, style_config):
		'''
		Update a language with style options.
		
		*language* (``str``) is the name of a language you want to
		change the style of.
		
		*style_name* (``str``) is the name of the style you're setting.
		
		*style_config* (``dicdett``) is a dictionary of formatting options:
		
			*foreground* (``str``) is the foreground color of the text.
			
			*background* (``str``) is the background color of the text.
			
			*underline* (``bool``) if the text is underlined or not.
			
			*strikethrough* (``bool``) if the text is strikethrough or not.
			
			*italic* (``bool`) if the text is italicized or not.
			
			*bold* (``bool``) if the text is bolded or not.
		'''
		if language not in self.styles:
			raise LanguageUndefinedError("{} is not defined!".format(repr(lanugage)))
		if style_name not in self.styles[language]['styles'].keys():
			raise StyleUndefinedError("style: {} is not defined for language: {}!".format(repr(style_name), repr(language)))
		self.styles[language]['styles'][style_name].update(style_config)

	def get_styles(self, language):
		'''
		Get styles config for a given language
		'''
		if language not in self.styles:
			raise LanguageUndefinedError("{} is not defined!".format(repr(language)))
		return self.styles[language]

	def get_style(self, language, style_name):
		'''
		Retrieve style information for a particular language.
		
		*language* (``str``) is the name of a language you to retrieve a style
		from.
		
		*style_name* (``str``) is the name of the style you're retrieving.
		'''
		if language not in self.styles:
			raise LanguageUndefinedError("{} is not defined!".format(repr(lanugage)))
		if style_name not in self.styles[language]['styles'].keys():
			raise StyleUndefinedError("style: {} is not defined for language: {}!".format(repr(style_name), repr(language)))
		return dict(self.styles[language]['styles'][style_name])
	
	def set_global_styles(self, style_name, style_config):
		'''
		Update the global styles.
		
		*style_name* (``str``) is the name of the style you're setting.
		
		*style_config* (``dict``) is a dictionary of formatting options:
		
			*foreground* (``str``) is the foreground color of the text.
			
			*background* (``str``) is the background color of the text.
			
			*underline* (``bool``) if the text is underlined or not.
			
			*strikethrough* (``bool``) if the text is strikethrough or not.
			
			*italic* (``bool`) if the text is italicized or not.
			
			*bold* (``bool``) if the text is bolded or not.
		'''
		if style_name not in self.styles[self.globals_key]:
			raise StyleUndefinedError("style: {} is not defined!".format(repr(style_name)))
		self.styles[self.globals_key].update({style_name: style_config})
	
	def get_global_styles(self, global_style):
		'''
		Retrieve global style information for a certain global *global_style*
		
		*global_style* (``str``) is a global style name.
		'''
		if global_style not in self.styles[self.globals_key]:
			raise
		return dict(self.styles[self.globals_key][global_style])

	def iter_styles(self):
		'''
		Get each style config.
		
		Yields *style_config* (``dict``) 
		'''
		for language, style_config in self.styles.iteritems():
			if language == self.globals_key:
				continue
			yield style_config

	def iter_globals(self):
		'''
		Get each globals style config.
		
		Yields *styles_config* (``dict``)
		'''
		for global_name, style_config in self.styles[self.globals_key].iteritems():
			yield style_config

	def iter_global_names(self):
		for global_name, _ in self.styles[self.globals_key].iteritems():
			yield global_name

	def iter_language_names(self):
		'''
		Retrieve the title/name of each language in the styles dict
		'''
		for language, config in self.styles.iteritems():
			if language == self.globals_key:
				continue
			yield config['name']

	def write_to_file(self, filename):
		'''
		Write the styles structure in xml format to file *filename*.
		
		*filename* (``str``) is a filepath to write the xml structure to.
		'''
		root = etree.Element("style-scheme")
		tree = etree.ElementTree(root)
		
		# Set root attributes.
		root.set('id', self.scheme_id)
		root.set('_name', self.name)
		root.set('author', self.author)
		root.set('version', self.version)
		root.set('description', self.description)
		
		# Set styles.
		for language, style in self.styles.iteritems():
			for style_name, style_config in style.iteritems():
				if all(lang_style is None for lang_style in style_config['styles']):
					continue
				element = etree.Element('style')
				element.set('name', style_name)
				for attr, value in definition.iteritems():
					element.set(attr, str(value))
				root.append(element)
		
		# Save file.		
		self.tree.write(filename, pretty_print=True)

class GThemerRow:
	'''
	A data structure used to transfer data between the GThemerStyles data structure
	and the GtkTreeView's TreeModel.
	'''
	
	row_keys = ('definition', 'foreground_data', 'foreground_display',
	            'background_data', 'background_display', 'bold', 'italic',
	            'underline', 'strikethrough', 'editable')

	str_keys = ('definition', 'foreground_data', 'foreground_display',
	            'background_data', 'background_display')

	bool_keys = ('bold', 'italic', 'underline', 'strikethrough', 'editable')
		
	def __init__(self, *args, **kwargs):
		'''
		Create a new GThemerRow
		'''
		if args and kwargs:
			raise InvalidArgsError("positional and keyword arguments passed, only one may be passed at a time!")

		# row_dict - The underlying dictionary
		self.row_dict = {}
		
		if args:
			if len(args) != len(self.row_keys):
				raise InvalidArgsLengthError("Args length[{}] != {}".format(len(args), len(self.row_keys)))
			self.row_dict = {key:args[idx] for idx, key in enumerate(self.row_keys)}
		elif kwargs:
			self.row_dict = {key:kwargs.get(key, None) for key in self.row_keys}
		else:
			self.row_dict = {key:'' if key in self.str_keys else False for key in self.row_keys}

	def __iter__(self):
		for item in self.get_row():
			yield item
			
	def __setitem__(self, key, value):
		if key not in self.row_keys:
			raise KeyError("{} is not a valid key in GThemerRow.".format(repr(key)))
		self.row_dict[key] = value

	def __getitem__(self, key):
		return self.row_dict[key]

	def __len__(self):
		return len(self.row_keys)
	
	def get_row(self):
		'''
		Returns the row as a list
		'''
		return [self.row_dict[key] for key in self.row_keys]

	def get_row_dict(self):
		return dict(self.row_dict)

	def index_of(self, column):
		return list(self.row_keys).index(column)

		
		
class LanguageUndefinedError(Exception):
	'''
	This ``Exception`` is raised when attempting to retrieve a style for a particular
	language and that language is not defined in the styles structure.
	'''


class StyleUndefinedError(Exception):
	'''
	This ``Exception`` is raised when attempting to retrieve a style config for 
	a particular language and that language is not defined in the styles structure.
	'''


class InvalidArgsError(Exception):
	'''
	This ``Exception`` is raised when a GThemerRow is initialized and both
	positional and keyword arguments are passed to the constructor.
	'''	
	
	
class InvalidArgsLengthError(Exception):
	'''
	This ``Exception`` is raised when a GThemerRow is initialized with a 
	'''
	
	
if __name__ == '__main__':
	styles = GThemerStyles()
		
	
