#!/bin/sh
# Merges the feature branches in the order given in MERGING.md into the current branch.
# Usage: Tools/merge-features.sh [remote] [branches to skip...]
# Restart after a conflict (fix it, git add, git commit): merged branches are skipped.

REMOTE=${1:-origin}
[ $# -gt 0 ] && shift
SKIP="$*"
BRANCHES="feature/trade-route-logic feature/trade-route-manager feature/qol-specialty-and-buy-materials feature/game-options-multipliers feature/hud-message-panel feature/nested-tooltip feature/transfer-amount-window feature/building-upgrade-clean feature/import-export-window feature/spelling-fixes"

git config rerere.enabled true
git fetch "$REMOTE" || exit 1

for B in $BRANCHES; do
	case " $SKIP " in *" $B "*) echo "skipped: $B"; continue;; esac
	if ! git rev-parse --verify -q "$REMOTE/$B" >/dev/null; then
		echo "not found in $REMOTE: $B"; exit 1
	fi
	if git merge-base --is-ancestor "$REMOTE/$B" HEAD; then
		echo "already merged: $B"; continue
	fi
	echo "merging: $B"
	if ! git merge --no-edit "$REMOTE/$B"; then
		echo
		echo "Conflict while merging $B."
		echo "Solve it, then: git add <file>, git commit, and run this script again."
		exit 1
	fi
done
echo "done"
