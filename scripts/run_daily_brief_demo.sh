#!/usr/bin/env bash
# Atlas Daily Brief Demo — AMD + NVDA (with portfolio context)
# Runs the full local pipeline from structured example data to a Daily Brief summary.
# Exercises all five Daily Brief input surfaces: portfolio, research, watchlist,
# discovery, and company analysis.
# No network calls. No AI. No external APIs. Deterministic.
#
# Usage:
#   bash scripts/run_daily_brief_demo.sh
#
# Prerequisites: install Atlas in a local virtualenv first.
#   python -m venv .venv && source .venv/bin/activate && pip install -e .

set -euo pipefail

# Resolve the atlas CLI — prefer the local virtualenv if present.
if [ -f ".venv/bin/atlas" ]; then
  ATLAS=".venv/bin/atlas"
elif command -v atlas &>/dev/null; then
  ATLAS="atlas"
else
  echo "ERROR: 'atlas' command not found."
  echo "Install Atlas first:"
  echo "  python -m venv .venv && source .venv/bin/activate && pip install -e ."
  exit 1
fi

DEMO_DIR="examples/daily_brief_demo"
TMP_DIR="tmp/atlas_demo"
BRIEF_OUT="$TMP_DIR/daily_brief.txt"

echo "=== Atlas Daily Brief Demo (AMD + NVDA) ==="
echo "Atlas:  $ATLAS"
echo "Input:  $DEMO_DIR"
echo "Output: $TMP_DIR"
echo ""

mkdir -p "$TMP_DIR"

echo "Step 1: Export research projects (AMD + NVDA)..."
"$ATLAS" research export \
  --input "$DEMO_DIR/research_input.json" \
  --output "$TMP_DIR/research.json"
echo "  → $TMP_DIR/research.json"

echo ""
echo "Step 2: Export watchlist intelligence (AMD + NVDA)..."
"$ATLAS" watchlist intelligence \
  --input "$DEMO_DIR/watchlist_input.json" \
  --output "$TMP_DIR/watchlist.json"
echo "  → $TMP_DIR/watchlist.json"

echo ""
echo "Step 3: Export discovery candidates..."
"$ATLAS" discovery export \
  --knowledge "$DEMO_DIR/knowledge.json" \
  --research "$TMP_DIR/research.json" \
  --watchlist "$TMP_DIR/watchlist.json" \
  --output "$TMP_DIR/discovery.json"
echo "  → $TMP_DIR/discovery.json"

echo ""
echo "Step 4: Export AMD company analysis..."
"$ATLAS" company-analysis export \
  --ticker AMD \
  --company-name "AMD Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "AMD designs high-performance CPUs and GPUs." \
  --knowledge "$DEMO_DIR/knowledge.json" \
  --research "$TMP_DIR/research.json" \
  --output "$TMP_DIR/company_analysis_amd.json"
echo "  → $TMP_DIR/company_analysis_amd.json"

echo ""
echo "Step 5: Export NVDA company analysis..."
"$ATLAS" company-analysis export \
  --ticker NVDA \
  --company-name "NVIDIA Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "NVIDIA designs GPUs and accelerated computing platforms." \
  --knowledge "$DEMO_DIR/knowledge.json" \
  --research "$TMP_DIR/research.json" \
  --output "$TMP_DIR/company_analysis_nvda.json"
echo "  → $TMP_DIR/company_analysis_nvda.json"

echo ""
echo "Step 6: Merge company analysis exports..."
"$ATLAS" company-analysis merge \
  --inputs "$TMP_DIR/company_analysis_amd.json" \
  --inputs "$TMP_DIR/company_analysis_nvda.json" \
  --output "$TMP_DIR/company_analysis.json"
echo "  → $TMP_DIR/company_analysis.json"

echo ""
echo "Step 7: Generate Daily Brief (all five input surfaces)..."
echo "────────────────────────────────────────────────────────────"
"$ATLAS" daily summary \
  --portfolio "$DEMO_DIR/portfolio.json" \
  --research "$TMP_DIR/research.json" \
  --watchlist "$TMP_DIR/watchlist.json" \
  --discovery "$TMP_DIR/discovery.json" \
  --company-analysis "$TMP_DIR/company_analysis.json" \
  | tee "$BRIEF_OUT"

echo "────────────────────────────────────────────────────────────"
echo ""
echo "Demo complete."
echo ""
echo "Input files:"
echo "  $DEMO_DIR/portfolio.json  (static demo data — no live prices)"
echo "  $DEMO_DIR/research_input.json"
echo "  $DEMO_DIR/watchlist_input.json"
echo "  $DEMO_DIR/knowledge.json"
echo ""
echo "Generated files:"
echo "  $TMP_DIR/research.json"
echo "  $TMP_DIR/watchlist.json"
echo "  $TMP_DIR/discovery.json"
echo "  $TMP_DIR/company_analysis_amd.json"
echo "  $TMP_DIR/company_analysis_nvda.json"
echo "  $TMP_DIR/company_analysis.json"
echo "  $BRIEF_OUT"
echo ""
echo "Daily Brief saved to: $BRIEF_OUT"
echo "To clean up: rm -rf $TMP_DIR"
