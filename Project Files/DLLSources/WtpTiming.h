#pragma once

#ifndef WTP_TIMING_H
#define WTP_TIMING_H

// WTP: lightweight turn timing + runtime settings (no rebuild needed to switch).
//
// Writes "WTP_Timing.txt" into the mod folder: one block per turn change with the time (ms) spent in the big parts of the
// turn processing (inclusive times, nested parts overlap on purpose, e.g. path searches are also part of the unit AI).
// Only the main thread is measured, worker threads are ignored, so the timing itself never touches shared data.
//
// Report format 2 (per turn change): the game (map size, players, cities, units), the timed parts with the longest single call
// (a long single call freezes the screen), a histogram of the single CvGame::updateMoves calls, the path searches by the unit AI
// that asked for them, the slowest single unit updates (owner, unit, plot, path search part), a table per player and counters of the
// workforce plan (colonists, jobs, rounds, colony scans).
//
// Reads "WTP_Settings.txt" from the mod folder at every turn change (created with defaults when missing), so values can be
// changed while the game is running:
//   PathfinderParallel=1     1 = child nodes of the path search are expanded with TBB, 0 = always serial (default, faster in the measurements)
//   PathfinderMinChildren=0  parallel only when at least this many child nodes have to be expanded in one step
//
// Remove the following define to compile all timing out. The settings keep working.
#define WTP_TIMING

namespace WtpTiming
{
	enum Slot
	{
		SLOT_GAME_DOTURN,
		SLOT_GAME_UPDATEMOVES,
		SLOT_MAP_DOTURN,
		SLOT_TEAM_DOTURN,
		SLOT_PLAYER_DOTURN,
		SLOT_PLAYER_DOTURNUNITS,
		SLOT_AI_DOTURNPRE,
		SLOT_AI_DOTURNPOST,
		SLOT_AI_DOTURNUNITSPRE,
		SLOT_AI_DOTURNUNITSPOST,
		SLOT_AI_UNITUPDATE,
		SLOT_CITY_DOTURN,
		SLOT_CITYAI_DOTURN,
		SLOT_ASSIGN_WORKING_PLOTS,
		SLOT_TRADE_ROUTES,
		SLOT_PATH_GENERATE,
		SLOT_PRE_DOCOUNTER,
		SLOT_PRE_DOENEMYUNITDATA,
		SLOT_PRE_DOEMOTIONS,
		SLOT_PRE_DOUNITAIWEIGHTS,
		SLOT_PRE_DOMILITARY,
		SLOT_PRE_DOSTRATEGY,
		SLOT_PRE_UPDATEYIELDVALUES,
		SLOT_PRE_DOCITIZENRELOCATION,
		SLOT_PRE_DOPEACEWARSHIPS,
		SLOT_PRE_UPDATEFULLSTORAGE,
		SLOT_PRE_DOWORKFORCEPLAN,
		SLOT_PRE_DORECLAIMTERRITORY,
		SLOT_PRE_DOSURPLUSPIONEERS,
		SLOT_PRE_DONATIVEMERCDEFENSE,
		SLOT_PRE_LOGSTATUSSUMMARY,
		SLOT_WF_TRAVEL,
		SLOT_WF_PLAN,
		SLOT_WF_S0,
		SLOT_WF_S1,
		SLOT_WF_S2,
		SLOT_WF_S3SETUP,
		SLOT_WF_S4,
		SLOT_WF_S5,
		SLOT_COUNT
	};

	// timed per player (table "per player")
	enum PlayerSlot
	{
		PS_DOTURN,
		PS_AI_DOTURNPRE,
		PS_AI_DOTURNPOST,
		PS_AI_UNITUPDATE,
		PS_WORKFORCEPLAN,
		PS_COUNT
	};

	static const char* const g_aszPlayerSlotNames[PS_COUNT] =
	{
		"doTurn",
		"AI_doTurnPre",
		"AI_doTurnPost",
		"AI_unitUpdate",
		"WorkforcePlan"
	};

	// counters (summed over the turn change)
	enum Counter
	{
		CNT_WF_PLANS,
		CNT_WF_COLONIES,
		CNT_WF_WORKERS,
		CNT_WF_JOBS,
		CNT_WF_ROUNDS,
		CNT_WF_COLONY_SCANS,
		CNT_COUNT
	};

