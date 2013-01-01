#encoding: utf-8
"""
Build the xml file that contains the styles structure necessary for defining
syntax highlighting formats for gtksourceview

This is a sample for how the styles data structure will look that needs to be
converted into xml
styles = {

	'Python':{
		'python:keyword': {
			'foreground': '',
			'background': '',
			'bold': False,
			'italic': False,
			'underline': False,
			'strikethrough': False,
		}
	}
}

This is what the xml will look like for the above structure:

<style-scheme id="Wes2" _name="Wes-Black/Green" version="1.0">
	<author>Wesley Hansen</author>
	<_description>Black background with green text</_description>
	<style name="python:keyword" foreground="#00A72F" background="#454343" bold="False" italic="False" underline="False" strikethrough="False"/>
</style-scheme>


"""

__author__ = "Wesley Hansen"
__date__ = "08/29/2012 09:31:38 PM"
__version__ = "0.1"
__status__ = "Prototype"

import os
import pprint

from lxml import etree
from gi.repository import Pango, Gtk

from lib.styles import GThemerRow

class ParseError(Exception):
	'''
	This exception is raised when an xml can't be parsed.
	'''


class StyleGenerator():
	'''
	Converts a treestore to the a style-schemes xml.
	'''

	style_columns = {
		'definition': 'name',
		'foreground_data': 'foreground',
		'background_data': 'background',
		'bold': 'bold',
		'italic': 'italic',
		'underline': 'underline',
		'strikethrough': 'strikethrough'
	}
	
	def __init__(self):
		root = etree.Element("style-scheme")
		self.tree=etree.ElementTree( root )

	def parse_file(self, filename, db):
		'''
		Opens an existing xml scheme file.
		
		*filename* (``str``) xml styles-scheme filepath.
		*db* (``GThemerDB``) is a reference to the database that
			contains all the styles nad 
		'''
		styles = {}
		tree = etree.parse(open(filename, 'rb'))
		# Retrieve file info.
		root = tree.xpath('//style-scheme')
		if root is None:
			raise ParseError("'style-scheme' tag not found.")
		root = root[0]
		_id = root.get('id')
		name = root.get('_name')
		version = root.get('version')
		author_node = tree.xpath('//author')
		author = None
		if author_node is not None:
			author = author_node[0].text
		descrip_node = tree.xpath('//_description')
		descrip = None
		if descrip_node is not None:
			descrip = descrip_node[0].text
		
		info = {
			'id': _id or '',
			'name': name or '',
			'version': version or '',
			'author': author or '',
			'description': descrip or '',
		}
		
		# Determine available styles from db
		print("Retrieving database information...")
		global_styles = [glob['scheme'] for glob in db.iter_globals()]
		style_languages = {style[0]: style[1] for style in db.iter_languages()}
		for scheme, title in style_languages.iteritems():
			styles.update(
				{
					scheme:{
						'name': title,
						'styles': {}
					}
				}
			)
		styles['__globals'] = {}
		# Parse the file
		print("Beginning iterparse of 'style' tags...")
		columns = ('name', 'foreground', 'background', 'italic', 'bold', 'underline', 'strikethrough')

		for event, element in etree.iterparse(open(filename, 'rb'), tag='style'):
			if event == 'end':
				scheme_name = element.get('name')
				update_row = {col_name: element.get(col_name) for col_name in columns}
				if ":" in element.get('name'):
					# This element is assigned to a language
					scheme = scheme_name.split(':')[0]
					style_scheme = styles.get(scheme, {'name': style_languages.get(scheme, scheme),'styles':{}})
					style_scheme['styles'].update({scheme_name: update_row})
					styles.update({scheme: style_scheme})
				else:
					# This is a global...update the global struct
					styles['__globals'].update({scheme_name: update_row})

		new_styles = {}
		for style, config in styles.iteritems():
			if style == "__globals":
				new_styles[style] = config
			else:
				if config['styles'] != {}:
					new_styles[style] = config
		styles = new_styles
				
				
		return info, styles					
		
	def add_info(self, scheme_id, name, author=None, description=None, version=None):
		'''
		Add info about the style...like name, description, author
		'''
		root = self.tree.getroot()
		root.set('id', scheme_id)
		root.set('_name', name)
		if version is None:
			raise ValueError('Version is required!')
		root.set('version', version)
		if author is not None:
			author_node = etree.SubElement(root, 'author')
			author_node.text = author
		if description is not None:
			description_node = etree.SubElement(root, '_description')
			description_node.text = description
		
	def add_styles(self, styles):
		'''
		Add styles nodes to the tree
		'''
		assert self.tree is not None, "lxml.etree hasn't been set"

		root = self.tree.getroot()
		defn_iter = styles.iter_children(None)
		while defn_iter is not None:
			lang = GThemerRow(*[style for style in styles[defn_iter]])
			print "Lang: {}".format(lang.get_row())
			if lang['definition'] == 'Global gedit Settings':
				# Handle globals
				child_iter = styles.iter_children(defn_iter)
				while child_iter is not None:
					child = GThemerRow(*[style for style in styles[child_iter]])
					print("Global child: {}".format(child.get_row()))
					if not all(item is None for item in child):
						element = etree.Element('style')
						for row, column in self.style_columns.iteritems():
							attr = str(child[row]) if isinstance(child[row], bool) else child[row]
							if column == 'name':
								_, __, attr, ___ = Pango.parse_markup(child[row], len(child[row]), "\0")
							if attr is not None:
								element.set(column, attr)
						root.append(element)
					else:
						print("Oops, this row is empty for lang: {}. {}".format(lang['definition'], child.get_row() ))
					child_iter = styles.iter_next(child_iter)
			else:
				# Handle everything else.
				child_iter = styles.iter_children(defn_iter)
				while child_iter is not None:
					child = GThemerRow(*styles[child_iter])
					print("Child: {}".format(child.get_row()))
					if not all(item is None for item in child):
						element = etree.Element('style')
						for row, column in self.style_columns.iteritems():
							attr = str(child[row]) if isinstance(child[row], bool) else child[row]
							if column == 'name':
								_, __, attr, ___ = Pango.parse_markup(child[row], len(child[row]), "\0")
							if attr is not None:
								element.set(column, attr)
						root.append(element)
					else:
						print("Oops, this row is empty for lang: {}. {}".format(lang['definition'], child.get_row() ))
					child_iter = styles.iter_next(child_iter)
			defn_iter = styles.iter_next(defn_iter)

	def save_file(self, filename):
		'''
		Save the etree to file.
		'''
		assert self.tree is not None, "lxml.etree hasn't been set"
		string = etree.tostring(self.tree, pretty_print=True)
		with open(filename, 'w') as fp:
			fp.write(string)
		
if __name__ == '__main__':
	generator = StyleGenerator()
	generator.add_info("1001", "Wes' Test Theme", author="Wesley Hansen", description="Just testing my API")	
	styles = {
		'Python': {
			'python:keyword': {
				'foreground': '#161616',
				'background': '#38FF6F',
				'bold': False,
				'italic': False,
				'underline': False,
				'strikethrough': False,
			},
			'python:declaration': {
				'foreground': 'green',
			}
		}	
	}
	
	generator.add_styles(styles)
	
	print etree.tostring(generator.tree.getroot(), pretty_print=True)
	generator.save_file('test1.xml')
	
	
	
	
	
	
		

