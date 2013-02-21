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
This module deals with connecting to a sourceview object in order to determine
all of the languages and their associated styles.
"""

__author__ = "Wesley Hansen"
__date__ = "08/28/2012 11:16:31 PM"

from gi.repository import GtkSource

class SourceviewStyles():
	def __init__(self):
		'''
		styles = {
			{name}: (style_id1, style_id2),
		}
		'''
		self.styles = {}
		self.manager = GtkSource.LanguageManager() # Get the language manager

	def build_styles(self):
		'''
		Builds the styles dictionary.
		'''
		self.styles = {}
		languages = self.manager.get_language_ids()
		for lang in languages:
			style_ids = self.manager.get_language(lang).get_style_ids()
			name = self.manager.get_language(lang).get_name()
			if name == "" or style_ids == []:
				print "Oops, there was something wrong, not adding this language, name: {}, style_ids: {}".format(repr(name), repr(style_ids))
				continue
			self.styles[name] = tuple(style_ids)
		
	def get_styles(self):
		return dict(self.styles)
	
	def get_language_names(self):
		return self.styles.keys()
	
	def get_language(self, lang):
		'''
		Get the style ids associated with `lang` language.
		:param lang: a string, a languages whose style IDs are being requested.
		'''
		if lang not in self.styles.keys():
			raise KeyError("{} is not defined for gtksourceview".format(repr(lang)))
		return self.styles[lang]
				


if __name__ == '__main__':
	import pprint
	my_styles = SourceviewStyles()
	my_styles.build_styles()
	pprint.pprint(my_styles.get_styles())