	static const char* const g_aszCounterNames[CNT_COUNT] =
	{
		"workforce plans made (one per AI player)",
		"colonies in the plans",
		"free colonists (workers) in the plans",
		"free jobs in the plans",
		"rounds of step 3 (one pair assigned per round)",
		"colony scans in step 3 (colonies searched again after an assignment)"
	};

	// buckets of the single updateMoves calls (ms, upper limits)
	enum { FREEZE_BUCKETS = 5 };
	static const int g_aiFreezeLimit[FREEZE_BUCKETS] = { 50, 200, 1000, 5000, 0 };

	enum { TOP_UNITS = 8 };

	static const char* const g_aszSlotNames[SLOT_COUNT] =
	{
		"CvGame::doTurn",
		"CvGame::updateMoves",
		"CvMap::doTurn",
		"CvTeam::doTurn",
		"CvPlayer::doTurn",
		"CvPlayer::doTurnUnits",
		"CvPlayerAI::AI_doTurnPre",
		"CvPlayerAI::AI_doTurnPost",
		"CvPlayerAI::AI_doTurnUnitsPre",
		"CvPlayerAI::AI_doTurnUnitsPost",
		"CvPlayerAI::AI_unitUpdate",
		"CvCity::doTurn",
		"CvCityAI::AI_doTurn",
		"CvPlayerAI::AI_assignWorkingPlots",
		"CvSelectionGroupAI::AI_tradeRoutes",
		"KmodPathFinder::GeneratePath (all path searches)",
		"  in AI_doTurnPre: AI_doCounter",
		"  in AI_doTurnPre: AI_doEnemyUnitData",
		"  in AI_doTurnPre: AI_doEmotions",
		"  in AI_doTurnPre: AI_doUnitAIWeights",
		"  in AI_doTurnPre: AI_doMilitary",
		"  in AI_doTurnPre: AI_doStrategy",
		"  in AI_doTurnPre: AI_updateYieldValues",
		"  in AI_doTurnPre: AI_doCitizenRelocation",
		"  in AI_doTurnPre: AI_doPeaceWarships",
		"  in AI_doTurnPre: AI_updateFullStorage",
		"  in AI_doTurnPre: AI_doWorkforcePlan",
		"  in AI_doTurnPre: AI_doReclaimTerritory",
		"  in AI_doTurnPre: AI_doSurplusPioneers",
		"  in AI_doTurnPre: AI_doNativeMercDefense",
		"  in AI_doTurnPre: AI_logStatusSummary",
		"    in AI_doWorkforcePlan: AI_wfUpdateTravel (travel times of the colonies)",
		"    in AI_doWorkforcePlan: target plan (step 3, pairs of colonist and job)",
		"      workforce plan step 0 (experts without raw material)",
		"      workforce plan step 1 (jobs, incl. travel times)",
		"      workforce plan step 2 (workforce)",
		"      workforce plan step 3 set-up (before the pairs are chosen)",
		"      workforce plan step 4 (seats now)",
		"      workforce plan step 5 (carry out)"
	};

