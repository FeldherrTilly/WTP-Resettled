## WTP: game options for the storage multiplier and the military upkeep multiplier.
## The choices are saved in WTP_GameOptions.ini (like the tooltip settings). They are applied to the defines of the game
## (WAREHOUSE_STORAGE_PERCENT, MILITARY_UPKEEP_SPEED_*) when a savegame is loaded, when a game starts and at the start of
## every turn - not at the moment the option is changed. Python 2.4: no conditional expressions, no with blocks.
from CvPythonExtensions import *

gc = CyGlobalContext()

OPTIONS_FILE = "WTP_GameOptions.ini"

# storage of warehouse, expansions, custom house / office in percent (100 = as in the game speed alone)
STORAGE_PERCENTS = (50, 75, 100, 125, 150, 175, 200)
STORAGE_DEFAULT = 2
# military upkeep multiplier in percent
UPKEEP_PERCENTS = (50, 75, 100, 125, 150, 175, 200)
UPKEEP_DEFAULT = 2

SPEED_DEFINES = ("MILITARY_UPKEEP_SPEED_QUICK", "MILITARY_UPKEEP_SPEED_NORMAL", "MILITARY_UPKEEP_SPEED_EPIC", "MILITARY_UPKEEP_SPEED_MARATHON", "MILITARY_UPKEEP_SPEED_BUILDUP")
NORMAL_DEFINE = "MILITARY_UPKEEP_SPEED_NORMAL"

# the factors of the game speeds in percent (the build does not allow reading defines in Python, so they are kept here;
# the values of MILITARY_UPKEEP_SPEED_* in GlobalDefinesAlt.xml are replaced by this module)
dSpeedBase = {
	"MILITARY_UPKEEP_SPEED_QUICK": 135,
	"MILITARY_UPKEEP_SPEED_NORMAL": 100,
	"MILITARY_UPKEEP_SPEED_EPIC": 50,
	"MILITARY_UPKEEP_SPEED_MARATHON": 35,
	"MILITARY_UPKEEP_SPEED_BUILDUP": 100
}

# what was put into the defines in this session
dApplied = {}

def setDefine(szDefine, iValue):
	if dApplied.get(szDefine) != iValue:
		gc.setDefineINT(szDefine, iValue)
		dApplied[szDefine] = iValue

def load():
	"(storage index, upkeep index, game speed dependence 0/1)"
	aiValues = [STORAGE_DEFAULT, UPKEEP_DEFAULT, 0]
	try:
		f = open(OPTIONS_FILE, "r")
		for szLine in f.readlines():
			if "=" in szLine:
				aszPart = szLine.strip().split("=")
				try:
					if aszPart[0] == "storage":
						aiValues[0] = max(0, min(len(STORAGE_PERCENTS) - 1, int(aszPart[1])))
					elif aszPart[0] == "upkeep":
						aiValues[1] = max(0, min(len(UPKEEP_PERCENTS) - 1, int(aszPart[1])))
					elif aszPart[0] == "speed":
						aiValues[2] = max(0, min(1, int(aszPart[1])))
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
		f.write("upkeep=%d\n" % aiValues[1])
		f.write("speed=%d\n" % aiValues[2])
		f.close()
	except:
		pass

def setStorage(iIndex):
	aiValues = load()
	aiValues[0] = max(0, min(len(STORAGE_PERCENTS) - 1, iIndex))
	save(aiValues)

def setUpkeep(iIndex):
	aiValues = load()
	aiValues[1] = max(0, min(len(UPKEEP_PERCENTS) - 1, iIndex))
	save(aiValues)

def setSpeedDependence(bValue):
	aiValues = load()
	if bValue:
		aiValues[2] = 1
	else:
		aiValues[2] = 0
	save(aiValues)

def applyToGame():
	"Puts the saved choices into the defines (load of a savegame, game start, start of a turn)"
	try:
		aiValues = load()
		setDefine("WAREHOUSE_STORAGE_PERCENT", STORAGE_PERCENTS[aiValues[0]])
		iUpkeep = UPKEEP_PERCENTS[aiValues[1]]
		for szDefine in SPEED_DEFINES:
			if aiValues[2] == 1:
				iBase = dSpeedBase[szDefine]
			else:
				# without the game speed dependence every speed uses the value of the normal speed
				iBase = dSpeedBase[NORMAL_DEFINE]
			setDefine(szDefine, max(1, (iBase * iUpkeep + 50) / 100))
	except:
		pass
