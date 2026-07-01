#!/usr/bin/env bash
# Atlas Daily Brief Demo — AMD + NVDA
# Runs the full local pipeline from structured example data to a Daily Brief summary.
# No network calls. No AI. No external APIs. Deterministic.

set -euo pipefail

DEMO_DIR="examples/daily_brief_demo"
TMP_DIR="tmp/atlas_demo"

echo "=== Atlas Daily Brief Demo (AMD + NVDA) ==="
echo "Input:  $DEMO_DIR"
echo "Output: $TMP_DIR"
echo ""

mkdir -p "$TMP_DIR"

echo "Step 1: Export research projects (AMD + NVDA)..."
atlas research export \
  --input "$DEMO_DIR/research_input.json" \
  --output "$TMP_DIR/research.json"
echo "  → $TMP_DIR/research.json"

echo "Step 2: Export watchlist intelligence (AMD + NVDA)..."
atlas watchlist intelligence \
  --input "$DEMO_DIR/watchlist_input.json" \
  --output "$TMP_DIR/watchlist.json"
echo "  → $TMP_DIR/watchlist.json"

echo "Step 3: Export discovery candidates..."
atlas discovery export \
  --knowledge "$DEMO_DIR/knowledge.json" \
  --research "$TMP_DIR/research.json" \
  --watchlist "$TMP_DIR/watchlist.json" \
  --output "$TMP_DIR/discovery.json"
echo "  → $TMP_DIR/discovery.json"

echo "Step 4: Export AMD company analysis (engine-backed)..."
atlas company-analysis export \
  --ticker AMD \
  --company-name "AMD Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "AMD designs high-performance CPUs and GPUs." \
  --knowledge "$DEMO_DIR/knowledge.json" \
  --research "$TMP_DIR/research.json" \
  --output "$TMP_DIR/company_analysis_amd.json"
echo "  → $TMP_DIR/company_analysis_amd.json"

echo "Step 5: Export NVDA company analysis (engine-backed)..."
atlas company-analysis export \
  --ticker NVDA \
  --company-name "NVIDIA Corporation" \
  --sector "Semiconductors" \
  --country "USA" \
  --business-description "NVIDIA designs GPUs and accelerated computing platforms." \
  --knowledge "$DEMO_DIR/knowledge.json" \
  --research "$TMP_DIR/research.json" \
  --output "$TMP_DIR/company_analysis_nvda.json"
echo "  → $TMP_DIR/company_analysis_nvda.json"

echo "Step 6: Merge company analysis exports into a single file..."
python3 -c "
import json, sys
amd = json.loads(open('$TMP_DIR/company_analysis_amd.json').read())
nvda = json.loads(open('$TMP_DIR/company_analysis_nvda.json').read())
combined = amd + nvda
open('$TMP_DIR/company_analysis.json', 'w').write(json.dumps(combined, indent=2))
print('  Combined:', len(combined), 'company report(s)')
"
echo "  → $TMP_DIR/company_analysis.json"

echo ""
echo "Step 7: Generate Daily Brief (AMD + NVDA)..."
echo "=========================================="
atlas daily summary \
  --research "$TMP_DIR/research.json" \
  --watchlist "$TMP_DIR/watchlist.json" \
  --discovery "$TMP_DIR/discovery.json" \
  --company-analysis "$TMP_DIR/company_analysis.json"

echo ""
echo "Demo complete. Outputs are in $TMP_DIR/"
echo "To clean up: rm -rf $TMP_DIR"