	struct Data
	{
		bool bInit;
		DWORD iMainThread;
		__int64 iFrequency;
		__int64 aiTicks[SLOT_COUNT];
		__int64 aiCalls[SLOT_COUNT];
		int aiDepth[SLOT_COUNT];
		__int64 aiMaxTicks[SLOT_COUNT];
		__int64 aiUnitTicks[2][NUM_UNITAI_TYPES + 1];
		__int64 aiUnitCalls[2][NUM_UNITAI_TYPES + 1];
		__int64 aiUnitMaxTicks[2][NUM_UNITAI_TYPES + 1];
		// path searches by the unit AI that was running (index NUM_UNITAI_TYPES: unknown type)
		__int64 aiUnitPathTicks[2][NUM_UNITAI_TYPES + 1];
		__int64 aiUnitPathCalls[2][NUM_UNITAI_TYPES + 1];
		__int64 aiUnitPathMaxTicks[2][NUM_UNITAI_TYPES + 1];
		__int64 iNoUnitPathTicks;
		__int64 iNoUnitPathCalls;
		__int64 iNoUnitPathMaxTicks;
		// the unit AI that is running now (-1: none) and the running totals of the path searches (for the slowest-units table)
		int iCurUnitAI;
		int iCurNative;
		__int64 iPathTicksRun;
		__int64 iPathCallsRun;
		// single updateMoves calls
		__int64 aiFreezeCalls[FREEZE_BUCKETS];
		__int64 aiFreezeTicks[FREEZE_BUCKETS];
		// the slowest single unit updates
		struct TopUnit
		{
			__int64 iTicks;
			__int64 iPathTicks;
			__int64 iPathCalls;
			int iUnitAI;
			int iNative;
			int iOwner;
			int iID;
			int iX;
			int iY;
		};
		TopUnit aTopUnits[TOP_UNITS];
		int iNumTopUnits;
		// per player
		__int64 aiPlayerTicks[PS_COUNT][MAX_PLAYERS];
		__int64 aiPlayerCalls[PS_COUNT][MAX_PLAYERS];
		__int64 aiPlayerMaxTicks[PS_COUNT][MAX_PLAYERS];
		bool abPlayerInfo[MAX_PLAYERS];
		char acPlayerType[MAX_PLAYERS];
		int aiPlayerCities[MAX_PLAYERS];
		int aiPlayerUnits[MAX_PLAYERS];
		char aszPlayerName[MAX_PLAYERS][40];
		int iMapWidth;
		int iMapHeight;
		__int64 aiCounter[CNT_COUNT];
		int iPathfinderParallel;
		int iPathfinderMinChildren;
	};

	inline Data& data()
	{
		static Data kData; // zero initialized
		if (!kData.bInit)
		{
			kData.bInit = true;
			kData.iCurUnitAI = -1;
			kData.iCurNative = 0;
			kData.iPathfinderParallel = 0; // measured: serial is about 25-30% faster in the late game
			kData.iPathfinderMinChildren = 0;
			LARGE_INTEGER kFreq;
			kFreq.QuadPart = 0;
			QueryPerformanceFrequency(&kFreq);
			kData.iFrequency = (kFreq.QuadPart > 0) ? kFreq.QuadPart : 1;
		}
		return kData;
	}

	inline __int64 now()
	{
		LARGE_INTEGER kNow;
		kNow.QuadPart = 0;
		QueryPerformanceCounter(&kNow);
		return kNow.QuadPart;
	}

	// settings, used by the path finder (read on the main thread only at turn change, plain ints are fine)
	inline bool pathfinderParallel(size_t iNumChildren)
	{
		const Data& kData = data();
		return kData.iPathfinderParallel != 0 && (int)iNumChildren >= kData.iPathfinderMinChildren;
	}

#ifdef WTP_TIMING
	inline void addFreeze(__int64 iTicks)
	{
		Data& kData = data();
		const double dMs = 1000.0 * (double)iTicks / (double)kData.iFrequency;
		int iBucket = FREEZE_BUCKETS - 1;
		for (int i = 0; i < FREEZE_BUCKETS - 1; i++)
		{
			if (dMs < (double)g_aiFreezeLimit[i])
			{
				iBucket = i;
				break;
			}
		}
		kData.aiFreezeCalls[iBucket]++;
		kData.aiFreezeTicks[iBucket] += iTicks;
	}

	// a path search (outermost call) ended: add it to the unit AI that asked for it
	inline void addPathSearch(__int64 iTicks)
	{
		Data& kData = data();
		kData.iPathTicksRun += iTicks;
		kData.iPathCallsRun++;
		if (kData.iCurUnitAI >= 0)
		{
			kData.aiUnitPathTicks[kData.iCurNative][kData.iCurUnitAI] += iTicks;
			kData.aiUnitPathCalls[kData.iCurNative][kData.iCurUnitAI]++;
			if (iTicks > kData.aiUnitPathMaxTicks[kData.iCurNative][kData.iCurUnitAI])
			{
				kData.aiUnitPathMaxTicks[kData.iCurNative][kData.iCurUnitAI] = iTicks;
			}
		}
		else
		{
			kData.iNoUnitPathTicks += iTicks;
			kData.iNoUnitPathCalls++;
			if (iTicks > kData.iNoUnitPathMaxTicks)
			{
				kData.iNoUnitPathMaxTicks = iTicks;
			}
		}
	}

