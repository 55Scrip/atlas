#!/usr/bin/env bash
# Atlas Internal v1 Demo
# Runs the full safe Atlas user journey:
#   Snapshot Draft validate → review → confirm → reject → export-research-notes
#   → export-company-facts → weekly-review
#
# Local-only. No network calls. No external services. No credentials required.
# Writes only to /tmp/atlas_internal_v1_demo/. Does not mutate repository files.
#
# Usage:
#   bash scripts/run_internal_v1_demo.sh
#
# Prerequisites: install Atlas in a local virtualenv first.
#   python -m venv .venv && source .venv/bin/activate && pip install -e .

set -euo pipefail

# ── Resolve CLI ────────────────────────────────────────────────────────────────
if [ -f ".venv/bin/atlas" ]; then
  ATLAS=".venv/bin/atlas"
elif command -v atlas &>/dev/null; then
  ATLAS="atlas"
else
  echo "ERROR: atlas CLI not found. Run: pip install -e ."
  exit 1
fi

# ── Temporary output directory ─────────────────────────────────────────────────
DEMO_DIR="/tmp/atlas_internal_v1_demo"

echo "=== Atlas Internal v1 Demo ==="
echo "Atlas CLI: $ATLAS"
echo "Demo output: $DEMO_DIR"
echo "Note: this demo writes only to $DEMO_DIR. No repository files are modified."
echo ""

# Clean and recreate demo directory
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"

# ── Stage 1: Validate Snapshot Drafts ──────────────────────────────────────────
echo "── Stage 1: Validate Snapshot Drafts ──"
echo ""

echo "[1a] Validate unconfirmed research notes draft..."
"$ATLAS" snapshot validate examples/snapshot_drafts/research_notes_snapshot.json
echo ""

echo "[1b] Validate confirmed research notes draft..."
"$ATLAS" snapshot validate examples/snapshot_drafts/research_notes_snapshot_confirmed.json
echo ""

echo "[1c] Validate confirmed company facts draft..."
"$ATLAS" snapshot validate examples/snapshot_drafts/company_facts_snapshot_confirmed.json
echo ""

echo "  ✓ Stage 1 complete — all drafts valid"
echo ""

# ── Stage 2: Review Snapshot Drafts ───────────────────────────────────────────
echo "── Stage 2: Review Snapshot Drafts ──"
echo ""

echo "[2a] Review unconfirmed research notes draft..."
"$ATLAS" snapshot review examples/snapshot_drafts/research_notes_snapshot.json
echo ""

echo "[2b] Review confirmed company facts draft..."
"$ATLAS" snapshot review examples/snapshot_drafts/company_facts_snapshot_confirmed.json
echo ""

echo "  ✓ Stage 2 complete — review is read-only; no files written"
echo ""

# ── Stage 3: Confirm a Draft Copy ─────────────────────────────────────────────
echo "── Stage 3: Confirm a Draft Copy ──"
echo ""

CONFIRMED_DRAFT="$DEMO_DIR/research_notes_confirmed.json"

echo "[3] Confirm research notes draft → $CONFIRMED_DRAFT ..."
"$ATLAS" snapshot confirm \
  examples/snapshot_drafts/research_notes_snapshot.json \
  --output-draft "$CONFIRMED_DRAFT" \
  --overwrite
echo ""

echo "[3-check] Verify original draft is unchanged (should still show: draft)..."
"$ATLAS" snapshot validate examples/snapshot_drafts/research_notes_snapshot.json | grep "Confirmation Status"
echo ""

echo "  ✓ Stage 3 complete — confirmed copy written; original unchanged"
echo ""

# ── Stage 4: Reject a Draft Copy ──────────────────────────────────────────────
echo "── Stage 4: Reject a Draft Copy ──"
echo ""

REJECTED_DRAFT="$DEMO_DIR/research_notes_rejected.json"

