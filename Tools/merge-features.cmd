@echo off
rem Merges the feature branches in the order given in MERGING.md into the current branch.
rem Usage: Tools\merge-features.cmd [remote] [branches to skip...]
rem Restart after a conflict (fix it, git add, git commit): merged branches are skipped.
setlocal enabledelayedexpansion
set REMOTE=%~1
if "%REMOTE%"=="" set REMOTE=origin
set SKIP=
set N=0
for %%A in (%*) do (set /a N+=1 & if !N! GTR 1 set SKIP=!SKIP! %%A)
set BRANCHES=feature/trade-route-logic feature/trade-route-manager feature/qol-specialty-and-buy-materials feature/game-options-multipliers feature/hud-message-panel feature/nested-tooltip feature/transfer-amount-window feature/building-upgrade-clean feature/import-export-window feature/spelling-fixes

git config rerere.enabled true
git fetch %REMOTE% || exit /b 1

for %%B in (%BRANCHES%) do (
  set SKIPIT=0
  for %%S in (!SKIP!) do if "%%S"=="%%B" set SKIPIT=1
  if "!SKIPIT!"=="1" (
    echo skipped: %%B
  ) else (
    git rev-parse --verify -q %REMOTE%/%%B >nul
    if errorlevel 1 (echo not found in %REMOTE%: %%B & exit /b 1)
    git merge-base --is-ancestor %REMOTE%/%%B HEAD
    if not errorlevel 1 (
      echo already merged: %%B
    ) else (
      echo merging: %%B
      git merge --no-edit %REMOTE%/%%B
      if errorlevel 1 (
        echo.
        echo Conflict while merging %%B.
        echo Solve it, then: git add ^<file^>, git commit, and run this script again.
        exit /b 1
      )
    )
  )
)
echo done