	class Scope
	{
	public:
		explicit Scope(Slot eSlot) : m_eSlot(eSlot), m_iStart(0), m_bActive(false)
		{
			Data& kData = data();
			if (kData.iMainThread != 0 && kData.iMainThread == GetCurrentThreadId())
			{
				m_bActive = true;
				if (kData.aiDepth[m_eSlot]++ == 0)
				{
					m_iStart = now();
				}
			}
		}
		~Scope()
		{
			if (m_bActive)
			{
				Data& kData = data();
				kData.aiCalls[m_eSlot]++;
				if (--kData.aiDepth[m_eSlot] == 0)
				{
					const __int64 iTicks = now() - m_iStart;
					kData.aiTicks[m_eSlot] += iTicks;
					if (iTicks > kData.aiMaxTicks[m_eSlot])
					{
						kData.aiMaxTicks[m_eSlot] = iTicks;
					}
					if (m_eSlot == SLOT_GAME_UPDATEMOVES)
					{
						addFreeze(iTicks);
					}
					else if (m_eSlot == SLOT_PATH_GENERATE)
					{
						addPathSearch(iTicks);
					}
				}
			}
		}
	private:
		Slot m_eSlot;
		__int64 m_iStart;
		bool m_bActive;
	};

	// consecutive parts of one function: next() ends the part that runs and starts the next one, the destructor ends the last one
	// (also on an early return). Use it for slots that are not nested in a Scope of the same slot.
	class Lap
	{
	public:
		explicit Lap(Slot eSlot) : m_eSlot(eSlot), m_iStart(0), m_bActive(false)
		{
			open();
		}
		void next(Slot eSlot)
		{
			close();
			m_eSlot = eSlot;
			open();
		}
		~Lap()
		{
			close();
		}
	private:
		void open()
		{
			Data& kData = data();
			if (kData.iMainThread != 0 && kData.iMainThread == GetCurrentThreadId())
			{
				m_bActive = true;
				m_iStart = now();
			}
		}
		void close()
		{
			if (m_bActive)
			{
				Data& kData = data();
				const __int64 iTicks = now() - m_iStart;
				kData.aiCalls[m_eSlot]++;
				kData.aiTicks[m_eSlot] += iTicks;
				if (iTicks > kData.aiMaxTicks[m_eSlot])
				{
					kData.aiMaxTicks[m_eSlot] = iTicks;
				}
				m_bActive = false;
			}
		}
		Slot m_eSlot;
		__int64 m_iStart;
		bool m_bActive;
	};