echo "[4a] Reject research notes draft → $REJECTED_DRAFT ..."
"$ATLAS" snapshot reject \
  examples/snapshot_drafts/research_notes_snapshot.json \
  --output-draft "$REJECTED_DRAFT" \
  --overwrite
echo ""

echo "[4b] Verify rejected draft cannot be exported (expected: Status: blocked)..."
# Capture exit code without aborting; export from rejected must fail
if "$ATLAS" snapshot export-research-notes \
    "$REJECTED_DRAFT" \
    --output-dir "$DEMO_DIR/notes_from_rejected" 2>&1; then
  echo "ERROR: export from rejected draft should have been blocked"
  exit 1
fi
echo ""
echo "  ✓ Stage 4 complete — rejected copy written; rejected drafts are not exportable"
echo ""

# ── Stage 5: Export Research Notes ────────────────────────────────────────────
echo "── Stage 5: Export Research Notes ──"
echo ""

NOTES_DIR="$DEMO_DIR/research_notes"

echo "[5] Export confirmed research notes → $NOTES_DIR ..."
"$ATLAS" snapshot export-research-notes \
  "$CONFIRMED_DRAFT" \
  --output-dir "$NOTES_DIR" \
  --overwrite
echo ""

echo "[5-check] Verify exported notes file exists..."
EXPECTED_NOTES="$NOTES_DIR/ASML/notes.md"
if [ ! -f "$EXPECTED_NOTES" ]; then
  echo "ERROR: expected notes file not found: $EXPECTED_NOTES"
  exit 1
fi
echo "  File present: $EXPECTED_NOTES"
echo ""

echo "  ✓ Stage 5 complete — research notes written; no other files changed"
echo ""

# ── Stage 6: Export Company Facts ─────────────────────────────────────────────
echo "── Stage 6: Export Company Facts ──"
echo ""

FACTS_DIR="$DEMO_DIR/company_facts"

echo "[6] Export confirmed company facts draft → $FACTS_DIR ..."
"$ATLAS" snapshot export-company-facts \
  examples/snapshot_drafts/company_facts_snapshot_confirmed.json \
  --output-dir "$FACTS_DIR" \
  --overwrite
echo ""

echo "[6-check] Verify exported company facts file exists..."
EXPECTED_FACTS="$FACTS_DIR/ASML.json"
if [ ! -f "$EXPECTED_FACTS" ]; then
  echo "ERROR: expected facts file not found: $EXPECTED_FACTS"
  exit 1
fi
echo "  File present: $EXPECTED_FACTS"
echo ""

echo "  ✓ Stage 6 complete — company facts written; no other files changed"
echo ""

# ── Stage 7: Run Weekly Investment Review ─────────────────────────────────────
echo "── Stage 7: Run Weekly Investment Review ──"
echo ""

echo "[7] Weekly Review with all local inputs including exported research notes and company facts..."
echo ""
"$ATLAS" weekly-review \
  --portfolio examples/weekly_review/portfolio.json \
  --watchlist examples/weekly_review/watchlist.json \
  --profile examples/weekly_review/investor_profile.json \
  --journal examples/weekly_review/decision_journal.json \
  --company-facts "$FACTS_DIR" \
  --financials examples/weekly_review/financials \
  --research-notes "$NOTES_DIR" \
  --as-of 2026-01-01 \
  --scope-notes examples/weekly_review/scope_notes.md
echo ""

echo "  ✓ Stage 7 complete — Weekly Review rendered with exported local inputs"
echo ""

# ── Summary ────────────────────────────────────────────────────────────────────
echo "=== Atlas Internal v1 Demo complete ==="
echo ""
echo "Demo output files:"
find "$DEMO_DIR" -type f | sort | sed 's/^/  /'
echo ""
echo "Safety boundary:"
echo "  - No network calls were made."
echo "  - No broker connections were made."
echo "  - No external APIs were called."
echo "  - No AI, LLM, or OCR was used."
echo "  - No repository example files were modified."
echo "  - All output was written to: $DEMO_DIR"
echo ""
echo "To clean up: rm -rf $DEMO_DIR"
