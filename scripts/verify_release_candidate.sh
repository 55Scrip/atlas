#!/usr/bin/env bash
# Atlas Release Candidate Verification
# Runs compile check, full test suite, and Daily Brief demo.
# Local-only. No network calls. No external services.
#
# Usage:
#   bash scripts/verify_release_candidate.sh
#
# Prerequisites: install Atlas in a local virtualenv first.
#   python -m venv .venv && source .venv/bin/activate && pip install -e .

set -euo pipefail

# Resolve Python and atlas CLI from local virtualenv if present.
if [ -f ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 &>/dev/null; then
  PYTHON="python3"
else
  echo "ERROR: Python not found. Install Python and run: pip install -e ."
  exit 1
fi

echo "=== Atlas Release Candidate Verification ==="
echo "Python: $PYTHON"
echo ""

# ── Step 1: Compile check ──────────────────────────────────────────────────────
echo "Step 1: Compile check (atlas + tests)..."
"$PYTHON" -m compileall atlas tests -q
echo "  ✓ Compile check passed"
echo ""

# ── Step 2: Full test suite ────────────────────────────────────────────────────
echo "Step 2: Full test suite..."
"$PYTHON" -m pytest --tb=short -q
echo "  ✓ Tests passed"
echo ""

# ── Step 3: Daily Brief demo ───────────────────────────────────────────────────
echo "Step 3: Daily Brief demo..."
TMP_DIR="tmp/atlas_demo"
rm -rf "$TMP_DIR"
bash scripts/run_daily_brief_demo.sh > /dev/null
echo "  ✓ Demo completed"
echo ""

# ── Step 4: Verify generated files ────────────────────────────────────────────
echo "Step 4: Verify generated output files..."

EXPECTED_FILES=(
  "$TMP_DIR/research.json"
  "$TMP_DIR/watchlist.json"
  "$TMP_DIR/discovery.json"
  "$TMP_DIR/company_analysis_amd.json"
  "$TMP_DIR/company_analysis_nvda.json"
  "$TMP_DIR/company_analysis.json"
  "$TMP_DIR/daily_brief.txt"
)

for f in "${EXPECTED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "  ERROR: Expected file not found: $f"
    exit 1
  fi
  echo "  ✓ $f"
done
echo ""

# ── Step 5: Sanity check output sections ──────────────────────────────────────
echo "Step 5: Output section sanity check..."

BRIEF="$TMP_DIR/daily_brief.txt"

check_section() {
  local section="$1"
  if grep -q "$section" "$BRIEF"; then
    echo "  ✓ $section"
  else
    echo "  ERROR: Expected section not found in daily_brief.txt: $section"
    exit 1
  fi
}

check_section "Opening Summary"
check_section "Included Context"
check_section "What Deserves Attention"
check_section "Company Analysis Context"
check_section "What Can Safely Wait"
check_section "Research Framing"
echo ""

# ── Step 6: Forbidden language check ──────────────────────────────────────────
echo "Step 6: Forbidden language check on Daily Brief output..."

FORBIDDEN_TERMS=("strong buy" "strong sell" "price target" "outperform" "market-beating" "must act" "guaranteed" "risk-free" "urgent")

BRIEF_LOWER=$(tr '[:upper:]' '[:lower:]' < "$BRIEF")
for term in "${FORBIDDEN_TERMS[@]}"; do
  if echo "$BRIEF_LOWER" | grep -q "$term"; then
    echo "  ERROR: Forbidden term found in output: '$term'"
    exit 1
  fi
done
echo "  ✓ No forbidden language found"
echo ""

# ── Step 7: Cleanup ───────────────────────────────────────────────────────────
echo "Step 7: Cleanup..."
rm -rf "$TMP_DIR"
echo "  ✓ $TMP_DIR removed"
echo ""

echo "=== Verification complete. Atlas RC1 is green. ==="