	// one entry per unit AI type (natives separately)
	class UnitScope
	{
	public:
		UnitScope(int iUnitAI, bool bNative, int iOwner, int iID, int iX, int iY)
			: m_iUnitAI(iUnitAI), m_iNative(bNative ? 1 : 0), m_iOwner(iOwner), m_iID(iID), m_iX(iX), m_iY(iY), m_iStart(0),
			m_iPathTicks(0), m_iPathCalls(0), m_iPrevAI(-1), m_iPrevNative(0), m_bActive(false)
		{
			Data& kData = data();
			if (kData.iMainThread != 0 && kData.iMainThread == GetCurrentThreadId())
			{
				if (m_iUnitAI < 0 || m_iUnitAI >= NUM_UNITAI_TYPES)
				{
					m_iUnitAI = NUM_UNITAI_TYPES;
				}
				m_bActive = true;
				m_iPrevAI = kData.iCurUnitAI;
				m_iPrevNative = kData.iCurNative;
				kData.iCurUnitAI = m_iUnitAI;
				kData.iCurNative = m_iNative;
				m_iPathTicks = kData.iPathTicksRun;
				m_iPathCalls = kData.iPathCallsRun;
				m_iStart = now();
			}
		}
		~UnitScope()
		{
			if (m_bActive)
			{
				Data& kData = data();
				const __int64 iTicks = now() - m_iStart;
				kData.aiUnitCalls[m_iNative][m_iUnitAI]++;
				kData.aiUnitTicks[m_iNative][m_iUnitAI] += iTicks;
				if (iTicks > kData.aiUnitMaxTicks[m_iNative][m_iUnitAI])
				{
					kData.aiUnitMaxTicks[m_iNative][m_iUnitAI] = iTicks;
				}
				kData.iCurUnitAI = m_iPrevAI;
				kData.iCurNative = m_iPrevNative;

				// the slowest single updates: keep the TOP_UNITS longest
				int iSlot = -1;
				if (kData.iNumTopUnits < TOP_UNITS)
				{
					iSlot = kData.iNumTopUnits++;
				}
				else
				{
					__int64 iMin = kData.aTopUnits[0].iTicks;
					int iMinIndex = 0;
					for (int i = 1; i < TOP_UNITS; i++)
					{
						if (kData.aTopUnits[i].iTicks < iMin)
						{
							iMin = kData.aTopUnits[i].iTicks;
							iMinIndex = i;
						}
					}
					if (iTicks > iMin)
					{
						iSlot = iMinIndex;
					}
				}
				if (iSlot >= 0)
				{
					Data::TopUnit& kTop = kData.aTopUnits[iSlot];
					kTop.iTicks = iTicks;
					kTop.iPathTicks = kData.iPathTicksRun - m_iPathTicks;
					kTop.iPathCalls = kData.iPathCallsRun - m_iPathCalls;
					kTop.iUnitAI = m_iUnitAI;
					kTop.iNative = m_iNative;
					kTop.iOwner = m_iOwner;
					kTop.iID = m_iID;
					kTop.iX = m_iX;
					kTop.iY = m_iY;
				}
			}
		}
	private:
		int m_iUnitAI;
		int m_iNative;
		int m_iOwner;
		int m_iID;
		int m_iX;
		int m_iY;
		__int64 m_iStart;
		__int64 m_iPathTicks;
		__int64 m_iPathCalls;
		int m_iPrevAI;
		int m_iPrevNative;
		bool m_bActive;
	};

	// time of one part per player
	class PlayerScope
	{
	public:
		PlayerScope(PlayerSlot eSlot, int iPlayer) : m_eSlot(eSlot), m_iPlayer(iPlayer), m_iStart(0), m_bActive(false)
		{
			Data& kData = data();
			if (kData.iMainThread != 0 && kData.iMainThread == GetCurrentThreadId() && iPlayer >= 0 && iPlayer < MAX_PLAYERS)
			{
				m_bActive = true;
				m_iStart = now();
			}
		}
		~PlayerScope()
		{
			if (m_bActive)
			{
				Data& kData = data();
				const __int64 iTicks = now() - m_iStart;
				kData.aiPlayerCalls[m_eSlot][m_iPlayer]++;
				kData.aiPlayerTicks[m_eSlot][m_iPlayer] += iTicks;
				if (iTicks > kData.aiPlayerMaxTicks[m_eSlot][m_iPlayer])
				{
					kData.aiPlayerMaxTicks[m_eSlot][m_iPlayer] = iTicks;
				}
			}
		}
	private:
		PlayerSlot m_eSlot;
		int m_iPlayer;
		__int64 m_iStart;
		bool m_bActive;
	};

	inline void count(Counter eCounter, __int64 iValue)
	{
		Data& kData = data();
		if (kData.iMainThread != 0 && kData.iMainThread == GetCurrentThreadId())
		{
			kData.aiCounter[eCounter] += iValue;
		}
	}

	// called at the start of the turn change (CvGame::doTurn) for every living player, before flush
	inline void notePlayer(int iPlayer, char cType, int iCities, int iUnits, const char* szName)
	{
		Data& kData = data();
		if (iPlayer >= 0 && iPlayer < MAX_PLAYERS)
		{
			kData.abPlayerInfo[iPlayer] = true;
			kData.acPlayerType[iPlayer] = cType;
			kData.aiPlayerCities[iPlayer] = iCities;
			kData.aiPlayerUnits[iPlayer] = iUnits;
			strncpy(kData.aszPlayerName[iPlayer], (szName != NULL) ? szName : "", sizeof(kData.aszPlayerName[iPlayer]) - 1);
			kData.aszPlayerName[iPlayer][sizeof(kData.aszPlayerName[iPlayer]) - 1] = 0;
		}
	}

