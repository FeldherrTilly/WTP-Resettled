## WTP: window of the governor button of the city screen (import / export settings of the goods). It replaces the popup of the
## game, which has a fixed width (no room for the land / sea checkboxes) and no mouse wheel. The DLL
## (CvDLLButtonPopup::launchYieldImportExportPopup) calls askTradeRouteSetup in CvScreensInterface; the settings are sent
## with CyMessageControl().sendDoTask exactly as the popup did (CvDLLButtonPopup::OnOkClicked).
## The window is drawn on the main interface (like the amount dialog) and CvMainInterface.redraw does nothing while it is open.

from CvPythonExtensions import *
import CvUtil
import CvScreenEnums

gc = CyGlobalContext()
localText = CyTranslator()

BTN_OK = 41001
BTN_CANCEL = 41002
BTN_UP = 41003
BTN_DOWN = 41004
BTN_PRESET = 41010 # + 0..6 (0 clear all, 1 import all, 2 auto export all, 3 building material, 4 market automatic, 5 livestock, 6 military goods)
BTN_FAV_IMP = 41020 # (the favorite checkbox of a row: 41020 + slot)
BTN_FAV_EXP = 41100 # + slot
BTN_FILTER = 41400 # + slot (the filter checkbox of a row)
BTN_VIEW = 41200 # the drop down: default view / favorites
BTN_SEARCH = 41300 # the search field
BTN_CLEAR_SEARCH = 41301
BTN_MOVE = 41310 # +0 left, +1 right, +2 up, +3 down
BTN_WARN_RESET = 41330 # the notice in the middle of the window: reset the good to the setting of market automatic
BTN_WARN_OK = 41331 # the notice: ignore / OK
MOVE_STEP = 60
MOVE_DELAY = 18 # frames until the key repeats
MOVE_REPEAT = 3 # frames between the steps
BTN_ROW = 42000 # + slot * 16 + field
VIEW_ALL = 0
VIEW_FAV = 1
VIEW_MARKED = 2
VIEW_BUILD = 3 # the goods of the building material preset
VIEW_MARKET = 4 # the goods of the market automatic preset
VIEW_PRODUCED = 5 # the goods the city produces
VIEW_NEEDED = 6 # the goods the current production needs
VIEW_FILTER = 7 # the goods of the searches (kept, goods can be taken out again)
VIEW_LIVESTOCK = 8 # the goods of the livestock preset
VIEW_MILITARY = 9 # the goods of the military goods preset

# fields of a row
F_IMP_MINUS = 0
F_IMP_PLUS = 1
F_IMP_CHECK = 2
F_IMP_FEEDER = 3
F_IMP_LAND = 4
F_IMP_SEA = 5
F_EXP_MINUS = 6
F_EXP_PLUS = 7
F_EXP_CHECK = 8
F_EXP_AUTO = 9
F_EXP_LAND = 10
F_EXP_SEA = 11

# the lightening of a marked button (a translucent orange rectangle, the picture WTPMark.dds stretched to the face of the button, dimmer
# than the hover effect of the game) and, because that covers the hover effect of the game, our own one on marked buttons (WTPHover.dds,
# brighter). The pictures are 1 x 1 pixel (orange, different transparency); the margins are the border of the button picture that is
# left free. The hover effect is drawn on every button (also when the mouse is over its text).
USE_OVERLAY = True
MARK_ART = "Art/Interface/Screens/TradeRoutes/WTPMark.dds"
HOVER_ART = "Art/Interface/Screens/TradeRoutes/WTPHover.dds"
HILITE_LAYERS = 1
HOVER_LAYERS = 1
MARGIN_X = 2
MARGIN_Y = 3
# the font of all texts
TEXT_FONT = "3b"
# texts of the buttons: color of a text that is not marked, the offset of the text top to the middle of the button (font 3b: the
# letters from the top of the I to the bottom of the p are centered in the button)
TEXT_COLOR = "88,64,40"
TEXT_DY = -14

STEP = 50
STEP_CTRL = 10
MAX_VALUE = 0xFFFF

# the player option "new import / export window" (options screen, tab Game; it uses the player option slot PLAYEROPTION_MODDER_1):
# off (the default, the WTP community decides if the new window becomes the standard) = the original popup of the DLL with its original
# tooltips (the option cannot be read: off)
def isNewWindowEnabled():
	try:
		return CyUserProfile().getPlayerOption(PlayerOptionTypes.PLAYEROPTION_MODDER_1)
	except:
		return False

def logTrade(szText):
	try:
		f = open("WTP_TradeRoutes.log", "a")
		f.write(szText + "\n")
		f.close()
	except:
		pass

# the favorite goods are stored in the script data of the player (saved with the game, valid for all cities): a marker
# [[WTPFAV:TYPE_1,TYPE_2]] in the text (the random events keep their own markers in the same text, they are left alone)
FAV_PREFIX = "[[WTPFAV:"
FAV_SUFFIX = "]]"
# the filter (the goods of the searches) is kept like the favorites, in the script data of the player
FLT_PREFIX = "[[WTPFLT:"
FLT_SUFFIX = "]]"

def loadFilter():
	aFlt = []
	try:
		szData = getActivePlayer().getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(FLT_PREFIX)
		if iStart != -1:
			iStart += len(FLT_PREFIX)
			iEnd = szData.find(FLT_SUFFIX, iStart)
			if iEnd != -1:
				for szType in szData[iStart:iEnd].split(","):
					szType = szType.strip()
					if len(szType) > 0:
						aFlt.append(szType)
	except:
		pass
	return aFlt

def saveFilter(aFlt):
	try:
		pPlayer = getActivePlayer()
		szData = pPlayer.getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(FLT_PREFIX)
		if iStart != -1:
			iEnd = szData.find(FLT_SUFFIX, iStart)
			if iEnd != -1:
				szData = szData[:iStart] + szData[iEnd + len(FLT_SUFFIX):]
		if len(aFlt) > 0:
			szData = szData + FLT_PREFIX + ",".join(aFlt) + FLT_SUFFIX
		pPlayer.setScriptData(szData)
	except:
		import traceback
		logTrade(traceback.format_exc())

def getActivePlayer():
	return gc.getPlayer(gc.getGame().getActivePlayer())

def loadFavorites():
	aFav = []
	try:
		szData = getActivePlayer().getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(FAV_PREFIX)
		if iStart != -1:
			iStart += len(FAV_PREFIX)
			iEnd = szData.find(FAV_SUFFIX, iStart)
			if iEnd != -1:
				for szType in szData[iStart:iEnd].split(","):
					szType = szType.strip()
					if len(szType) > 0:
						aFav.append(szType)
	except:
		pass
	return aFav

def saveFavorites(aFav):
	try:
		pPlayer = getActivePlayer()
		szData = pPlayer.getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(FAV_PREFIX)
		if iStart != -1:
			iEnd = szData.find(FAV_SUFFIX, iStart)
			if iEnd != -1:
				szData = szData[:iStart] + szData[iEnd + len(FAV_SUFFIX):]
		if len(aFav) > 0:
			szData = szData + FAV_PREFIX + ",".join(aFav) + FAV_SUFFIX
		pPlayer.setScriptData(szData)
	except:
		import traceback
		logTrade(traceback.format_exc())

# the building material preset is a switch: it remembers (per city, in the script data of the player like the favorites) which goods it
# turned on (and their levels before), so that switching it off takes only those away again; the goods that were set by hand before are
# not touched at all
BLD_PREFIX = "[[WTPBLD:"
BLD_SUFFIX = "]]"
BLD_MATERIAL = ["YIELD_CLAY", "YIELD_STONE", "YIELD_TOOLS", "YIELD_HORSES", "YIELD_SAILCLOTH", "YIELD_HARDWOOD", "YIELD_ROPE"] # import and feeder, levels 100 / 150
BLD_OTHER = []
# the livestock preset: import and feeder for all livestock, at most 100 imported (the maintain level stays as it is)
LIV_PREFIX = "[[WTPLIV:"
LIV_GOODS = ["YIELD_HORSES", "YIELD_CATTLE", "YIELD_GEESE", "YIELD_GOATS", "YIELD_PIGS", "YIELD_SHEEP", "YIELD_CHICKEN"]
# the military goods preset: import and feeder for muskets, blades, cannons, black powder, bakery goods (provisions) and horses, at most 100 imported
MIL_PREFIX = "[[WTPMIL:"
MIL_GOODS = ["YIELD_MUSKETS", "YIELD_BLADES", "YIELD_CANNONS", "YIELD_BLACK_POWDER", "YIELD_BAKERY_GOODS", "YIELD_HORSES"] # (the bakery goods are the provisions the soldier professions ask for)

# the presets that switch goods on (the market automatic is a preset of its own, handled by the DLL): the data is kept per city in the script
# data of the player (prefix), "maintain" -1: the level of the good stays, the preset protection (see below) works for all of them
PRESETS = [
	{"id": "BLD", "prefix": BLD_PREFIX, "goods": BLD_MATERIAL + BLD_OTHER, "maintain": 100, "limit": 150, "code": 3, "view": VIEW_BUILD, "slot": 0, "text": "TXT_KEY_WTP_TRADEROUTE_PRESET3_SHORT", "on": "TXT_KEY_WTP_TRADEROUTE_PRESET3_SHORT_ON"},
	{"id": "LIV", "prefix": LIV_PREFIX, "goods": LIV_GOODS, "maintain": 150, "limit": 150, "code": 5, "view": VIEW_LIVESTOCK, "slot": 1, "text": "TXT_KEY_WTP_TRADEROUTE_PRESET5_SHORT", "on": "TXT_KEY_WTP_TRADEROUTE_PRESET5_SHORT_ON"},
	{"id": "MIL", "prefix": MIL_PREFIX, "goods": MIL_GOODS, "maintain": -1, "limit": 100, "code": 6, "view": VIEW_MILITARY, "slot": 2, "text": "TXT_KEY_WTP_TRADEROUTE_PRESET6_SHORT", "on": "TXT_KEY_WTP_TRADEROUTE_PRESET6_SHORT_ON"},
]

def loadBuild(szPrefix = BLD_PREFIX):
	dBuild = {}
	try:
		szData = getActivePlayer().getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(szPrefix)
		if iStart != -1:
			iStart += len(szPrefix)
			iEnd = szData.find(BLD_SUFFIX, iStart)
			if iEnd != -1:
				for szEntry in szData[iStart:iEnd].split(";"):
					if szEntry.find(":") == -1:
						continue
					szCity, szTypes = szEntry.split(":", 1)
					aTypes = []
					for szType in szTypes.split(","):
						aPart = szType.strip().split("@")
						if len(aPart) == 3 or len(aPart) == 4:
							iImp = 0
							if len(aPart) == 4:
								iImp = int(aPart[3])
							aTypes.append([aPart[0], int(aPart[1]), int(aPart[2]), iImp]) # [type, the maintain level and the import limit before, import before (0 / 1)]
					dBuild[int(szCity)] = aTypes
	except:
		pass
	return dBuild

