=======
GThemer
=======

What this project is about
==========================
	I want an application kinda like `badschemer` that provides a GUI to help
	create a custom theme for syntax highlighting in gedit. But I was never very
	happy with badschemer's interface, so I've decided to make my interface.
	
Ideas for my interface
======================
	Since this is all about colors and such, I like the idea of having many
	color_buttons to choose the color(or maybe I'll put it in a treeview).
	But I really think it's necessary to create a little sample window that will
	let you show the user what their current setup looks like(on-the-fly).

	Language selectors - choose which languages they want to create themes for.
	Autofill in the languages - Basically if you create just one language, there
	should be an option for themes to be created based on the colors you chose for
	the one language.

What I know so far about gtksourceview
======================================
	I know that all of the themes and language definitions are defined by xml
	files. So I'll have to create an api that will build an xml file following
	the style scheme definition reference.
	
	Update: From the looks of it, a programming language is defined in a .lang
	file. This appears to be an xml file that defines the styles that are
	associated with the language.
	But, it looks like I may be able to use gtksourceview api to get all the
	available languages and their styles...woot!



Links
=====
http://developer.gnome.org/gtksourceview/stable/style-reference.html
http://developer.gnome.org/gtksourceview/stable/lang-tutorial.html