	inline void noteMap(int iWidth, int iHeight)
	{
		Data& kData = data();
		kData.iMapWidth = iWidth;
		kData.iMapHeight = iHeight;
	}
#else
	class Scope
	{
	public:
		explicit Scope(Slot) {}
	};
	class Lap
	{
	public:
		explicit Lap(Slot) {}
		void next(Slot) {}
	};
	class UnitScope
	{
	public:
		UnitScope(int, bool, int, int, int, int) {}
	};
	class PlayerScope
	{
	public:
		PlayerScope(PlayerSlot, int) {}
	};
	inline void count(Counter, __int64) {}
	inline void notePlayer(int, char, int, int, const char*) {}
	inline void noteMap(int, int) {}
#endif

	inline void readSettings(const char* szFile)
	{
		Data& kData = data();
		FILE* f = fopen(szFile, "r");
		if (f == NULL)
		{
			// create the file with defaults so it can be found and edited
			f = fopen(szFile, "w");
			if (f != NULL)
			{
				fprintf(f, "PathfinderParallel=%d\n", kData.iPathfinderParallel);
				fprintf(f, "PathfinderMinChildren=%d\n", kData.iPathfinderMinChildren);
				fclose(f);
			}
			return;
		}
		char szLine[256];
		while (fgets(szLine, sizeof(szLine), f) != NULL)
		{
			int iValue = 0;
			if (sscanf(szLine, "PathfinderParallel=%d", &iValue) == 1)
			{
				kData.iPathfinderParallel = iValue;
			}
			else if (sscanf(szLine, "PathfinderMinChildren=%d", &iValue) == 1)
			{
				kData.iPathfinderMinChildren = iValue;
			}
		}
		fclose(f);
	}