def saveBuild(dBuild, szPrefix = BLD_PREFIX):
	try:
		pPlayer = getActivePlayer()
		szData = pPlayer.getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(szPrefix)
		if iStart != -1:
			iEnd = szData.find(BLD_SUFFIX, iStart)
			if iEnd != -1:
				szData = szData[:iStart] + szData[iEnd + len(BLD_SUFFIX):]
		aEntries = []
		for iCity in dBuild.keys():
			aTypeEntries = []
			for aType in dBuild[iCity]:
				iImp = 0
				if len(aType) > 3:
					iImp = aType[3]
				aTypeEntries.append("%s@%d@%d@%d" % (aType[0], aType[1], aType[2], iImp))
			aEntries.append(str(iCity) + ":" + ",".join(aTypeEntries))
		if len(aEntries) > 0:
			szData = szData + szPrefix + ";".join(aEntries) + BLD_SUFFIX
		pPlayer.setScriptData(szData)
	except:
		import traceback
		logTrade(traceback.format_exc())

# the market automatic preset: remembers (per city) the import settings of the goods the market asks for before it was switched on, so that
# switching it off restores them: [[WTPMKT:cityId:TYPE@imp@feeder@maintain@limit,...;...]]
MKT_PREFIX = "[[WTPMKT:"
MKT_SUFFIX = "]]"

def loadMarket():
	dMarket = {}
	try:
		szData = getActivePlayer().getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(MKT_PREFIX)
		if iStart != -1:
			iStart += len(MKT_PREFIX)
			iEnd = szData.find(MKT_SUFFIX, iStart)
			if iEnd != -1:
				for szEntry in szData[iStart:iEnd].split(";"):
					if szEntry.find(":") == -1:
						continue
					szCity, szTypes = szEntry.split(":", 1)
					aTypes = []
					for szType in szTypes.split(","):
						aPart = szType.strip().split("@")
						if len(aPart) == 5:
							aTypes.append([aPart[0], int(aPart[1]) != 0, int(aPart[2]) != 0, int(aPart[3]), int(aPart[4])])
					dMarket[int(szCity)] = aTypes
	except:
		pass
	return dMarket

def saveMarket(dMarket):
	try:
		pPlayer = getActivePlayer()
		szData = pPlayer.getScriptData()
		if szData == None:
			szData = ""
		iStart = szData.find(MKT_PREFIX)
		if iStart != -1:
			iEnd = szData.find(MKT_SUFFIX, iStart)
			if iEnd != -1:
				szData = szData[:iStart] + szData[iEnd + len(MKT_SUFFIX):]
		aEntries = []
		for iCity in dMarket.keys():
			aTypeEntries = []
			for aType in dMarket[iCity]:
				aTypeEntries.append("%s@%d@%d@%d@%d" % (aType[0], int(aType[1]), int(aType[2]), aType[3], aType[4]))
			if len(aTypeEntries) > 0:
				aEntries.append(str(iCity) + ":" + ",".join(aTypeEntries))
		if len(aEntries) > 0:
			szData = szData + MKT_PREFIX + ";".join(aEntries) + MKT_SUFFIX
		pPlayer.setScriptData(szData)
	except:
		import traceback
		logTrade(traceback.format_exc())

# the keys of the search field: key name -> character
SEARCH_KEY_NAMES = {}
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
	SEARCH_KEY_NAMES["KB_" + _c] = _c.lower()
for _c in "0123456789":
	SEARCH_KEY_NAMES["KB_" + _c] = _c
SEARCH_KEY_NAMES["KB_SPACE"] = " "
SEARCH_KEY_NAMES["KB_MINUS"] = "-"

