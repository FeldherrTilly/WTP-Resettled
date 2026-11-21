## WTP: game options (at the moment: the storage multiplier).
## The choices are saved in WTP_GameOptions.ini (like the tooltip settings). They are applied to the defines of the game
## (WAREHOUSE_STORAGE_PERCENT) when a savegame is loaded, when a game starts and at the start of
## every turn - not at the moment the option is changed. Python 2.4: no conditional expressions, no with blocks.
from CvPythonExtensions import *

gc = CyGlobalContext()

OPTIONS_FILE = "WTP_GameOptions.ini"

# storage of warehouse, expansions, custom house / office in percent (100 = as in the game speed alone)
STORAGE_PERCENTS = (50, 75, 100, 125, 150, 175, 200)
STORAGE_DEFAULT = 2

# what was put into the defines in this session
dApplied = {}

def setDefine(szDefine, iValue):
	if dApplied.get(szDefine) != iValue:
		gc.setDefineINT(szDefine, iValue)
		dApplied[szDefine] = iValue

def load():
	"(storage index)"
	aiValues = [STORAGE_DEFAULT]
	try:
		f = open(OPTIONS_FILE, "r")
		for szLine in f.readlines():
			if "=" in szLine:
				aszPart = szLine.strip().split("=")
				try:
					if aszPart[0] == "storage":
						aiValues[0] = max(0, min(len(STORAGE_PERCENTS) - 1, int(aszPart[1])))
				except:
					pass
		f.close()
	except:
		pass
	return aiValues

def save(aiValues):
	try:
		f = open(OPTIONS_FILE, "w")
		f.write("storage=%d\n" % aiValues[0])
		f.close()
	except:
		pass

def setStorage(iIndex):
	aiValues = load()
	aiValues[0] = max(0, min(len(STORAGE_PERCENTS) - 1, iIndex))
	save(aiValues)

def applyToGame(szWhere = ""):
	"Puts the saved choices into the defines (load of a savegame, game start, start of a turn)"
	try:
		aiValues = load()
		setDefine("WAREHOUSE_STORAGE_PERCENT", STORAGE_PERCENTS[aiValues[0]])
	except:
		pass