	// Call at the start of CvGame::doTurn (main thread): writes the report for everything since the last call, resets, reloads settings.
	inline void flush(int iGameTurn)
	{
		Data& kData = data();
		std::string szBase = gDLL->getModName();

		readSettings((szBase + "WTP_Settings.txt").c_str());

#ifdef WTP_TIMING
		const bool bFirst = (kData.iMainThread == 0);
		kData.iMainThread = GetCurrentThreadId();
		if (bFirst)
		{
			return;
		}

		bool bAny = false;
		for (int i = 0; i < SLOT_COUNT; i++)
		{
			bAny = bAny || kData.aiCalls[i] > 0;
		}
		if (bAny)
		{
			FILE* f = fopen((szBase + "WTP_Timing.txt").c_str(), "a");
			if (f != NULL)
			{
				const double dMs = 1000.0 / (double)kData.iFrequency;
				fprintf(f, "=== Turn change at game turn %d | PathfinderParallel=%d PathfinderMinChildren=%d | format 2 ===\n",
					iGameTurn, kData.iPathfinderParallel, kData.iPathfinderMinChildren);

				// the game
				int iNumPlayers = 0;
				int iCities = 0;
				int iUnits = 0;
				for (int iP = 0; iP < MAX_PLAYERS; iP++)
				{
					if (kData.abPlayerInfo[iP])
					{
						iNumPlayers++;
						iCities += kData.aiPlayerCities[iP];
						iUnits += kData.aiPlayerUnits[iP];
					}
				}
				fprintf(f, "game: map %d x %d, %d living players (H human, A AI colony, K king, N native), %d cities, %d units\n",
					kData.iMapWidth, kData.iMapHeight, iNumPlayers, iCities, iUnits);

				fprintf(f, "--- timed parts\nms\tcalls\tms/call\tmax ms (longest single call)\tname (inclusive, parts overlap)\n");
				for (int i = 0; i < SLOT_COUNT; i++)
				{
					if (kData.aiCalls[i] > 0)
					{
						const double dTotal = (double)kData.aiTicks[i] * dMs;
						fprintf(f, "%.1f\t%I64d\t%.3f\t%.1f\t%s\n", dTotal, kData.aiCalls[i], dTotal / (double)kData.aiCalls[i],
							(double)kData.aiMaxTicks[i] * dMs, g_aszSlotNames[i]);
					}
				}

				fprintf(f, "--- single CvGame::updateMoves calls by duration (the screen is frozen during one call)\ncalls\tms\tduration\n");
				for (int i = 0; i < FREEZE_BUCKETS; i++)
				{
					if (kData.aiFreezeCalls[i] > 0)
					{
						if (i < FREEZE_BUCKETS - 1)
						{
							fprintf(f, "%I64d\t%.1f\t< %d ms\n", kData.aiFreezeCalls[i], (double)kData.aiFreezeTicks[i] * dMs, g_aiFreezeLimit[i]);
						}
						else
						{
							fprintf(f, "%I64d\t%.1f\t>= %d ms\n", kData.aiFreezeCalls[i], (double)kData.aiFreezeTicks[i] * dMs, g_aiFreezeLimit[FREEZE_BUCKETS - 2]);
						}
					}
				}

				fprintf(f, "--- unit AI updates\nms\tcalls\tms/call\tmax ms\tname\n");
				for (int iNative = 0; iNative < 2; iNative++)
				{
					for (int iAI = 0; iAI <= NUM_UNITAI_TYPES; iAI++)
					{
						if (kData.aiUnitCalls[iNative][iAI] > 0)
						{
							const double dTotal = (double)kData.aiUnitTicks[iNative][iAI] * dMs;
							const char* szType = (iAI < NUM_UNITAI_TYPES) ? GC.getUnitAIInfo((UnitAITypes)iAI).getType() : "unknown";
							fprintf(f, "%.1f\t%I64d\t%.3f\t%.1f\tCvUnitAI::AI_update unitAI %s%s\n", dTotal, kData.aiUnitCalls[iNative][iAI],
								dTotal / (double)kData.aiUnitCalls[iNative][iAI], (double)kData.aiUnitMaxTicks[iNative][iAI] * dMs,
								szType, iNative ? " (native)" : "");
						}
					}
				}

				fprintf(f, "--- path searches by the unit AI that asked for them (outermost searches; ms only counted once)\nms\tcalls\tms/call\tmax ms\tname\n");
				for (int iNative = 0; iNative < 2; iNative++)
				{
					for (int iAI = 0; iAI <= NUM_UNITAI_TYPES; iAI++)
					{
						if (kData.aiUnitPathCalls[iNative][iAI] > 0)
						{
							const double dTotal = (double)kData.aiUnitPathTicks[iNative][iAI] * dMs;
							const char* szType = (iAI < NUM_UNITAI_TYPES) ? GC.getUnitAIInfo((UnitAITypes)iAI).getType() : "unknown";
							fprintf(f, "%.1f\t%I64d\t%.3f\t%.1f\tpaths in unitAI %s%s\n", dTotal, kData.aiUnitPathCalls[iNative][iAI],
								dTotal / (double)kData.aiUnitPathCalls[iNative][iAI], (double)kData.aiUnitPathMaxTicks[iNative][iAI] * dMs,
								szType, iNative ? " (native)" : "");
						}
					}
				}
				if (kData.iNoUnitPathCalls > 0)
				{
					const double dTotal = (double)kData.iNoUnitPathTicks * dMs;
					fprintf(f, "%.1f\t%I64d\t%.3f\t%.1f\tpaths outside of a unit AI update (workforce plan, trade routes, advisor, ...)\n", dTotal,
						kData.iNoUnitPathCalls, dTotal / (double)kData.iNoUnitPathCalls, (double)kData.iNoUnitPathMaxTicks * dMs);
				}

				if (kData.iNumTopUnits > 0)
				{
					// sort the slowest unit updates, longest first
					for (int i = 0; i < kData.iNumTopUnits; i++)
					{
						for (int j = i + 1; j < kData.iNumTopUnits; j++)
						{
							if (kData.aTopUnits[j].iTicks > kData.aTopUnits[i].iTicks)
							{
								Data::TopUnit kTmp = kData.aTopUnits[i];
								kData.aTopUnits[i] = kData.aTopUnits[j];
								kData.aTopUnits[j] = kTmp;
							}
						}
					}
					fprintf(f, "--- slowest single unit updates\nms\tpath ms\tpath calls\towner\tunit id\tplot x,y\tunitAI\n");
					for (int i = 0; i < kData.iNumTopUnits; i++)
					{
						const Data::TopUnit& kTop = kData.aTopUnits[i];
						const char* szType = (kTop.iUnitAI < NUM_UNITAI_TYPES) ? GC.getUnitAIInfo((UnitAITypes)kTop.iUnitAI).getType() : "unknown";
						fprintf(f, "%.1f\t%.1f\t%I64d\t%d\t%d\t%d,%d\t%s%s\n", (double)kTop.iTicks * dMs, (double)kTop.iPathTicks * dMs,
							kTop.iPathCalls, kTop.iOwner, kTop.iID, kTop.iX, kTop.iY, szType, kTop.iNative ? " (native)" : "");
					}
				}

				fprintf(f, "--- per player (ms / calls / longest single call ms)\nid\ttype\tcivilization\tcities\tunits");
				for (int s2 = 0; s2 < PS_COUNT; s2++)
				{
					fprintf(f, "\t%s", g_aszPlayerSlotNames[s2]);
				}
				fprintf(f, "\n");
				for (int iP = 0; iP < MAX_PLAYERS; iP++)
				{
					bool bPlayerAny = false;
					for (int s2 = 0; s2 < PS_COUNT; s2++)
					{
						bPlayerAny = bPlayerAny || kData.aiPlayerCalls[s2][iP] > 0;
					}
					if (bPlayerAny && kData.abPlayerInfo[iP])
					{
						fprintf(f, "%d\t%c\t%s\t%d\t%d", iP, kData.acPlayerType[iP], kData.aszPlayerName[iP], kData.aiPlayerCities[iP], kData.aiPlayerUnits[iP]);
						for (int s2 = 0; s2 < PS_COUNT; s2++)
						{
							fprintf(f, "\t%.1f / %I64d / %.1f", (double)kData.aiPlayerTicks[s2][iP] * dMs, kData.aiPlayerCalls[s2][iP],
								(double)kData.aiPlayerMaxTicks[s2][iP] * dMs);
						}
						fprintf(f, "\n");
					}
				}

				bool bCounter = false;
				for (int i = 0; i < CNT_COUNT; i++)
				{
					bCounter = bCounter || kData.aiCounter[i] != 0;
				}
				if (bCounter)
				{
					fprintf(f, "--- counters\n");
					for (int i = 0; i < CNT_COUNT; i++)
					{
						fprintf(f, "%I64d\t%s\n", kData.aiCounter[i], g_aszCounterNames[i]);
					}
				}
				fprintf(f, "\n");
				fclose(f);
			}
		}

		memset(kData.aiTicks, 0, sizeof(kData.aiTicks));
		memset(kData.aiCalls, 0, sizeof(kData.aiCalls));
		memset(kData.aiMaxTicks, 0, sizeof(kData.aiMaxTicks));
		memset(kData.aiUnitTicks, 0, sizeof(kData.aiUnitTicks));
		memset(kData.aiUnitCalls, 0, sizeof(kData.aiUnitCalls));
		memset(kData.aiUnitMaxTicks, 0, sizeof(kData.aiUnitMaxTicks));
		memset(kData.aiUnitPathTicks, 0, sizeof(kData.aiUnitPathTicks));
		memset(kData.aiUnitPathCalls, 0, sizeof(kData.aiUnitPathCalls));
		memset(kData.aiUnitPathMaxTicks, 0, sizeof(kData.aiUnitPathMaxTicks));
		kData.iNoUnitPathTicks = 0;
		kData.iNoUnitPathCalls = 0;
		kData.iNoUnitPathMaxTicks = 0;
		kData.iPathTicksRun = 0;
		kData.iPathCallsRun = 0;
		memset(kData.aiFreezeCalls, 0, sizeof(kData.aiFreezeCalls));
		memset(kData.aiFreezeTicks, 0, sizeof(kData.aiFreezeTicks));
		kData.iNumTopUnits = 0;
		memset(kData.aiPlayerTicks, 0, sizeof(kData.aiPlayerTicks));
		memset(kData.aiPlayerCalls, 0, sizeof(kData.aiPlayerCalls));
		memset(kData.aiPlayerMaxTicks, 0, sizeof(kData.aiPlayerMaxTicks));
		memset(kData.abPlayerInfo, 0, sizeof(kData.abPlayerInfo));
		memset(kData.aiCounter, 0, sizeof(kData.aiCounter));
		// aiDepth is not reset, scopes may be open (flush runs inside nothing, but stay safe)
#endif
	}
}

#endif // WTP_TIMING_H