class CvTradeRouteScreen:
	"Import / export settings of a city"

	def __init__(self):
		self.BACKGROUND_ID = "TRSBackground"
		self.W = 1100
		self.H = 600
		self.OX = 0
		self.OY = 0
		self.ROW_H = 60
		self.CHECK_H = 28
		self.LIST_Y = 206
		self.BLOCK_IMP_X = 90
		self.BLOCK_EXP_X = 520
		self.CHECK_W = 124
		self.BLOCK_SPIN_W = 116
		self.iCity = -1
		self.bCondensed = False
		self.bFinished = True
		self.pHost = None
		self.aYields = []
		self.dData = {}
		self.iFirst = 0
		self.iVisible = 0
		self.iYRes = 1440
		self.tLayout = (0, False)
		self.iReload = 0
		self.iViewX = 0
		self.aAllYields = [] # all goods of the default view
		self.aFav = [] # the favorite goods (yield types)
		self.iView = VIEW_ALL
		self.aDrawn = [] # the names of the widgets that are drawn (to delete them again)
		self.iMoveDir = -1 # the move button that is held (0 left, 1 right, 2 up, 3 down)
		self.iMoveWait = 0
		self.aHeld = [] # the arrow keys that are down
		self.iHoldWait = 0
		self.bMouseWasDown = False
		self.bRepeatDone = False
		self.iPendX = 0
		self.iPendY = 0
		self.iMoveX = 0 # the window moved by the player
		self.iMoveY = 0
		self.dBtn = {} # the buttons (name: [x, y, w, h, code, text, marked, font, dy, panels])
		self.szQuery = u""
		self.aConfirmed = [] # the goods confirmed with Enter (lowercase names)
		self.szSuggestion = u""
		self.bSearchSelected = False
		self.dNames = {}
		self.dKeys = {}
		self.sHover = ""
		self.tWarn = None # the notice in the middle of the window: (line 1, line 2, the good of market automatic to reset or -1, the goods of a preset that were switched off)
		self.aWarnQueue = [] # notices that wait for the one on the screen
		self.dIgnored = {}
		self.aWarnDrawn = []

	def isOpen(self):
		return not self.bFinished

	def isHostMain(self):
		return not self.bFinished

	def getCity(self):
		try:
			return gc.getPlayer(gc.getGame().getActivePlayer()).getCity(self.iCity)
		except:
			return None

	def getKeyId(self, szName):
		iKey = getattr(InputTypes, szName, None)
		if iKey == None:
			return -12345
		return int(iKey)

	def hasExactName(self, szTerm):
		for iYield in self.dNames.keys():
			if self.dNames[iYield].lower() == szTerm:
				return True
		return False

	# the completion of the typed text: the first good (alphabetically) that starts with it and is not confirmed yet
	def findSuggestion(self):
		self.szSuggestion = u""
		szLast = self.szQuery.lstrip().lower()
		if len(szLast) == 0:
			return
		aMatches = []
		for iYield in self.dNames.keys():
			szName = self.dNames[iYield]
			szLower = szName.lower()
			if szLower[:len(szLast)] == szLast and len(szLower) > len(szLast) and not szLower in self.aConfirmed:
				aMatches.append((szLower, szName))
		if len(aMatches) > 0:
			aMatches.sort()
			self.szSuggestion = self.szQuery[:len(self.szQuery) - len(self.szQuery.lstrip())] + aMatches[0][1]

	def drawSearchText(self):
		szCursor = u"<color=255,220,100>|</color>"
		if len(self.szQuery) == 0:
			szText = szCursor + u"<color=140,140,140> " + localText.getText("TXT_KEY_WTP_TRADEROUTE_SEARCH_HINT", ()) + u"</color>"
		elif len(self.szSuggestion) > len(self.szQuery):
			szText = u"<color=255,255,255>" + self.szSuggestion[:len(self.szQuery)] + u"</color>" + szCursor + u"<color=130,130,130>" + self.szSuggestion[len(self.szQuery):] + u"</color>"
		else:
			szText = u"<color=255,255,255>" + self.szQuery + u"</color>" + szCursor
		self.pHost.setTextAt("TRSSearchText", "TRSSearchBG", u"<font=3>" + szText + u"</font>", CvUtil.FONT_LEFT_JUSTIFY, 8, 6, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, BTN_SEARCH, -1)
		self.pHost.show("TRSSearchText")

	# a key of the search field
	def handleSearchKey(self, iKey, bShift):
		bChanged = False
		if self.dKeys.has_key(iKey):
			self.szQuery = self.szQuery + unicode(self.dKeys[iKey])
			bChanged = True
		elif iKey == self.iKeyBack:
			if len(self.szQuery) > 0:
				self.szQuery = self.szQuery[:-1]
				bChanged = True
			elif len(self.aConfirmed) > 0:
				self.aConfirmed.pop() # nothing typed: take back the last confirmed good
				bChanged = True
		elif iKey in self.aKeyConfirm:
			# Enter: keep the typed term (the exact good, or the nearest one) and empty the field for the next one
			szTerm = self.szQuery.strip().lower()
			if len(szTerm) > 0:
				if not self.hasExactName(szTerm) and len(self.szSuggestion) > len(self.szQuery):
					szTerm = self.szSuggestion.strip().lower() # no good has exactly this name: take the nearest one
				if not szTerm in self.aConfirmed:
					self.aConfirmed.append(szTerm)
				self.szQuery = u""
				bChanged = True
		elif iKey in self.aKeyAccept:
			if len(self.szSuggestion) > len(self.szQuery):
				self.szQuery = self.szSuggestion
				bChanged = True
		if bChanged:
			self.searchChanged(True)

	# the number of rows and whether there are pages: when it changes the window is built again (its height follows)
	def getMaxVisible(self):
		iBottom = self.iYRes
		if self.iMoveY == 0:
			iBottom = self.iYRes - 225 # (the default place: the three rows of the goods bar stay visible)
		return max(1, (iBottom - self.OY - self.LIST_Y - 70) / self.ROW_H)

	def getLayoutKey(self):
		iMaxVisible = self.getMaxVisible()
		iVisible = min(iMaxVisible, max(1, len(self.aYields)))
		return (iVisible, len(self.aYields) > iVisible)

	def refreshList(self):
		if self.getLayoutKey() != self.tLayout:
			self.teardownLayout()
			self.buildLayout()
		else:
			self.drawRows()
			self.drawPage()

	def searchChanged(self, bSwitch = False):
		self.findSuggestion()
		self.drawSearchText()
		self.syncFilter()
		if bSwitch and self.iView != VIEW_FILTER:
			# searching: the drop down changes to the filter view (the window is built again with the new selection)
			self.iView = VIEW_FILTER
			self.tLayout = (-1, False)
		self.buildView()
		self.refreshList()

	# the confirmed goods are saved (as yield types) with the game
	def syncFilter(self):
		aTypes = []
		for szName in self.aConfirmed:
			for iYield in self.dNames.keys():
				if self.dNames[iYield].lower() == szName:
					aTypes.append(gc.getYieldInfo(iYield).getType())
		if aTypes != loadFilter():
			saveFilter(aTypes)

	def isInFilter(self, iYield):
		return self.dNames[iYield].lower() in self.aConfirmed

	def toggleFilter(self, iYield):
		szName = self.dNames[iYield].lower()
		if szName in self.aConfirmed:
			self.aConfirmed.remove(szName)
		else:
			self.aConfirmed.append(szName)
		self.syncFilter()
		self.findSuggestion()
		self.drawSearchText()
		if self.iView == VIEW_FILTER:
			self.buildView()
			self.refreshList()
		else:
			self.drawRows()

	def filterClicked(self, iSlot):
		iIndex = self.iFirst + iSlot
		if iIndex < len(self.aYields):
			self.toggleFilter(self.aYields[iIndex])

	def isFav(self, iYield):
		return gc.getYieldInfo(iYield).getType() in self.aFav

	def toggleFav(self, iYield):
		szType = gc.getYieldInfo(iYield).getType()
		if szType in self.aFav:
			self.aFav.remove(szType)
		else:
			self.aFav.append(szType)
		saveFavorites(self.aFav)
		if self.iView == VIEW_FAV:
			self.buildView()
			self.drawRows()
			self.drawPage()
		else:
			self.drawRows()

	# the goods of the view: all of them (default) or the favorites
	def buildView(self):
		if self.iView == VIEW_FAV:
			self.aYields = [i for i in self.aAllYields if self.isFav(i)]
		elif self.iView == VIEW_MARKED:
			# the goods with any mark (import, feeder, export or auto export)
			self.aYields = [i for i in self.aAllYields if (self.dData[i]["imp"] or self.dData[i]["feeder"] or self.dData[i]["exp"] or self.dData[i]["auto"])]
		elif self.iView == VIEW_BUILD:
			self.aYields = [i for i in self.getAllCargo() if gc.getYieldInfo(i).getType() in BLD_MATERIAL + BLD_OTHER]
		elif self.iView == VIEW_LIVESTOCK:
			self.aYields = [i for i in self.getAllCargo() if gc.getYieldInfo(i).getType() in LIV_GOODS]
		elif self.iView == VIEW_MILITARY:
			self.aYields = [i for i in self.getAllCargo() if gc.getYieldInfo(i).getType() in MIL_GOODS]
		elif self.iView == VIEW_MARKET:
			pCity = self.getCity()
			self.aYields = []
			if pCity != None and not pCity.isNone():
				self.aYields = [i for i in self.getAllCargo() if pCity.isMarketDemandYield(i)]
		elif self.iView == VIEW_PRODUCED:
			pCity = self.getCity()
			self.aYields = []
			if pCity != None and not pCity.isNone():
				self.aYields = [i for i in self.aAllYields if pCity.getYieldRate(i) > 0]
		elif self.iView == VIEW_NEEDED:
			pCity = self.getCity()
			self.aYields = []
			if pCity != None and not pCity.isNone():
				self.aYields = [i for i in self.aAllYields if pCity.getRawYieldConsumed(i) > 0]
		else:
			self.aYields = list(self.aAllYields)
		szTerm = self.szQuery.strip().lower()
		if self.iView == VIEW_FILTER:
			# the confirmed goods exactly (kept), plus everything that contains the text just being typed
			aKept = []
			for iYield in self.aYields:
				szName = self.dNames[iYield].lower()
				if szName in self.aConfirmed or (len(szTerm) > 0 and szName.find(szTerm) >= 0):
					aKept.append(iYield)
			self.aYields = aKept
		self.iFirst = 0

	def getAllCargo(self):
		aKeys = self.dData.keys()
		aKeys.sort()
		return aKeys

	def setView(self, iView):
		if iView == self.iView:
			return
		self.iView = iView
		if iView != VIEW_FILTER and len(self.szQuery) > 0:
			# the text just being typed belongs to the filter view only
			self.szQuery = u""
			self.findSuggestion()
			self.drawSearchText()
		self.buildView()
		self.refreshList()

	def loadYield(self, pCity, iYield):
		d = {}
		d["imp"] = pCity.isImport(iYield)
		d["feeder"] = pCity.isImportFeeder(iYield)
		d["impLimit"] = pCity.getImportsLimit(iYield)
		d["impDom"] = pCity.getImportDomains(iYield)
		d["exp"] = pCity.isExport(iYield)
		d["auto"] = pCity.isAutoExport(iYield)
		d["maintain"] = pCity.getMaintainLevel(iYield)
		d["expDom"] = pCity.getExportDomains(iYield)
		self.dData[iYield] = d

	# the settings of the city are read again (after a preset: the city changes a moment after the command was sent)
	def reloadFromCity(self):
		pCity = self.getCity()
		if pCity == None or pCity.isNone():
			return
		for iYield in self.dData.keys():
			self.loadYield(pCity, iYield)
		if self.iView == VIEW_MARKED:
			self.buildView()
			self.drawPage()
		self.drawMarketButton(pCity)
		self.drawBuildButton()
		self.drawRows()

	# a good does something for the trade routes: the feeder is on (the game switches the import on with it), or it imports with an
	# import amount above 0 (import on with the amount 0 does nothing without the feeder)
	def isGoodActive(self, iYield):
		d = self.dData[iYield]
		return d["feeder"] or (d["imp"] and d["impLimit"] > 0)

	# a preset none of whose goods is active any more is off (its button shows it)
	def updatePresetState(self):
		if self.tWarn != None or len(self.aWarnQueue) > 0 or self.iCity < 0:
			return # (a notice is open: the player may still reset the goods)
		bChanged = False
		for p in PRESETS:
			dBuild = loadBuild(p["prefix"])
			if not dBuild.has_key(self.iCity):
				continue
			bActive = False
			for szType in p["goods"]:
				iYield = self.getYieldByType(szType)
				if iYield >= 0 and not self.isMarketLocked(iYield) and self.isGoodActive(iYield):
					bActive = True
			if not bActive:
				# the preset is off: its goods go back to what they were
				aSkipped = self.revertPresetGoods(p, dBuild[self.iCity])
				self.clearPresetLeftovers(p)
				del dBuild[self.iCity]
				saveBuild(dBuild, p["prefix"])
				bChanged = True
		if bChanged:
			self.apply()
			self.drawBuildButton()
			if self.iView == VIEW_MARKED:
				self.buildView()
				self.drawPage()

	def isPresetOn(self, p):
		return loadBuild(p["prefix"]).has_key(self.iCity)

	def isBuildOn(self):
		# one of the presets is on
		for p in PRESETS:
			if self.isPresetOn(p):
				return True
		return False

	# the buttons of the presets (building material, livestock, military goods) in one row below clear all / import all / auto-export all, a third of the window each
	def drawBuildButton(self):
		iThird = (self.W - 40 - 20) / 3
		for p in PRESETS:
			szKey = p["text"]
			bOn = self.isPresetOn(p)
			if bOn:
				szKey = p["on"]
			self.addButton("TRSPreset" + str(p["code"]), localText.getText(szKey, ()), bOn, self.OX + 20 + p["slot"] * (iThird + 10), self.OY + 130, iThird, 28, BTN_PRESET + p["code"])

	def getYieldByType(self, szType):
		for iYield in self.dData.keys():
			if gc.getYieldInfo(iYield).getType() == szType:
				return iYield
		return -1

	# the goods a preset turned on go back to what they were (off, the levels before); not the goods market automatic manages
	# (market automatic always wins: returned) and not the goods another preset that is on still asks for
	def revertPresetGoods(self, p, aEntries):
		aSkipped = []
		for aType in aEntries:
			iYield = self.getYieldByType(aType[0])
			if iYield < 0:
				continue
			if self.isMarketLocked(iYield):
				aSkipped.append(iYield)
				continue
			aOther = []
			for q in self.getPresetsOfGood(iYield):
				if q["id"] != p["id"]:
					aOther.append(q)
			if len(aOther) > 0:
				# another preset that is on still asks for the good: it keeps it and takes over what it was before (so that the good
				# is taken away again when that preset goes off)
				q = aOther[0]
				dOther = loadBuild(q["prefix"])
				if dOther.has_key(self.iCity):
					bHas = False
					for aOld in dOther[self.iCity]:
						if aOld[0] == aType[0]:
							bHas = True
					if not bHas:
						dOther[self.iCity].append(list(aType))
						saveBuild(dOther, q["prefix"])
				continue
			self.dData[iYield]["imp"] = False # (the import goes too, also an import with the amount 0 that was there before)
			self.dData[iYield]["feeder"] = False
			self.dData[iYield]["maintain"] = aType[1]
			self.dData[iYield]["impLimit"] = aType[2]
		return aSkipped

	# a preset that went off: what is left of it at its goods is switched off too (an import with the amount 0 and no feeder);
	# not the goods market automatic manages and not the goods another preset that is on still asks for
	def clearPresetLeftovers(self, p):
		for szType in p["goods"]:
			iYield = self.getYieldByType(szType)
			if iYield < 0 or self.isMarketLocked(iYield):
				continue
			bOther = False
			for q in self.getPresetsOfGood(iYield):
				if q["id"] != p["id"]:
					bOther = True
			d = self.dData[iYield]
			if not bOther and d["imp"] and not d["feeder"] and d["impLimit"] == 0:
				d["imp"] = False

	# a preset (building material, livestock) as a switch: on remembers the goods it turned on (and their levels before), off takes only those away
	def toggleBuild(self, p):
		dBuild = loadBuild(p["prefix"])
		aSkipped = []
		if dBuild.has_key(self.iCity):
			# off: only the goods the preset turned on are taken away again
			aSkipped = self.revertPresetGoods(p, dBuild[self.iCity])
			del dBuild[self.iCity]
		else:
			aAdded = []
			for szType in p["goods"]:
				iYield = self.getYieldByType(szType)
				if iYield < 0:
					continue
				d = self.dData[iYield]
				if self.isGoodActive(iYield):
					continue # set by hand before: stays as it is
				if self.isMarketLocked(iYield):
					aSkipped.append(iYield) # (market automatic manages the good)
					continue
				aAdded.append([szType, d["maintain"], d["impLimit"], int(d["imp"])])
				d["imp"] = True
				d["feeder"] = True
				self.setPresetLevels(d, p)
			dBuild[self.iCity] = aAdded
		saveBuild(dBuild, p["prefix"])
		self.apply()
		self.warnSkipped(aSkipped)
		self.drawBuildButton()
		if self.iView == VIEW_MARKED:
			self.buildView()
			self.drawPage()
		self.drawRows()
		self.iReload = 60

	# the levels of a preset (maintain -1: the level of the good stays, but never above the import limit)
	def setPresetLevels(self, d, p):
		if p["maintain"] >= 0:
			d["maintain"] = p["maintain"]
		d["impLimit"] = p["limit"]
		if d["maintain"] > d["impLimit"]:
			d["maintain"] = d["impLimit"]

	# --- PRESET PROTECTION (part 1): market automatic: the goods it manages are protected: the presets of the window leave them alone, a manual change is reported ---
	def isMarketOn(self):
		pCity = self.getCity()
		return pCity != None and not pCity.isNone() and pCity.isAutoMarketImport()

	# market automatic is on and the market asks for the good
	def isMarketLocked(self, iYield):
		if not self.isMarketOn():
			return False
		return self.getCity().getMarketImportMaintain(iYield) >= 0

	# the setting of the good differs from what market automatic sets (it never lowers a level, so a higher one is fine)
	def isMarketDeviating(self, iYield):
		pCity = self.getCity()
		iMaintain = pCity.getMarketImportMaintain(iYield)
		iLimit = pCity.getMarketImportLimit(iYield)
		if iMaintain < 0:
			return False
		d = self.dData[iYield]
		return (not d["imp"]) or (not d["feeder"]) or d["exp"] or d["maintain"] < iMaintain or d["impLimit"] < iLimit

	# a manual change: reported when it breaks market automatic or switches off a good a preset has set
	def checkMarketChange(self, iYield, dOld = None):
		if not self.isMarketLocked(iYield):
			if dOld != None:
				self.checkPresetLost([iYield], False, {iYield: dOld})
			return
		if self.isMarketDeviating(iYield):
			szLine1 = localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_MANUAL_1", (self.dNames[iYield],))
			szLine2 = localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_MANUAL_2", ())
			self.showWarn(szLine1, szLine2, iYield)

	# back to the setting of market automatic (the export is taken away: the market does not manage exported goods)
	def resetMarketGood(self, iYield):
		pCity = self.getCity()
		iMaintain = pCity.getMarketImportMaintain(iYield)
		iLimit = pCity.getMarketImportLimit(iYield)
		if iMaintain >= 0:
			d = self.dData[iYield]
			d["imp"] = True
			d["feeder"] = True
			d["exp"] = False
			d["auto"] = False
			d["maintain"] = iMaintain
			d["impLimit"] = iLimit
			self.apply()
			self.iReload = 60
		self.hideWarn()
		self.drawRows()

	# the goods a preset did not change because market automatic manages them: a notice
	def warnSkipped(self, aSkipped):
		if len(aSkipped) == 0:
			return
		aNames = [self.dNames[i] for i in aSkipped[:4]]
		szNames = ", ".join(aNames)
		if len(aSkipped) > 4:
			szNames += ", ..."
		szLine1 = localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_SKIPPED_1", (str(len(aSkipped)),))
		szLine2 = localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_SKIPPED_2", (szNames,))
		self.showWarn(szLine1, szLine2, -1)

	# --- PRESET PROTECTION (part 2): the building material preset (and presets to come): the goods it has set are reported when they are switched off again ---
	# the goods of the preset (the ones it turned on) that are off / zero now, among the given goods
	# the presets (switched on) that ask for the good
	def getPresetsOfGood(self, iYield):
		aPresets = []
		szType = gc.getYieldInfo(iYield).getType()
		for p in PRESETS:
			if szType in p["goods"] and self.isPresetOn(p):
				aPresets.append(p)
		return aPresets

	def getPresetNames(self, iYield):
		return [localText.getText(p["text"], ()) for p in self.getPresetsOfGood(iYield)]

	# what the presets (switched on) ask for a good: (maintain level or -1, import limit); the highest of them
	def getPresetLevels(self, iYield):
		iMaintain = -1
		iLimit = 0
		for p in self.getPresetsOfGood(iYield):
			iMaintain = max(iMaintain, p["maintain"])
			iLimit = max(iLimit, p["limit"])
		return (iMaintain, iLimit)

	# a good that a preset asks for (owned or not) was lowered by the last change: import or feeder switched off, or the maintain level or
	# the import limit lowered below what the presets ask for (raising something is fine); goods the player chose to ignore are left alone.
	# dOld: the settings of the good before the change
	def isPresetLost(self, iYield, dOld):
		if not self.dData.has_key(iYield) or len(self.getPresetsOfGood(iYield)) == 0 or self.isMarketLocked(iYield):
			return False
		d = self.dData[iYield]
		if self.dIgnored.has_key(iYield):
			if d["imp"] and d["feeder"]:
				del self.dIgnored[iYield] # active again: protected again
			return False
		iMaintain, iLimit = self.getPresetLevels(iYield)
		if dOld == None:
			return False
		if dOld["imp"] and not d["imp"]:
			return True
		if dOld["feeder"] and not d["feeder"]:
			return True
		if iMaintain >= 0 and d["maintain"] < dOld["maintain"] and d["maintain"] < iMaintain:
			return True
		if d["impLimit"] < dOld["impLimit"] and d["impLimit"] < iLimit:
			return True
		return False

	# the notice lists every switched off good with all presets that ask for it
	def checkPresetLost(self, aGoods, bQueue = False, dOldAll = None):
		if dOldAll == None:
			return
		aLost = [i for i in aGoods if dOldAll.has_key(i) and self.isPresetLost(i, dOldAll[i])]
		if len(aLost) == 0:
			return
		aNames = []
		for i in aLost[:4]:
			aNames.append(self.dNames[i] + " (" + ", ".join(self.getPresetNames(i)) + ")")
		szNames = "; ".join(aNames)
		if len(aLost) > 4:
			szNames += "; ..."
		szLine1 = localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_PRESET_1", (str(len(aLost)),))
		szLine2 = localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_PRESET_2", (szNames,))
		self.showWarn(szLine1, szLine2, -1, aLost, bQueue or self.tWarn != None)

	# reset: the goods get the levels the presets ask for (the highest of them, so that every preset is satisfied)
	def resetPresetGoods(self, aGoods):
		for iYield in aGoods:
			d = self.dData[iYield]
			d["imp"] = True
			d["feeder"] = True
			iMaintain, iLimit = self.getPresetLevels(iYield)
			if iMaintain >= 0:
				d["maintain"] = max(d["maintain"], iMaintain)
			d["impLimit"] = max(d["impLimit"], iLimit)
			if d["maintain"] > d["impLimit"]:
				d["maintain"] = d["impLimit"]
		self.apply()
		self.iReload = 60

	# ignore: the goods are not part of the presets any more (until they are switched on again); a preset none of whose goods is active
	# any more is off (its button shows it)
	def ignorePresetGoods(self, aGoods):
		aTypes = []
		for iYield in aGoods:
			self.dIgnored[iYield] = True
			aTypes.append(gc.getYieldInfo(iYield).getType())
		for p in PRESETS:
			dBuild = loadBuild(p["prefix"])
			if not dBuild.has_key(self.iCity):
				continue
			aRest = []
			for aType in dBuild[self.iCity]:
				if not aType[0] in aTypes:
					aRest.append(aType)
			dBuild[self.iCity] = aRest
			bActive = False
			for szType in p["goods"]:
				iYield = self.getYieldByType(szType)
				if iYield >= 0 and not self.isMarketLocked(iYield) and self.isGoodActive(iYield):
					bActive = True
			if not bActive:
				self.revertPresetGoods(p, dBuild[self.iCity])
				self.clearPresetLeftovers(p)
				del dBuild[self.iCity]
			saveBuild(dBuild, p["prefix"])
		self.apply()
		self.drawBuildButton()
		if self.iView == VIEW_MARKED:
			self.buildView()
			self.drawPage()

	def showWarn(self, szLine1, szLine2, iYield, aGoods = None, bQueue = False, p = None):
		if aGoods == None:
			aGoods = []
		if bQueue and self.tWarn != None:
			self.aWarnQueue.append((szLine1, szLine2, iYield, aGoods, p))
			return
		self.tWarn = (szLine1, szLine2, iYield, aGoods, p)
		self.drawWarn()

	def hideWarn(self):
		self.tWarn = None
		if len(self.aWarnQueue) > 0:
			# the next notice
			self.tWarn = self.aWarnQueue.pop(0)
		for szName in self.aWarnDrawn:
			self.drop(szName)
		for szName in ("TRSWarnReset", "TRSWarnOk"):
			self.removeButton(szName)
		self.aWarnDrawn = []
		if self.tWarn != None:
			self.drawWarn()

	# the text broken into lines of at most iMax characters
	def wrapText(self, szText, iMax):
		aLines = []
		szLine = u""
		for szWord in szText.split(u" "):
			if len(szLine) > 0 and len(szLine) + 1 + len(szWord) > iMax:
				aLines.append(szLine)
				szLine = szWord
			elif len(szLine) > 0:
				szLine = szLine + u" " + szWord
			else:
				szLine = szWord
		aLines.append(szLine)
		return aLines

	# the notice in the middle of the window: a dark panel, two lines and the buttons (Reset only for a changed good)
	def drawWarn(self):
		if self.tWarn == None:
			return
		screen = self.pHost
		for szName in self.aWarnDrawn:
			self.drop(szName)
		for szName in ("TRSWarnReset", "TRSWarnOk"):
			self.removeButton(szName)
		self.aWarnDrawn = []
		iW = min(self.W - 40, 900)
		aLines = self.wrapText(self.tWarn[1], 100)
		iH = 110 + 24 * len(aLines)
		iX = self.OX + (self.W - iW) / 2
		iY = self.OY + (self.H - iH) / 2
		for iLayer in range(3):
			szBack = "TRSWarnBack" + str(iLayer)
			screen.addPanel(szBack, u"", u"", True, False, iX, iY, iW, iH, PanelStyles.PANEL_STYLE_HUD_HELP, WidgetTypes.WIDGET_GENERAL, -1, -1)
			self.aWarnDrawn.append(szBack)
		screen.setText("TRSWarnText1", "", u"<font=3b><color=255,220,100>" + self.tWarn[0] + u"</color></font>", CvUtil.FONT_CENTER_JUSTIFY, iX + iW / 2, iY + 20, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)
		self.aWarnDrawn.append("TRSWarnText1")
		for iLine in range(len(aLines)):
			szLine = "TRSWarnText2_" + str(iLine)
			screen.setText(szLine, "", u"<font=3b><color=255,255,255>" + aLines[iLine] + u"</color></font>", CvUtil.FONT_CENTER_JUSTIFY, iX + iW / 2, iY + 50 + iLine * 24, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)
			self.aWarnDrawn.append(szLine)
		if self.tWarn[2] >= 0 or len(self.tWarn[3]) > 0:
			self.addButton("TRSWarnReset", localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_RESET", ()), False, iX + iW / 2 - 165, iY + iH - 42, 160, 28, BTN_WARN_RESET)
			self.addButton("TRSWarnOk", localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_IGNORE", ()), False, iX + iW / 2 + 5, iY + iH - 42, 160, 28, BTN_WARN_OK)
		else:
			self.addButton("TRSWarnOk", localText.getText("TXT_KEY_MAIN_MENU_OK", ()), False, iX + iW / 2 - 80, iY + iH - 42, 160, 28, BTN_WARN_OK)

	# market automatic: on remembers the settings of the goods the market asks for, off restores them
	def toggleMarket(self):
		pCity = self.getCity()
		if pCity == None or pCity.isNone():
			return
		if self.iView != VIEW_ALL:
			# (it works in the view with all goods only)
			self.showWarn(localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_VIEW_1", ()), localText.getText("TXT_KEY_WTP_TRADEROUTE_WARN_VIEW_2", ()), -1)
			return
		try:
			dMarket = loadMarket()
			if pCity.isAutoMarketImport():
				self.apply() # (the settings made by hand are sent first)
				aSaved = []
				if dMarket.has_key(self.iCity):
					aSaved = dMarket[self.iCity]
					del dMarket[self.iCity]
				CyMessageControl().sendDoTask(self.iCity, TaskTypes.TASK_TRADEROUTE_PRESET, 1, 0, False, False, False, False) # (switches it off)
				for aType in aSaved:
					iYield = self.getYieldByType(aType[0])
					if iYield >= 0:
						d = self.dData[iYield]
						d["imp"] = aType[1]
						d["feeder"] = aType[2]
						d["maintain"] = aType[3]
						d["impLimit"] = aType[4]
				self.apply() # (restores them; the preset above is processed first)
			else:
				self.apply()
				aSaved = []
				for iYield in self.dData.keys():
					if pCity.isMarketDemandYield(iYield):
						d = self.dData[iYield]
						aSaved.append([gc.getYieldInfo(iYield).getType(), d["imp"], d["feeder"], d["maintain"], d["impLimit"]])
				dMarket[self.iCity] = aSaved
				CyMessageControl().sendDoTask(self.iCity, TaskTypes.TASK_TRADEROUTE_PRESET, 1, 0, False, False, False, False)
			saveMarket(dMarket)
		except:
			import traceback
			logTrade(traceback.format_exc())
		self.drawRows()
		self.iReload = 60

	def drawMarketButton(self, pCity):
		szMarket = "TXT_KEY_WTP_TRADEROUTE_PRESET4_SHORT"
		if pCity.isAutoMarketImport():
			szMarket = "TXT_KEY_WTP_TRADEROUTE_PRESET4_SHORT_ON"
		# on top of the three buttons clear all / import all / auto-export all, as wide as these together
		self.addButton("TRSPreset4", localText.getText(szMarket, ()), pCity.isAutoMarketImport(), self.OX + 20, self.OY + 62, self.W - 40, 28, BTN_PRESET + 4)

	# opens the window (1: it is open, 0: the DLL shows its own popup instead)
	def open(self, iCity, bCondensed):
		if not self.bFinished:
			return 1
		self.iCity = iCity
		pCity = self.getCity()
		if pCity == None or pCity.isNone():
			return 0
		self.bCondensed = bCondensed
		self.aYields = []
		self.dData = {}
		self.aFav = loadFavorites()
		self.iView = VIEW_ALL
		self.dBtn = {}
		self.sHover = ""
		self.tWarn = None
		self.aWarnQueue = []
		self.dIgnored = {} # the goods the player ignored the preset protection for (until they are active again)
		for iYield in range(YieldTypes.NUM_YIELD_TYPES):
			if not gc.getYieldInfo(iYield).isCargo():
				continue
			self.loadYield(pCity, iYield)
			if bCondensed and not pCity.isYieldInTradeRouteCondensedList(iYield):
				continue
			self.aYields.append(iYield)

		self.aAllYields = list(self.aYields)
		self.szQuery = u""
		self.aConfirmed = []
		self.szSuggestion = u""
		self.bSearchSelected = False
		self.dNames = {}
		for iYield in self.dData.keys():
			self.dNames[iYield] = gc.getYieldInfo(iYield).getDescription()
		# the filter of the searches before (names in the order they were confirmed)
		for szType in loadFilter():
			for iYield in self.dNames.keys():
				if gc.getYieldInfo(iYield).getType() == szType:
					self.aConfirmed.append(self.dNames[iYield].lower())
		self.dKeys = {}
		for szKey in SEARCH_KEY_NAMES.keys():
			iKey = getattr(InputTypes, szKey, None)
			if iKey != None:
				self.dKeys[int(iKey)] = SEARCH_KEY_NAMES[szKey]
		self.iKeyBack = self.getKeyId("KB_BACKSPACE")
		self.aKeyAccept = [self.getKeyId("KB_TAB")]
		self.aKeyConfirm = [self.getKeyId("KB_RETURN"), self.getKeyId("KB_NUMPADENTER")]
		self.aKeyArrows = [self.getKeyId("KB_LEFT"), self.getKeyId("KB_RIGHT"), self.getKeyId("KB_UP"), self.getKeyId("KB_DOWN")]
		self.iKey6 = self.getKeyId("KB_6")
		self.iKey7 = self.getKeyId("KB_7")
		self.iKeyEsc = self.getKeyId("KB_ESCAPE")
		self.pHost = CyGInterfaceScreen("MainInterface", CvScreenEnums.MAIN_INTERFACE)
		self.iFirst = 0
		self.iPendX = 0
		self.iPendY = 0
		self.iMoveDir = -1
		self.aHeld = []
		self.bFinished = False
		self.buildLayout()
		try:
			CyGame().setWheelCapture(True)
		except:
			pass
		return 1

	# the widgets of the window at its current place (also used to move it)
	def buildLayout(self):
		pCity = self.getCity()
		screen = self.pHost
		iXRes = screen.getXResolution()
		iYRes = screen.getYResolution()
		self.iYRes = iYRes
		# the default place: at the right edge of the screen, just below the top bar (until the player moves the window)
		iBaseX = iXRes - self.W
		iBaseY = 71
		# the height follows the number of goods shown (the top stays where it is, the bottom moves): in the default place it ends above
		# the three rows of the goods bar, a window the player has moved down may go down to the bottom of the screen
		iTop = max(0, min(iYRes - (self.LIST_Y + self.ROW_H + 70), iBaseY + self.iMoveY))
		self.iMoveY = iTop - iBaseY
		self.OY = iTop
		iMaxVisible = self.getMaxVisible()
		self.iVisible = min(iMaxVisible, max(1, len(self.aYields)))
		self.tLayout = self.getLayoutKey()
		self.H = self.LIST_Y + self.iVisible * self.ROW_H + 70
		self.OX = max(0, min(iXRes - self.W, iBaseX + self.iMoveX))
		self.iMoveX = self.OX - iBaseX
		self.iFirst = min(self.iFirst, max(0, (len(self.aYields) - 1) / self.iVisible * self.iVisible))
		self.aDrawn = []

		# the dark, translucent background: the panel style of the message panel, three layers on top of each other like the expanded one
		for szBack in ("TRSBack1", "TRSBack2"):
			screen.addPanel(szBack, u"", u"", True, False, self.OX, self.OY, self.W, self.H, PanelStyles.PANEL_STYLE_HUD_HELP, WidgetTypes.WIDGET_GENERAL, -1, -1)
			self.aDrawn.append(szBack)
		screen.addPanel(self.BACKGROUND_ID, u"", u"", True, False, self.OX, self.OY, self.W, self.H, PanelStyles.PANEL_STYLE_HUD_HELP, WidgetTypes.WIDGET_GENERAL, -1, -1)
		self.aDrawn.append(self.BACKGROUND_ID)
		szTitle = u"<font=3><color=255,220,100>" + pCity.getName() + u"</color></font>"
		screen.setLabelAt("TRSTitle", self.BACKGROUND_ID, szTitle, CvUtil.FONT_CENTER_JUSTIFY, self.W / 2, 18, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.setLabelAt("TRSHint", self.BACKGROUND_ID, u"<font=2>" + localText.getText("TXT_KEY_WTP_TRADEROUTE_HINT", ()) + u"</font>", CvUtil.FONT_CENTER_JUSTIFY, self.W / 2, 44, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)
		self.aDrawn.append("TRSTitle")
		self.aDrawn.append("TRSHint")
		iHeadW = self.BLOCK_SPIN_W + 8 + 2 * self.CHECK_W + 4
		screen.setLabelAt("TRSHeadImp", self.BACKGROUND_ID, u"<font=3b><color=255,220,100>" + localText.getText("TXT_KEY_WTP_TRADEROUTE_IMPORT_OPTIONS", ()) + u"</color></font>", CvUtil.FONT_CENTER_JUSTIFY, self.BLOCK_IMP_X + iHeadW / 2, self.LIST_Y - 28, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)
		screen.setLabelAt("TRSHeadExp", self.BACKGROUND_ID, u"<font=3b><color=255,220,100>" + localText.getText("TXT_KEY_WTP_TRADEROUTE_EXPORT_OPTIONS", ()) + u"</color></font>", CvUtil.FONT_CENTER_JUSTIFY, self.BLOCK_EXP_X + iHeadW / 2, self.LIST_Y - 28, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)
		self.aDrawn.append("TRSHeadImp")
		self.aDrawn.append("TRSHeadExp")

		# the presets (the buttons of the old popup)
		iBW = (self.W - 40 - 20) / 3
		aszPreset = [localText.getText("TXT_KEY_POPUP_IMPORT_CLEAR_ALL", ()), localText.getText("TXT_KEY_POPUP_IMPORT_ALL", ()), localText.getText("TXT_KEY_POPUP_IMPORT_EXPORT_ALL", ())]
		for i in range(3):
			self.addButton("TRSPreset" + str(i), aszPreset[i], False, self.OX + 20 + i * (iBW + 10), self.OY + 96, iBW, 28, BTN_PRESET + i)
		iHalf = (self.W - 40 - 10) / 2
		self.drawBuildButton()
		self.drawMarketButton(pCity)

		# moves the window (the arrows at the top right; Ctrl with the arrow keys does the same)
		iMX = self.OX + self.W - 20 - 4 * 30
		self.addButton("TRSMoveL", u"\u00ab", False, iMX, self.OY + 12, 28, 24, BTN_MOVE)
		self.addButton("TRSMoveU", u"^", False, iMX + 30, self.OY + 12, 28, 24, BTN_MOVE + 2)
		self.addButton("TRSMoveD", u"v", False, iMX + 60, self.OY + 12, 28, 24, BTN_MOVE + 3)
		self.addButton("TRSMoveR", u"\u00bb", False, iMX + 90, self.OY + 12, 28, 24, BTN_MOVE + 1)
		self.addButton("TRSOk", localText.getText("TXT_KEY_MAIN_MENU_OK", ()), False, self.OX + self.W / 2 - 105, self.OY + self.H - 44, 100, 28, BTN_OK)
		self.addButton("TRSCancel", localText.getText("TXT_KEY_POPUP_CANCEL", ()), False, self.OX + self.W / 2 + 5, self.OY + self.H - 44, 100, 28, BTN_CANCEL)
		if len(self.aYields) > self.iVisible:
			self.addButton("TRSUp", u"\u00ab", False, self.OX + 24, self.OY + self.H - 44, 36, 28, BTN_UP)
			self.addButton("TRSDown", u"\u00bb", False, self.OX + 24 + 36 + 150, self.OY + self.H - 44, 36, 28, BTN_DOWN)
			self.aDrawn.append("TRSPage")

		# the search field between Cancel and the drop down
		self.iSearchX = self.W / 2 + 5 + 100 + 14
		self.iSearchW = self.W - 20 - 160 - 14 - 34 - 6 - self.iSearchX
		screen.addPanel("TRSSearchBG", u"", u"", False, False, self.OX + self.iSearchX, self.OY + self.H - 46, self.iSearchW, 32, PanelStyles.PANEL_STYLE_IN, WidgetTypes.WIDGET_GENERAL, BTN_SEARCH, -1)
		self.aDrawn.append("TRSSearchBG")
		self.addButton("TRSClearSearch", u"X", False, self.OX + self.iSearchX + self.iSearchW + 4, self.OY + self.H - 46, 34, 32, BTN_CLEAR_SEARCH)
		self.drawSearchText()
		self.iViewX = self.W - 20 - 160
		screen.addDropDownBoxGFC("TRSView", self.OX + self.iViewX, self.OY + self.H - 44, 160, WidgetTypes.WIDGET_GENERAL, BTN_VIEW, -1, FontTypes.GAME_FONT)
		# the views: all goods, market automatic, favorites, filter, marked only, needed goods, produced goods; then the presets in alphabetical
		# order (of the text of the language; the number of the view is the data of the entry)
		aFixed = [(0, "TXT_KEY_WTP_TRADEROUTE_VIEW_ALL"), (4, "TXT_KEY_WTP_TRADEROUTE_PRESET4_SHORT"), (1, "TXT_KEY_WTP_TRADEROUTE_VIEW_FAV"),
			(7, "TXT_KEY_WTP_TRADEROUTE_VIEW_FILTER"), (2, "TXT_KEY_WTP_TRADEROUTE_VIEW_MARKED"), (6, "TXT_KEY_WTP_TRADEROUTE_VIEW_NEEDED"),
			(5, "TXT_KEY_WTP_TRADEROUTE_VIEW_PRODUCED")]
		aPresetViews = []
		for p in PRESETS:
			aPresetViews.append((localText.getText(p["text"], ()).lower(), p["text"], p["view"]))
		aPresetViews.sort()
		aViews = []
		for aView in aFixed:
			aViews.append((aView[0], localText.getText(aView[1], ())))
		for aView in aPresetViews:
			aViews.append((aView[2], localText.getText(aView[1], ())))
		for iPos in range(len(aViews)):
			screen.addPullDownString("TRSView", aViews[iPos][1], iPos, aViews[iPos][0], self.iView == aViews[iPos][0])
		self.aDrawn.append("TRSView")
		self.drawRows()
		self.drawPage()

	def drop(self, szName):
		try:
			self.pHost.deleteWidget(szName)
		except:
			pass

	# a button: blank button of the game, on it the text of the game (placed exactly, yellow when marked); a marked button is lighter
	def addButton(self, szName, szText, bMark, iX, iY, iW, iH, iCode, szFont = "", iDy = 0):
		screen = self.pHost
		if szFont == "":
			szFont = TEXT_FONT
		self.removeButton(szName)
		screen.setButtonGFC(szName, u"", "", iX, iY, iW, iH, WidgetTypes.WIDGET_GENERAL, iCode, -1, ButtonStyles.BUTTON_STYLE_STANDARD)
		aLights = []
		if bMark and USE_OVERLAY:
			for i in range(HILITE_LAYERS):
				szLight = "TRSb" + str(i) + "_" + szName
				screen.setImageButton(szLight, MARK_ART, iX + MARGIN_X, iY + MARGIN_Y, iW - 2 * MARGIN_X, iH - 2 * MARGIN_Y, WidgetTypes.WIDGET_GENERAL, iCode, -1)
				aLights.append(szLight)
		self.dBtn[szName] = [iX, iY, iW, iH, iCode, szText, bMark, szFont, iDy, aLights]
		self.drawButtonText(szName)

	def drawButtonText(self, szName):
		b = self.dBtn[szName]
		szLabel = "TRSL" + szName
		self.drop(szLabel)
		szColor = TEXT_COLOR
		if b[6]:
			szColor = "255,220,100"
		szShown = u"<font=" + b[7] + u"><color=" + szColor + u">" + b[5] + u"</color></font>"
		self.pHost.setText(szLabel, "", szShown, CvUtil.FONT_CENTER_JUSTIFY, b[0] + b[2] / 2, b[1] + b[3] / 2 + TEXT_DY + b[8], 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, b[4], -1)

	def removeButton(self, szName):
		self.drop(szName)
		self.drop("TRSL" + szName)
		for i in range(HILITE_LAYERS):
			self.drop("TRSb" + str(i) + "_" + szName)
		if self.dBtn.has_key(szName):
			if self.sHover == szName:
				self.clearHover()
			del self.dBtn[szName]

	def clearHover(self):
		for i in range(HOVER_LAYERS):
			self.drop("TRSHover" + str(i))
		self.sHover = ""

	# the button under the mouse gets a lighter / orange panel (called every frame)
	def updateHover(self):
		if not USE_OVERLAY:
			return
		iX = CyGame().getCursorClientX()
		iY = CyGame().getCursorClientY()
		szNew = ""
		for szName in self.dBtn.keys():
			b = self.dBtn[szName]
			if iX >= b[0] and iX < b[0] + b[2] and iY >= b[1] + 3 and iY < b[1] + b[3] - 3:
				szNew = szName
				break
		if szNew == self.sHover:
			return
		self.clearHover()
		if szNew != "":
			b = self.dBtn[szNew]
			for i in range(HOVER_LAYERS):
				self.pHost.setImageButton("TRSHover" + str(i), HOVER_ART, b[0] + MARGIN_X, b[1] + MARGIN_Y, b[2] - 2 * MARGIN_X, b[3] - 2 * MARGIN_Y, WidgetTypes.WIDGET_GENERAL, b[4], -1)
			self.sHover = szNew
			self.drawButtonText(szNew) # (the text on top of the panel)

	def drawCheck(self, szName, szText, bOn, iX, iY, iCode):
		self.addButton(szName, szText, bOn, iX, iY, self.CHECK_W, self.CHECK_H, iCode)

	def drawRows(self):
		screen = self.pHost
		self.clearHover()
		self.updatePresetState()
		szImport = localText.getText("TXT_KEY_POPUP_IMPORT_IMPORT", ())
		szFeeder = localText.getText("TXT_KEY_POPUP_IMPORT_FEEDER", ())
		szLand = localText.getText("TXT_KEY_POPUP_IMPORT_LAND", ())
		szSea = localText.getText("TXT_KEY_POPUP_IMPORT_SEA", ())
		szExport = localText.getText("TXT_KEY_POPUP_IMPORT_EXPORT", ())
		szAuto = localText.getText("TXT_KEY_POPUP_IMPORT_AUTO_EXPORT", ())
		szFav = localText.getText("TXT_KEY_WTP_TRADEROUTE_FAVORITE", ())
		szFilter = localText.getText("TXT_KEY_WTP_TRADEROUTE_VIEW_FILTER", ())
		for iSlot in range(self.iVisible):
			iIndex = self.iFirst + iSlot
			if iIndex >= len(self.aYields):
				self.clearSlot(iSlot)
				continue
			iYield = self.aYields[iIndex]
			d = self.dData[iYield]
			iY = self.OY + self.LIST_Y + iSlot * self.ROW_H
			iBase = BTN_ROW + iSlot * 16
			szIcon = "TRSIcon" + str(iSlot)
			self.drop(szIcon)
			screen.setImageButton(szIcon, gc.getYieldInfo(iYield).getButton(), self.OX + 22, iY + (self.ROW_H - 32) / 2, 32, 32, WidgetTypes.WIDGET_HELP_YIELD, iYield, -1)
			# import block
			iX = self.OX + self.BLOCK_IMP_X
			self.drawSpin(iSlot, 0, d["impLimit"], iX, iY, iBase + F_IMP_MINUS, iBase + F_IMP_PLUS)
			iCX = iX + self.BLOCK_SPIN_W + 8
			self.drawCheck("TRSc" + str(iSlot) + "_2", szImport, d["imp"], iCX, iY + 2, iBase + F_IMP_CHECK)
			self.drawCheck("TRSc" + str(iSlot) + "_3", szFeeder, d["feeder"], iCX + self.CHECK_W + 4, iY + 2, iBase + F_IMP_FEEDER)
			self.drawCheck("TRSc" + str(iSlot) + "_4", szLand, (d["impDom"] & 1) != 0, iCX, iY + 2 + self.CHECK_H + 2, iBase + F_IMP_LAND)
			self.drawCheck("TRSc" + str(iSlot) + "_5", szSea, (d["impDom"] & 2) != 0, iCX + self.CHECK_W + 4, iY + 2 + self.CHECK_H + 2, iBase + F_IMP_SEA)
			# export block
			iX = self.OX + self.BLOCK_EXP_X
			self.drawSpin(iSlot, 1, d["maintain"], iX, iY, iBase + F_EXP_MINUS, iBase + F_EXP_PLUS)
			iCX = iX + self.BLOCK_SPIN_W + 8
			self.drawCheck("TRSc" + str(iSlot) + "_8", szExport, d["exp"], iCX, iY + 2, iBase + F_EXP_CHECK)
			self.drawCheck("TRSc" + str(iSlot) + "_9", szAuto, d["auto"], iCX + self.CHECK_W + 4, iY + 2, iBase + F_EXP_AUTO)
			self.drawCheck("TRSc" + str(iSlot) + "_10", szLand, (d["expDom"] & 1) != 0, iCX, iY + 2 + self.CHECK_H + 2, iBase + F_EXP_LAND)
			self.drawCheck("TRSc" + str(iSlot) + "_11", szSea, (d["expDom"] & 2) != 0, iCX + self.CHECK_W + 4, iY + 2 + self.CHECK_H + 2, iBase + F_EXP_SEA)
			# the favorite checkbox at the right end of the row (one setting per good, for import and export)
			bFav = self.isFav(iYield)
			self.drawCheck("TRSc" + str(iSlot) + "_fe", szFav, bFav, self.OX + self.iViewX + (160 - self.CHECK_W) / 2, iY + 2, BTN_FAV_EXP + iSlot)
			# below it: the good is part of the filter (the goods of the searches, view "Filter")
			self.drawCheck("TRSc" + str(iSlot) + "_ff", szFilter, self.isInFilter(iYield), self.OX + self.iViewX + (160 - self.CHECK_W) / 2, iY + 2 + self.CHECK_H + 2, BTN_FILTER + iSlot)
		self.drawWarn() # (the notice stays on top of the rows)

	def drawSpin(self, iSlot, iBlock, iValue, iX, iY, iMinusCode, iPlusCode):
		screen = self.pHost
		szTag = str(iSlot) + "_" + str(iBlock)
		iBH = 30
		iBY = iY + (self.ROW_H - iBH) / 2
		self.drop("TRSv" + szTag)
		self.addButton("TRSm" + szTag, u"-", False, iX, iBY, 28, iBH, iMinusCode, "", 1)
		self.addButton("TRSp" + szTag, u"+", False, iX + self.BLOCK_SPIN_W - 28 - 7, iBY, 28, iBH, iPlusCode, "", -1)
		screen.setLabelAt("TRSv" + szTag, self.BACKGROUND_ID, u"<font=3><color=255,255,255>" + unicode(iValue) + u"</color></font>", CvUtil.FONT_CENTER_JUSTIFY, (iX - self.OX) + self.BLOCK_SPIN_W / 2, (iY - self.OY) + (self.ROW_H - 22) / 2, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)

	def refreshRow(self, iSlot):
		# only the changed row is drawn again: all of them (cheap enough, the list is short)
		self.drawRows()

	def clearSlot(self, iSlot):
		self.drop("TRSIcon" + str(iSlot))
		for iBlock in range(2):
			self.removeButton("TRSm" + str(iSlot) + "_" + str(iBlock))
			self.removeButton("TRSp" + str(iSlot) + "_" + str(iBlock))
			self.drop("TRSv" + str(iSlot) + "_" + str(iBlock))
		for szTag in ("2", "3", "4", "5", "8", "9", "10", "11", "fe", "ff"):
			self.removeButton("TRSc" + str(iSlot) + "_" + szTag)

	def clearRows(self):
		for iSlot in range(self.iVisible):
			self.clearSlot(iSlot)

	def getNumPages(self):
		return max(1, (len(self.aYields) + self.iVisible - 1) / self.iVisible)

	def drawPage(self):
		if len(self.aYields) <= self.iVisible:
			return
		szText = u"<font=3b>" + localText.getText("TXT_KEY_WTP_TRADEROUTE_PAGE", (self.iFirst / self.iVisible + 1, self.getNumPages())) + u"</font>"
		self.pHost.setLabelAt("TRSPage", self.BACKGROUND_ID, szText, CvUtil.FONT_CENTER_JUSTIFY, 24 + 36 + 75, self.H - 40, 0, FontTypes.GAME_FONT, WidgetTypes.WIDGET_GENERAL, -1, -1)

	# iDelta pages forward / back
	def scroll(self, iDelta):
		iPage = (self.iFirst / self.iVisible + iDelta) % self.getNumPages() # (endless: after the last page the first one follows and vice versa)
		if iPage * self.iVisible != self.iFirst:
			self.iFirst = iPage * self.iVisible
			self.drawRows()
			self.drawPage()

	def changeValue(self, iSlot, iBlock, iDelta):
		iIndex = self.iFirst + iSlot
		if iIndex >= len(self.aYields):
			return
		d = self.dData[self.aYields[iIndex]]
		dOld = dict(d)
		szKey = "impLimit"
		if iBlock == 1:
			szKey = "maintain"
		d[szKey] = max(0, min(MAX_VALUE, d[szKey] + iDelta))
		self.checkMarketChange(self.aYields[iIndex], dOld) # (before the redraw: a notice keeps the preset on until it is answered)
		self.drawRows()

	def toggleField(self, iSlot, iField):
		iIndex = self.iFirst + iSlot
		if iIndex >= len(self.aYields):
			return
		d = self.dData[self.aYields[iIndex]]
		dOld = dict(d)
		if iField == F_IMP_CHECK:
			d["imp"] = not d["imp"]
			if not d["imp"]:
				d["feeder"] = False # (the game keeps the import on as long as the feeder is on)
		elif iField == F_IMP_FEEDER:
			d["feeder"] = not d["feeder"]
			if d["feeder"]:
				d["imp"] = True # (the game switches the import on with the feeder)
		elif iField == F_IMP_LAND:
			d["impDom"] = (d["impDom"] ^ 1) & 1
		elif iField == F_IMP_SEA:
			d["impDom"] = (d["impDom"] ^ 2) & 2
		elif iField == F_EXP_CHECK:
			d["exp"] = not d["exp"]
		elif iField == F_EXP_AUTO:
			d["auto"] = not d["auto"]
		elif iField == F_EXP_LAND:
			d["expDom"] = (d["expDom"] ^ 1) & 1
		elif iField == F_EXP_SEA:
			d["expDom"] = (d["expDom"] ^ 2) & 2
		self.checkMarketChange(self.aYields[iIndex], dOld) # (before the redraw: a notice keeps the preset on until it is answered)
		self.drawRows()

	def apply(self):
		pCity = self.getCity()
		if pCity == None or pCity.isNone():
			return
		for iYield in self.dData.keys():
			d = self.dData[iYield]
			if (d["imp"] != pCity.isImport(iYield) or d["exp"] != pCity.isExport(iYield) or d["feeder"] != pCity.isImportFeeder(iYield)
				or d["auto"] != pCity.isAutoExport(iYield) or d["impDom"] != pCity.getImportDomains(iYield)
				or d["expDom"] != pCity.getExportDomains(iYield) or d["maintain"] != pCity.getMaintainLevel(iYield)
				or d["impLimit"] != pCity.getImportsLimit(iYield)):
				iData1 = iYield | (d["impDom"] << 8) | (d["expDom"] << 10)
				# (see NetworkDataTradeRouteInts: the import limit in the lower, the maintain level in the upper 16 bits)
				iData2 = (d["impLimit"] & 0xFFFF) | ((d["maintain"] & 0xFFFF) << 16)
				if iData2 >= 2147483648L:
					iData2 = iData2 - 4294967296L
				CyMessageControl().sendDoTask(self.iCity, TaskTypes.TASK_YIELD_TRADEROUTE, iData1, int(iData2), d["imp"], d["exp"], d["feeder"], d["auto"])

	def favClicked(self, iSlot):
		iIndex = self.iFirst + iSlot
		if iIndex < len(self.aYields):
			self.toggleFav(self.aYields[iIndex])

	# the tooltip of a widget of the window (CvScreensInterface.getWidgetHelp); empty text: none
	def getHelp(self, iCode):
		if iCode == BTN_VIEW:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_VIEW_HELP", ())
		if iCode == BTN_SEARCH:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_SEARCH_HELP", ())
		if iCode >= BTN_MOVE and iCode < BTN_MOVE + 4:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_MOVE_HELP", (self.OX, self.OY))
		if iCode == BTN_CLEAR_SEARCH:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_SEARCH_CLEAR_HELP", ())
		if iCode >= BTN_FAV_IMP and iCode < BTN_FAV_IMP + 80:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_FAVORITE_HELP", ())
		if iCode >= BTN_FAV_EXP and iCode < BTN_FAV_EXP + 80:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_FAVORITE_HELP", ())
		if iCode >= BTN_FILTER and iCode < BTN_FILTER + 80:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_FILTER_HELP", ())
		if iCode == BTN_UP:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_PAGE_PREV_HELP", ())
		if iCode == BTN_DOWN:
			return localText.getText("TXT_KEY_WTP_TRADEROUTE_PAGE_NEXT_HELP", ())
		if iCode >= BTN_ROW:
			iField = (iCode - BTN_ROW) % 16
			aszKey = {F_IMP_MINUS: "TXT_KEY_WTP_TRADEROUTE_WIN_IMPORT_HELP", F_IMP_PLUS: "TXT_KEY_WTP_TRADEROUTE_WIN_IMPORT_HELP", F_IMP_CHECK: "TXT_KEY_WTP_TRADEROUTE_WIN_IMPORT_HELP", F_IMP_FEEDER: "TXT_KEY_WTP_TRADEROUTE_WIN_FEEDER_HELP", F_IMP_LAND: "TXT_KEY_POPUP_IMPORT_LAND_HELP", F_IMP_SEA: "TXT_KEY_POPUP_IMPORT_SEA_HELP", F_EXP_MINUS: "TXT_KEY_WTP_TRADEROUTE_WIN_EXPORT_HELP", F_EXP_PLUS: "TXT_KEY_WTP_TRADEROUTE_WIN_EXPORT_HELP", F_EXP_CHECK: "TXT_KEY_WTP_TRADEROUTE_WIN_EXPORT_HELP", F_EXP_AUTO: "TXT_KEY_WTP_TRADEROUTE_WIN_AUTO_EXPORT_HELP", F_EXP_LAND: "TXT_KEY_POPUP_EXPORT_LAND_HELP", F_EXP_SEA: "TXT_KEY_POPUP_EXPORT_SEA_HELP"}
			if aszKey.has_key(iField):
				return localText.getText(aszKey[iField], ())
		if iCode >= BTN_PRESET and iCode < BTN_PRESET + 7:
			aszKey = ["TXT_KEY_WTP_TRADEROUTE_PRESET0_HELP", "TXT_KEY_WTP_TRADEROUTE_PRESET1_HELP", "TXT_KEY_WTP_TRADEROUTE_PRESET2_HELP", "TXT_KEY_WTP_TRADEROUTE_WIN_PRESET_BUILD_HELP", "TXT_KEY_TRADEROUTE_PRESET_MARKET_AUTO", "TXT_KEY_WTP_TRADEROUTE_PRESET5_HELP", "TXT_KEY_WTP_TRADEROUTE_PRESET6_HELP"]
			if iCode - BTN_PRESET == 4:
				pCity = self.getCity()
				if pCity != None and not pCity.isNone() and pCity.isAutoMarketImport():
					return localText.getText("TXT_KEY_TRADEROUTE_PRESET_MARKET_AUTO_OFF", ()) + localText.getText("TXT_KEY_WTP_TRADEROUTE_MARKET_VIEW_HINT", ())
				return localText.getText(aszKey[iCode - BTN_PRESET], ()) + localText.getText("TXT_KEY_WTP_TRADEROUTE_MARKET_VIEW_HINT", ())
			if iCode - BTN_PRESET == 3 or iCode - BTN_PRESET >= 5:
				return localText.getText(aszKey[iCode - BTN_PRESET], ()) + localText.getText("TXT_KEY_WTP_TRADEROUTE_BUILD_PROTECT_HINT", ())
			return localText.getText(aszKey[iCode - BTN_PRESET], ())
		return u""

	# a preset: the changes of the window are sent first, the window stays open and shows the result a moment later
	# clear all / import all goods / auto-export all goods for the goods of the current filter only (all pages of the view / search)
	def runFilteredPreset(self, iPreset):
		aSkipped = []
		dOldAll = {}
		for iYield in self.aYields:
			dOldAll[iYield] = dict(self.dData[iYield])
		for iYield in self.aYields:
			d = self.dData[iYield]
			if self.isMarketLocked(iYield):
				# market automatic manages the good: only a manual change touches it (import all changes nothing there)
				if iPreset == 0 or (iPreset == 2 and not d["auto"]):
					aSkipped.append(iYield)
				continue
			if iPreset == 0:
				d["imp"] = False
				d["feeder"] = False
				d["exp"] = False
				d["auto"] = False
				d["impDom"] = 0
				d["expDom"] = 0
				d["maintain"] = 0
				d["impLimit"] = 0
			elif iPreset == 1:
				d["imp"] = True
			else:
				d["auto"] = True
		self.apply()
		if self.iView == VIEW_MARKED:
			self.buildView()
			self.drawPage()
		self.warnSkipped(aSkipped)
		if iPreset == 0:
			self.checkPresetLost(self.aYields, True, dOldAll)
		self.drawRows() # (after the notices: with one open a preset stays on until it is answered)
		self.iReload = 60

	def runPreset(self, iPreset):
		if iPreset == 3 or iPreset == 5 or iPreset == 6:
			for p in PRESETS:
				if p["code"] == iPreset:
					self.toggleBuild(p)
			return
		if iPreset == 4:
			self.toggleMarket()
			return
		try:
			if iPreset <= 2 and (len(self.aYields) != len(self.aAllYields) or self.isMarketOn() or self.isBuildOn()):
				# only the goods of the current view (all pages); with market automatic on also here: the goods it manages stay as they are
				self.runFilteredPreset(iPreset)
				return
			self.apply()
			if iPreset <= 2:
				# 0: clear all, 1: import all, 2: auto export all
				CyMessageControl().sendDoTask(self.iCity, TaskTypes.TASK_AUTO_TRADEROUTE, 0, 0, iPreset == 0, iPreset == 1, iPreset == 2, False)
			else:
				CyMessageControl().sendDoTask(self.iCity, TaskTypes.TASK_TRADEROUTE_PRESET, iPreset - 3, 0, False, False, False, False)
		except:
			import traceback
			logTrade(traceback.format_exc())
		self.iReload = 60

	def teardownLayout(self):
		try:
			for szName in self.aWarnDrawn:
				self.drop(szName)
			self.aWarnDrawn = []
			self.clearRows()
			self.clearHover()
			for szName in self.dBtn.keys():
				self.removeButton(szName)
			for szName in self.aDrawn:
				self.drop(szName)
			for szName in ("TRSOk", "TRSCancel", "TRSUp", "TRSDown", "TRSPage", "TRSSearchText", "TRSSearchBG", "TRSHeadImp", "TRSHeadExp", "TRSTitle", "TRSHint", "TRSBack1", "TRSBack2", self.BACKGROUND_ID):
				self.drop(szName)
			for i in range(7):
				self.drop("TRSPreset" + str(i))
		except:
			import traceback
			logTrade(traceback.format_exc())
		self.dBtn = {}
		self.sHover = ""

	# the pixels of a step: normal, with Shift twice as far, with Ctrl half, with both a third
	def getMoveStep(self, bCtrl, bShift):
		if bCtrl and bShift:
			return MOVE_STEP / 3
		if bShift:
			return MOVE_STEP * 2
		if bCtrl:
			return MOVE_STEP / 2
		return MOVE_STEP

	# a step is only noted here, the window is built again once per frame (many key repeats do not pile up)
	def queueMove(self, iDir, iStep):
		self.iPendX += [-iStep, iStep, 0, 0][iDir]
		self.iPendY += [0, 0, -iStep, iStep][iDir]

	def getModifiers(self):
		try:
			return (CyInterface().ctrlKey(), CyInterface().shiftKey())
		except:
			return (False, False)

	# an arrow key goes down (the repeats of the keyboard are ignored: the held keys are handled in updateMove)
	def pressArrow(self, iDir, bCtrl, bShift):
		if iDir in self.aHeld:
			return
		self.aHeld.append(iDir)
		self.iHoldWait = MOVE_DELAY
		self.queueMove(iDir, self.getMoveStep(bCtrl, bShift))

	# Ctrl + Shift + Q: back to the default place
	def resetPosition(self):
		self.iMoveX = 0
		self.iMoveY = 0
		self.iPendX = 0
		self.iPendY = 0
		self.teardownLayout()
		self.buildLayout()

	def handleKeyUp(self, iKey):
		if iKey in self.aKeyArrows:
			iDir = self.aKeyArrows.index(iKey)
			if iDir in self.aHeld:
				self.aHeld.remove(iDir)

	# the move buttons held down: the steps go on until the mouse button is released (the first step is the click itself)
	def updateMove(self):
		try:
			bDown = CyInterface().isLeftMouseDown()
		except:
			bDown = False
		if not bDown:
			self.iMoveDir = -1
			self.bMouseWasDown = False
		elif self.iMoveDir == -1:
			if not self.bMouseWasDown:
				self.bMouseWasDown = True
				self.bRepeatDone = False
				iX = CyGame().getCursorClientX()
				iY = CyGame().getCursorClientY()
				for szName in self.dBtn.keys():
					b = self.dBtn[szName]
					if b[4] >= BTN_MOVE and b[4] < BTN_MOVE + 4 and iX >= b[0] and iX < b[0] + b[2] and iY >= b[1] and iY < b[1] + b[3]:
						self.iMoveDir = b[4] - BTN_MOVE
						self.iMoveWait = MOVE_DELAY
						break
		else:
			self.iMoveWait -= 1
			if self.iMoveWait <= 0:
				self.iMoveWait = MOVE_REPEAT
				self.bRepeatDone = True
				aMod = self.getModifiers()
				self.queueMove(self.iMoveDir, self.getMoveStep(aMod[0], aMod[1]))
		# the arrow keys held: the window goes on moving, two keys at once move it diagonally
		if len(self.aHeld) > 0:
			self.iHoldWait -= 1
			if self.iHoldWait <= 0:
				self.iHoldWait = MOVE_REPEAT
				aMod = self.getModifiers()
				for iHeld in self.aHeld:
					self.queueMove(iHeld, self.getMoveStep(aMod[0], aMod[1]))
		if self.iPendX != 0 or self.iPendY != 0:
			iX = self.iPendX
			iY = self.iPendY
			self.iPendX = 0
			self.iPendY = 0
			self.moveWindow(iX, iY)
			return 1
		return 0

	# moves the window and builds it again at the new place
	def moveWindow(self, iDX, iDY):
		self.iMoveX += iDX
		self.iMoveY += iDY
		self.teardownLayout()
		self.buildLayout()

	def finish(self, bOk, iPreset):
		if self.bFinished:
			return
		if bOk:
			try:
				self.apply()
				if iPreset >= 0 and iPreset <= 2:
					# 0: clear all, 1: import all, 2: auto export all
					CyMessageControl().sendDoTask(self.iCity, TaskTypes.TASK_AUTO_TRADEROUTE, 0, 0, iPreset == 0, iPreset == 1, iPreset == 2, False)
				elif iPreset >= 3:
					CyMessageControl().sendDoTask(self.iCity, TaskTypes.TASK_TRADEROUTE_PRESET, iPreset - 3, 0, False, False, False, False)
			except:
				import traceback
				logTrade(traceback.format_exc())
		self.bFinished = True
		try:
			CyGame().setWheelCapture(False)
		except:
			pass
		self.teardownLayout()
		# the interface is redrawn completely afterwards
		for szBit in ("MiscButtons_DIRTY_BIT", "GameData_DIRTY_BIT", "ResourceTable_DIRTY_BIT", "Minimap_Section_DIRTY_BIT", "Help_DIRTY_BIT", "InfoPane_DIRTY_BIT", "SelectionButtons_DIRTY_BIT", "CityScreen_DIRTY_BIT"):
			try:
				CyInterface().setDirty(getattr(InterfaceDirtyBits, szBit), True)
			except:
				pass
		self.pHost = None

	# a key down event (CvEventManager.onKbdEvent gives them to the window while it is open)
	def handleKey(self, iKey, bCtrl, bShift = False, bAlt = False):
		if bAlt and iKey != self.iKeyEsc:
			# Alt+Tab (switching out of the game) must not count as Tab (accept the suggestion) or as typing
			return
		if iKey == self.iKeyEsc:
			self.finish(False, -1)
		elif bCtrl and bShift and iKey == self.getKeyId("KB_Q"):
			self.resetPosition()
		elif iKey in self.aKeyArrows:
			self.pressArrow(self.aKeyArrows.index(iKey), bCtrl, bShift)
		else:
			self.handleSearchKey(iKey, bShift)

	# after an error in a key: the search state is made consistent again and the window is built again
	def recoverFromError(self):
		self.syncFilter()
		self.findSuggestion()
		if self.iView == VIEW_FILTER:
			self.buildView()
		self.tLayout = (-1, False)
		self.refreshList()
		self.drawSearchText()

	# the clicks on the buttons of the window; returns 1 if the event was for it
	def handleEmbeddedInput(self, inputClass):
		if int(inputClass.getNotifyCode()) == int(NotifyCode.NOTIFY_LISTBOX_ITEM_SELECTED) and inputClass.getFunctionName() == "TRSView":
			iIndex = self.pHost.getSelectedPullDownID("TRSView")
			self.setView(self.pHost.getPullDownData("TRSView", iIndex))
			return 1
		if int(inputClass.getNotifyCode()) != int(NotifyCode.NOTIFY_CLICKED) or inputClass.getButtonType() != WidgetTypes.WIDGET_GENERAL:
			return 0
		iData = inputClass.getData1()
		if iData < BTN_OK or iData >= BTN_ROW + 16 * 64:
			return 0
		bCtrl = inputClass.isCtrlKeyDown()
		iStep = STEP
		if bCtrl:
			iStep = STEP_CTRL
		if iData == BTN_OK:
			self.finish(True, -1)
		elif iData == BTN_CANCEL:
			self.finish(False, -1)
		elif iData >= BTN_MOVE and iData < BTN_MOVE + 4:
			if self.bRepeatDone:
				self.bRepeatDone = False # (the release after the window was moved by holding the button)
			else:
				aMod = self.getModifiers()
				self.queueMove(iData - BTN_MOVE, self.getMoveStep(aMod[0], aMod[1]))
		elif iData == BTN_WARN_RESET:
			if self.tWarn != None and self.tWarn[2] >= 0:
				self.resetMarketGood(self.tWarn[2])
			elif self.tWarn != None and len(self.tWarn[3]) > 0:
				aGoods = self.tWarn[3]
				self.resetPresetGoods(aGoods)
				self.hideWarn()
				self.drawRows()
		elif iData == BTN_WARN_OK:
			if self.tWarn != None and len(self.tWarn[3]) > 0:
				self.ignorePresetGoods(self.tWarn[3])
			self.hideWarn()
			self.drawRows()
		elif iData == BTN_CLEAR_SEARCH:
			self.szQuery = u""
			self.aConfirmed = []
			self.searchChanged()
		elif iData >= BTN_FILTER and iData < BTN_FILTER + 80:
			self.filterClicked(iData - BTN_FILTER)
		elif iData == BTN_SEARCH:
			self.drawSearchText()
		elif iData == BTN_UP:
			self.scroll(-1)
		elif iData == BTN_DOWN:
			self.scroll(1)
		elif iData >= BTN_PRESET and iData < BTN_PRESET + 7:
			self.runPreset(iData - BTN_PRESET)
		elif iData >= BTN_FAV_IMP and iData < BTN_FAV_IMP + 80:
			self.favClicked(iData - BTN_FAV_IMP)
		elif iData >= BTN_FAV_EXP and iData < BTN_FAV_EXP + 80:
			self.favClicked(iData - BTN_FAV_EXP)
		elif iData >= BTN_ROW:
			iSlot = (iData - BTN_ROW) / 16
			iField = (iData - BTN_ROW) % 16
			if iField == F_IMP_MINUS:
				self.changeValue(iSlot, 0, -iStep)
			elif iField == F_IMP_PLUS:
				self.changeValue(iSlot, 0, iStep)
			elif iField == F_EXP_MINUS:
				self.changeValue(iSlot, 1, -iStep)
			elif iField == F_EXP_PLUS:
				self.changeValue(iSlot, 1, iStep)
			else:
				self.toggleField(iSlot, iField)
		else:
			return 0
		return 1

	# the mouse wheel (collected by the DLL while the window is open): over a number it changes it, elsewhere it scrolls the list
	def update(self, fDelta):
		if self.bFinished:
			return 0
		try:
			if self.updateMove():
				return 0
			self.updateHover()
			if self.iReload > 0:
				self.iReload -= 1
				if self.iReload % 10 == 0:
					self.reloadFromCity()
			iNotches = CyGame().takeWheelNotches()
			if iNotches == 0:
				return 0
			iX = CyGame().getCursorClientX() - self.OX
			iY = CyGame().getCursorClientY() - self.OY
			iStep = STEP
			if CyGame().isCtrlKeyPressed():
				iStep = STEP_CTRL
			iSlot = (iY - self.LIST_Y) / self.ROW_H
			iBlock = -1
			if iY >= self.LIST_Y and iSlot >= 0 and iSlot < self.iVisible:
				if iX >= self.BLOCK_IMP_X and iX < self.BLOCK_IMP_X + self.BLOCK_SPIN_W:
					iBlock = 0
				elif iX >= self.BLOCK_EXP_X and iX < self.BLOCK_EXP_X + self.BLOCK_SPIN_W:
					iBlock = 1
			for i in range(abs(iNotches)):
				if iBlock >= 0:
					if iNotches > 0:
						self.changeValue(iSlot, iBlock, iStep)
					else:
						self.changeValue(iSlot, iBlock, -iStep)
				else:
					if iNotches > 0:
						self.scroll(-1)
					else:
						self.scroll(1)
		except:
			import traceback
			logTrade(traceback.format_exc())
		return 0

	def onClose(self):
		self.bFinished = True
		try:
			CyGame().setWheelCapture(False)
		except:
			pass
		return 0

