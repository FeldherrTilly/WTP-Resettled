## WTP: the colors of the import / export and raw material states in one place (the import / export window, its tooltips and the lines of
## the tooltips that name them). A group is a tuple (red, green, blue, alpha); tag() puts a text in it for the text of the game.

RAW_MISSING = (255, 0, 0, 255) # raw materials missing, output reduced
RAW_SCARCE = (255, 140, 0, 255) # raw materials scarce, import needed
RAW_IMPORT_SET = (255, 200, 110, 255) # raw material import set
IMPORT = RAW_IMPORT_SET # the import (the same light orange as "import set")
EXPORT = (255, 220, 100, 255) # the export (the yellow of the headings of the window)

def code(tColor):
	return u"%d,%d,%d,%d" % tColor

def tag(tColor, szText):
	return u"<color=" + code(tColor) + u">" + szText + u"</color>"
