#encoding: utf-8
"""
 GThemer MainWindow -- The GUI main window for the GThemer application
 
 This window was designed in GLADE -- "main_window.glade"
"""

__author__ = "Wesley Hansen"
__date__ = "08/31/2012 11:37:55 PM"
__version__  = "0.3"
__status__ = "Prototype"
__application__ = "GThemer" + __version__

import pprint

from gi.repository import Gtk, Gdk, Pango
from lxml import etree

from lib.styles import GThemerRow
from lib.style_generator import StyleGenerator, ParseError
from lib.stylesdb import GThemerDB

__about_dialog__ = "ui/about_dialog.glade"
__about_file__ = "docs/about.txt"

class MainWindow():
	'''
	The main window of GThemer
	'''	
	def __init__(self, ui_file):	
		builder = self.builder = Gtk.Builder()
		builder.add_from_file(ui_file)
		builder.add_from_file(__about_dialog__)
		builder.connect_signals(self)
		self.filename = None

	def initialize_app(self):
		'''
		Load the gui elements from the builder
		'''
		self.window = self.builder.get_object("main_window")
		self.window.set_title(__application__)
		self.window.show_all()
		self.sourceview_styles = GThemerDB('default.db')
		# Generate language_combo
		self.language_combo = self.builder.get_object("language_combo")
		self.language_combo.set_model(None)
		self.build_language_combo()
		self.styles_combo = self.builder.get_object("styles_combo")
		scrolled_window = self.builder.get_object("scrolledwindow")
		self.name_entry = self.builder.get_object("name_entry")
		self.id_entry = self.builder.get_object("id_entry")
		self.author_entry = self.builder.get_object("author_entry")
		self.version_entry = self.builder.get_object("version_entry")
		self.description_entry = self.builder.get_object("description_entry")
		# Create TreeView
		self.styles_treeview = StylesTreeView()
		self.styles_treeview._setup_columns()
		self.styles_treeview.show_all()
		scrolled_window.add(self.styles_treeview)
		# Initialize treemodel
		styles_model = Gtk.TreeStore(str, str, str, str, str, bool, bool, bool, bool, bool)
		self.styles_treeview.set_model(styles_model)
		self.styles_interface = StylesTreeStoreInterface(styles_model, self.sourceview_styles)
		self.styles_treeview.styles = self.styles_interface.styles_rows
		# Setup globals
		self.styles_interface.init_globals()
		
	def open_about_dialog(self, widget):
		'''
		Open the About Dialog.
		'''
		dialog = self.builder.get_object("aboutdialog")
		text_view = self.builder.get_object("about_textview")
		text_buffer = Gtk.TextBuffer()
		text_buffer.set_text(open(__about_file__, 'rb').read())
		text_view.set_buffer(text_buffer)
		dialog.run()
		dialog.destroy()
		
	def open_file_dialog(self):
		'''
		When the filename icon is clicked on, open the file chooser dialog that
		will determine the file.
		'''
		dialog = Gtk.FileChooserDialog(title="Choose a File",
							 	 	   parent=self.window,
							 	 	   action=Gtk.FileChooserAction.SAVE,
							 	 	   buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
							 	 	   			Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
		xml_file_filter = Gtk.FileFilter()
		xml_file_filter.add_pattern("*.xml")
		xml_file_filter.set_name("XML Files")
		dialog.add_filter(xml_file_filter)
		if self.filename is None:
			dialog.set_current_name("Untitled.xml")
			dialog.set_do_overwrite_confirmation(True)
		else:
			dialog.set_current_name(self.filename)
		response = dialog.run()
		if response == Gtk.ResponseType.ACCEPT:
			# Get the file name that is currently in the 
			filename = dialog.get_filename()
			self.window.set_title(__application__ + " - " + filename)
			dialog.destroy()
			return filename
		elif response == Gtk.ResponseType.CANCEL:
			dialog.destroy()
			return None
		else:
			dialog.destroy()
			return None

	def build_language_combo(self, languages=None):
		'''
		Retrieve languages from the SourceviewStyles or from an existing file
		and update the language combo
		'''
		self.language_combo.set_model(None)
		model = Gtk.ListStore(str, str)
		if languages is None:
			# Get languages from SourceviewStyles
			for language in sorted(self.sourceview_styles.iter_languages()):
				model.append([language[1], language[0]])
			self.language_combo.set_model(model)
		else:
			# Get languages extracted from file.
			pass

	def on_language_combo_changed(self, widget):
		'''
		This callback is fired whenever a language is selected from the language
		combo. When a language is selected, the styles associated with that
		language is updated in the styles_combo
		'''
		current_language = self.language_combo.get_model()[self.language_combo.get_active_iter()][1]
		if current_language not in [x[0] for x in self.sourceview_styles.iter_languages()]:
			print("Error! {} is NOT defined in SourceviewStyles".format(repr(current_language)))
		else:
			self.styles_combo.remove_all()
			styles = self.sourceview_styles.iter_styles(language=current_language)
			for style in sorted(styles):
				self.styles_combo.append_text(str(style['style']))

	def add_group(self, widget):
		'''
		When the Add Lang button is clicked, add all the definitions for 
		the chosen language to the StylesTreeView if they don't exist
		'''
		model = self.language_combo.get_model()
		current_iter = self.language_combo.get_active_iter()
		lang_title = model[current_iter][0]
		lang_name = model[current_iter][1]
		self.styles_interface.add_group(lang_name,
										lang_title,
										sorted(name['style'] for name in self.sourceview_styles.iter_styles(lang_name)))

	def add_style(self, widget):
		'''
		When the Add Style button is clicked, add the selected definition to
		the StylesTreeView if the definition isn't already in the TreeView.
		'''
		model = self.language_combo.get_model()
		lang = model[self.language_combo.get_active_iter()][0]
		style = self.styles_combo.get_active_text()
		self.styles_interface.add_style(lang, style)

	def on_delete_event(self, widget, event):
		Gtk.main_quit()

	def on_quit(self, widget):
		'''
		Exit the application when Quit button is pressed
		'''
		self.window.destroy()
		Gtk.main_quit()

	def load_file(self, widget, data=None):
		'''
		This callback is fired when the "Open" Gtk.MenuItem is activated. This
		method opens a filechooser dialog to choose an xml file and then load
		its contents into the treeview.
		'''
		dialog = Gtk.FileChooserDialog(title=None,
							 	 	   parent=None,
							 	 	   action=Gtk.FileChooserAction.OPEN,
							 	 	   buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
							 	 	   			Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
		xml_file_filter = Gtk.FileFilter()
		xml_file_filter.add_pattern("*.xml")
		xml_file_filter.set_name("XML Files")
		dialog.add_filter(xml_file_filter)
		response = dialog.run()
		if response == Gtk.ResponseType.ACCEPT:
			filename = dialog.get_filename()
			print("Opening file: {}".format(filename))
			dialog.destroy()
			generator = StyleGenerator()
			try:
				info, styles = generator.parse_file(filename, self.sourceview_styles)
			except ParseError:
				traceback.print_exc()
				# Open a dialog that says it failed to parse.
				return
			except Exception as e:
				traceback.print_exc()
				# Open a dialog that says it failed to parse.
				return
			# Set the info pane
			#self.filename_entry.set_text(filename)
			self.window.set_title(__application__ + " - " + filename)
			self.name_entry.set_text(info['name'])
			self.id_entry.set_text(info['id'])
			self.author_entry.set_text(info['author'])
			self.version_entry.set_text(info['version'])
			self.description_entry.set_text(info['description'])
			self.styles_interface.treestore.clear()
			self.styles_interface.styles_rows = {}
			# Set styles
			for lang, config in sorted(styles.iteritems()):
				if lang == '__globals':
					# Add globals to the StylesTreeView
					for scheme, conf in config.iteritems():
						row = self.format_row(conf, scheme)
						config[scheme] = row
					self.styles_interface.init_globals(globals_defaults=config)
				else:
					language = config['name']
					styles = config['styles']
					for scheme, style in styles.iteritems():
						row = self.format_row(style, scheme)
						self.styles_interface.add_style(language, scheme, row)
		else:
			dialog.destroy()

	def format_row(self, config, scheme):
		'''
		Format values for use in the StylesTreeView.
		
		*config* (``dict``) of attributes to set.
		'''
		color_cols = {
			'background': 'background_display',
			'foreground': 'foreground_display',
		}
		bool_cols = ('italic', 'bold', 'underline', 'strikethrough')
		markup_cols = ('background', 'foreground') + bool_cols
		new_config = {}
		for col_name, col_value in config.iteritems():
			if col_name in bool_cols:
				new_config[col_name] = True if col_value.lower() == 'true' else False
		
			elif col_name in color_cols:
				text = config[col_name]
				display_text = '<span background="{text}">{text}</span>'.format(text=text) if text else ""
				new_config[color_cols[col_name]] = display_text
				new_config[col_name + "_data"] = text
		new_keys = {}
		for key, value in new_config.iteritems():
			new_keys[key] = value
		markup = "<span"
		if new_keys['foreground_data'] not in (None, ""):
			markup += ' foreground="{}" '.format(new_keys['foreground_data'])
		if new_keys['background_data'] not in (None, ""):
			markup += ' background="{}" '.format(new_keys['background_data'])
		if new_keys['bold'] == True:
			markup += ' weight="bold" '
		if new_keys['italic'] == True:
			markup += ' style="italic" '
		if new_keys['underline'] == True:
			markup += ' underline="single" '
		if new_keys['strikethrough'] == True:
			markup += ' strikethrough="true" '
		markup += ">{}</span>".format(scheme)
		new_keys['definition'] = markup	
		return new_keys

	def on_new(self, widget):
		'''
		When the "New" button is pressed, clear the current contents of the
		application.
		'''
		self.styles_interface.styles_rows = {}
		self.styles_interface.treestore.clear()
		self.filename = None
		self.styles_interface.init_globals()
		self.window.set_title(__application__)
		self.name_entry.set_text("")
		self.id_entry.set_text("")
		self.author_entry.set_text("")
		self.description_entry.set_text("")

	def on_save(self, widget):
		'''
		When the save button is pressed, a filechooser dialog is created, asking
		the user to choose a file. That file is overwritten with the new information.
		'''
		if self.filename:
			self._save_file()
		else:
			self.on_save_as(widget)

	def on_save_as(self, widget):
		'''
		When that save as button is pressed, a filechooser dialog is created, asking
		the user to choose a filename to save the theme to. That file is overwritten
		with the new information.
		'''
		filename = self.open_file_dialog()
		if filename:
			self.filename = filename
			self._save_file()

	def _save_file(self):
		'''
		Save the theme to the current filepath in `self.filename`
		'''
		# Build the styles dict based on the styles that are laid out in the
		# StylesTreeView.
		styles_object = self.styles_interface.treestore
		generator = StyleGenerator()
		info = self. get_info()
		generator.add_info(info['id'], info['name'], 
						   author=info['author'],
						   description=info['description'],
						   version=info['version'])	
		generator.add_styles(styles_object)
		print etree.tostring(generator.tree.getroot(), pretty_print=True)
		generator.save_file(info['filename'])

	def get_info(self):
		'''
		Get text from the textboxes. Returns a dict of all the values
		info_dict = {
			'filename': '',
			'name': '',
			'id': '',
			'author': '',
			'version': '',
			'description': '',			
		}
		'''
		info_dict = {}
		info_dict['filename'] = self.filename
		info_dict['name'] = self.name_entry.get_text()
		info_dict['id'] = self.id_entry.get_text()
		info_dict['author'] = self.author_entry.get_text()
		info_dict['version'] = self.version_entry.get_text()
		info_dict['description'] = self.description_entry.get_text()
		return info_dict

class StylesTreeStoreInterface():
	'''
	This class handles manipulating the TreeStore, adding and deleting styles
	and languages to the TreeStore.
	'''
	
	# style_rows - mapping of style schemes to the GtkIter they belong to.
	styles_rows = {}
	
	def __init__(self, treestore, styles):
		'''
		*treestore* (``Gtk.TreeStore``) that will contain the data
		
		*styles* (``GThemerDB``) is the GThemerDB reference.
		'''
		self.treestore = treestore
		self.styles = styles

	def init_globals(self, globals_defaults={}):
		'''
		Initialize the globals styles in the treestore
		
		*globals_defaults* (``dict``) is optional defaults to give the globals.
		'''
		self.global_styles = sorted([glob for glob in self.styles.iter_globals()], key=lambda x: x['scheme'])
		if '__globals' in self.styles_rows:
			child_iter = self.treestore.iter_children(self.styles_rows['__globals'])
			# Clear global's children
			remove = True
			while remove != False:
				remove = self.treestore.remove(child_iter)
		else:
			default_row = GThemerRow()
			default_row['definition'] = "Global gedit Settings"
			global_iter = self.treestore.append(None, default_row.get_row())
			self.styles_rows['__globals'] = global_iter
		
		# Add new iters
		for style in self.global_styles:
			row = globals_defaults.get(style['scheme'], {})
			global_row = GThemerRow(**row)
			global_row['definition'] = style['scheme'] if row == {} else global_row['definition']
			self.treestore.append(self.styles_rows['__globals'], global_row.get_row())
	
	def add_group(self, lang_name, lang_title, styles):
		'''
		Adds an entire language group of definitions to the TreeStore. If one
		of the languages already exist in the structure
		'''	
		if lang_title not in self.styles_rows:
			# A new language is being added to the TreeStore
			# First get the reference to the new language's GtkIter and
			# add it to self.styles.
			
			# language_row -- this row is only comprised of the language name
			language_row = GThemerRow()
			language_row['definition'] = lang_title
			# New iter reference to the language
			new_iter = self.treestore.append(None, language_row.get_row())
			self.styles_rows[lang_title] = new_iter

		# Append the data to the new row.
		for defn in sorted(styles):
			if not self.in_treestore(self.styles_rows[lang_title], defn):
				default_row = GThemerRow()
				default_row['definition'] = defn
				self.treestore.append(self.styles_rows[lang_title], default_row.get_row())

	def add_style(self, lang, style, row=None):
		'''
		Add a style definition to a language group if the style definition isn't
		already in the group.
		
		*lang* (``str``) is the language to add the style to.
		
		*style* (``str``) is the name of the style to add.
		
		*row* (``dict``) is optional attributes to set on the row. ``None`` by
			default to represent the default row
		'''
		lang_iter = None
		if lang not in self.styles_rows:
			language_row = GThemerRow()
			language_row['definition'] = lang
			#New iter reference to the language
			new_iter = self.treestore.append(None, language_row.get_row())
			self.styles_rows[lang] = new_iter
			lang_iter = new_iter
		else:
			lang_iter = self.styles_rows[lang]

		if not self.in_treestore(lang_iter, style):
			row = {} if row is None else row
			default_row = GThemerRow(**row)
			default_row['definition'] = style if row == {} else default_row['definition']
			self.treestore.append(self.styles_rows[lang], default_row.get_row())

	def in_treestore(self, lang_iter, definition):
		'''
		Returns True if definition is defined in treestore, False if it isn't
		'''
		child_iter = self.treestore.iter_children(lang_iter)
		while child_iter != None:
			_, __, treestore_text, ___ = Pango.parse_markup(self.treestore[child_iter][0], len(self.treestore[child_iter][0]), "\0")
			if treestore_text == definition:
				return True
			child_iter = self.treestore.iter_next(child_iter)
		return False

	def get_styles(self):
		'''
		Generate a *styles dict* based on the information that's in the
		treestore.
		
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
		'''
		styles = {}
		for language, style_iter in self.styles.iteritems():
			used_styles = {}
			child_iter = self.treestore.iter_children(style_iter)
			while child_iter is not None:
				style_name, lang_style = self.generate_lang_style(self.treestore[child_iter][:])
				used_styles[style_name] = lang_style
				child_iter = self.treestore.iter_next(child_iter)
			styles[language] = used_styles
		return styles

				
class StylesTreeView(Gtk.TreeView):
	'''
	TreeView that displays styles. Styles will contain 7 columns:
	Definition, Foreground, Background, Bold, Italic, Underline, Strikethrough	
	'''
	column_names = ('Definition', 'Foreground', 'Background', 'Bold', 'Italic', 'Underline', 'Strikethrough')
	color_cols = ('Foreground', 'Background')
	pixbuf_cols = ('Bold', 'Italic', 'Underline', 'Strikethrough')
	
	row_skeleton = GThemerRow()

	def __init__(self):
		Gtk.TreeView.__init__(self)
		self.set_hover_selection(True)
		self.set_grid_lines(True)
	
	def _setup_columns(self):
		'''
		Initialize columns and add to treeview.
		'''
		for idx, name in enumerate(self.column_names):				
			column = Gtk.TreeViewColumn(name)
			if name in self.color_cols:
				# Setup the color columns
				renderer = Gtk.CellRendererText()
				column.pack_start(renderer, False)
				column.add_attribute(renderer, 'markup', self.row_skeleton.index_of(name.lower()+"_display"))
			elif name in self.pixbuf_cols:
				# Setup the pixbuf cols
				renderer = Gtk.CellRendererPixbuf()
				renderer.set_property('stock-id', Gtk.STOCK_APPLY)
				column.pack_start(renderer, False)
				column.add_attribute(renderer, 'visible', self.row_skeleton.index_of(name.lower()))
			else:
				# Setup default column(just a simple CellRendererText)
				renderer = Gtk.CellRendererText()
				column.pack_start(renderer, False)
				column.add_attribute(renderer, 'markup', self.row_skeleton.index_of(name.lower()))

			column.index = idx # Save the index so we know which column to set in the model
			if idx != 0:
				column.set_property('expand', True)
				#renderer.connect('edited', self.on_cell_changed, idx)
				
			else:
				column.set_min_width(250)
				column.set_property('resizable', True)
				
			self.append_column(column)
		self.connect('button-press-event', self.on_button_press_event)
	
	def on_cell_changed(self, widget, path, text, column):
		print "path: {}, text: {}".format(path, text)
		treestore = self.get_model()
		treestore.set_value(treestore.get_iter(path), column, text)

	def on_button_press_event(self, treeview, event):
		'''
		Detect the path that was clicked on to open a color chooser dialog
		to fill the path with the color that was chosen.
		'''
		color_chooser_columns = ('Foreground', 'Background')
		bool_columns = ('Bold', 'Italic', 'Underline', 'Strikethrough')
		if event.button == 1: # Left click
			return_val  = treeview.get_path_at_pos(int(event.x), int(event.y))
			if return_val is not None:
				path, col, x, y = return_val
				model = treeview.get_model()
				if model.iter_parent(model.get_iter(path)) is not None:
					self.handle_click(path, col)
		elif event.button == 3: # Right click -- menus
			return_val = treeview.get_path_at_pos(int(event.x), int(event.y))
			if return_val is not None:
				path, col, x, y = return_val
				model = treeview.get_model()
				if model.iter_parent(model.get_iter(path)) is None:
					self.popup = None
					# A language was clicked on, open language menu.
					if model[path][0] == "Global gedit Settings":
						# Special global popup menu
						globl = True
					else:
						globl = False
					self.popup = self.create_lang_popup_menu(model, path, is_global=globl)
					self.popup.popup(None, None, None, None, event.button, event.time)
				else:
					self.popup = None
					# A style was clicked on, open style menu
					if model[model.iter_parent(model.get_iter(path))][0] == "Global gedit Settings":
						globl = True
					else:
						globl = False
					self.popup = self.create_styles_popup_menu(model, path, is_global=globl)
					self.popup.popup(None, None, None, None, event.button, event.time)

	def create_styles_popup_menu(self, model, path, is_global=None):
		'''
		Create a popup menu for Styles controls.
		'''
		style = model[path][0]
		_, __, style_text, ___ = Pango.parse_markup(style, len(style), "\0")
		menu = self.popup = Gtk.Menu()
		if not is_global:
			menuitem1 = Gtk.MenuItem("Delete {}".format(repr(style_text)))
			menuitem1.connect('activate', self.delete_style, model, path)
			menu.append(menuitem1)
		menuitem2 = Gtk.MenuItem("Clear {}".format(repr(style_text)))
		menuitem2.connect('activate', self.clear_style, model, path)
		menu.append(menuitem2)
		menu.show_all()
		return menu

	def create_lang_popup_menu(self, model, path, is_global=None):
		'''
		Create a popup menu for Language controls.
		'''
		language = model[path][0]
		menu = self.popup = Gtk.Menu()
		if not is_global:
			menuitem1 = Gtk.MenuItem("Delete {}".format(repr(language)))
			menuitem1.connect('activate', self.delete_language, model, path)
			menu.append(menuitem1)
		menuitem2 = Gtk.MenuItem("Clear All {} styles".format(repr(language)))
		menuitem2.connect('activate', self.clear_styles, model, path)
		menu.append(menuitem2)
		menu.show_all()
		return menu

	def delete_style(self, widget, model, path):
		'''
		Delete style at ``path``
		'''
		del model[path]

	def clear_style(self, widget, model, path):
		'''
		Clear style at ``path``
		'''
		style = model[path][0]
		_, __, style_text, ___ = Pango.parse_markup(style, len(style), "\0")
		default_row = GThemerRow()
		default_row['definition'] = style_text
		for i in xrange(len(default_row)):
			model[path][i] = default_row.get_row()[i]

	def delete_language(self, widget, model, path):
		'''
		Delete ``language`` from model, including all styles defined for that 
		language.
		'''
		language = model[path][0]
		del model[path]
		del self.styles[language]

	def clear_styles(self, widget, model, path):
		'''
		Clear all styles associated with ``language``.
		'''
		path = model.get_iter(path)
		child_iter = model.iter_children(path)
		while child_iter is not None:
			self.clear_style(None, model, child_iter)
			child_iter = model.iter_next(child_iter)			

	def handle_click(self, path, col):
		'''
		When a column is left clicked, it will perform an action based on the
		column name. This function handles calling the particular action.
		'''
		model = self.get_model()
		change_made = False
		if col.get_title() in self.color_cols:
			# Open a color chooser
			dialog = Gtk.ColorChooserDialog("Select a color")
			response = dialog.run()
			if response == Gtk.ResponseType.OK:
				# Create a color object
				select_color = Gdk.RGBA()
				# Get the rgba color and set it in the color object
				dialog.get_rgba(select_color)
				# Okay, we go the color, so now it's time to set the appropriate
				# cell in the TreeModel
				color_string = rgba_to_hex(select_color)
				model[path][self.row_skeleton.index_of(col.get_title().lower() + '_data')] = color_string
				model[path][self.row_skeleton.index_of(col.get_title().lower() + '_display')] = '<span background="{col}" foreground="{readable}">{col}</span>'.format(col=color_string, readable=get_readable_color(select_color))
				change_made = True
				
			elif response == Gtk.ResponseType.CANCEL:
				# Do Nothing
				pass
			dialog.destroy()

		elif col.get_title() in self.pixbuf_cols:
			# Toggle the image-set property
			# First, determine the current value
			current_value = model[path][self.row_skeleton.index_of(col.get_title().lower())] 
			model[path][self.row_skeleton.index_of(col.get_title().lower())] = not current_value
			change_made = True
		
		# A change is made to the row, so 
		if change_made == True:
			# Save row settings to the tree model
			row = GThemerRow(*[i for i in model[path]])
			self.apply_row_settings(row, path, model)

	def apply_row_settings(self, row, path, model):
		'''
		Applies all of the settings that have been applied to the given row_iter
		onto the first column.
		'''
		row_text = row['definition']
		_, __, plain_text, ___ = Pango.parse_markup(row_text, len(row_text), "\0")
		markup = "<span"
		if row['foreground_data'] not in (None, ""):
			markup += ' foreground="{}" '.format(row['foreground_data'])
		if row['background_data'] not in (None, ""):
			markup += ' background="{}" '.format(row['background_data'])
		if row['bold'] == True:
			markup += ' weight="bold" '
		if row['italic'] == True:
			markup += ' style="italic" '
		if row['underline'] == True:
			markup += ' underline="single" '
		if row['strikethrough'] == True:
			markup += ' strikethrough="true" '
		
		markup += ">{}</span>".format(plain_text)
		row['definition'] = markup
		model[path] = row.get_row()
		

def get_readable_color(color):
	'''
	Takes a Gdk.RGBA and determines an appropriate 'readable' color for the text.
	Returns the hexadecimal string for this color.
	'''
	# TODO : implement this...it should detect if it's a light color and so it
	# will return black and if the given color is a "dark" color this function
	# will return white in order for the background/foreground mix to be human
	# readable.
	return "black"

def rgba_to_hex(color):
    """
    Get hexadecimal string for :class:`Gdk.RGBA` `color`.
    
    *color* (``Gdk.RGBA``) is the color to format to a hexstring
    
    Returns (``str``) the hex string.
    """
    return "#{0:02x}{1:02x}{2:02x}".format(int(color.red   * 255),
                                           int(color.green * 255),
                                           int(color.blue  * 255))		
		
if __name__ == "__main__":
	window = MainWindow()
	window.initialize_app()
	Gtk.main()	
