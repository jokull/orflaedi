#!/bin/bash
# Post-scrape pipeline: classify new untagged bikes, rebuild data,
# deploy to Cloudflare. Safe to run repeatedly — each step is a no-op
# if there's nothing to do.
#
# Usage:  bin/update-and-deploy.sh
#
# Exits 0 on success. Logs each step with timestamps.
#
# Safety limits (override via env):
#   CLASSIFY_MAX=50         max bikes classified per run
#   CLASSIFY_COST_CAP=5.00  stop classify early if spend exceeds USD
# Belt-and-suspenders on top of classify.py's own per-call budget and
# timeout so a stuck or buggy CLI can't drain the subscription.

set -euo pipefail

CLASSIFY_MAX="${CLASSIFY_MAX:-50}"
CLASSIFY_COST_CAP="${CLASSIFY_COST_CAP:-5.00}"

cd "$(dirname "$0")/.."
ROOT=$(pwd)

log() { echo "[$(date +%H:%M:%S)] $*"; }

load_cloudflare_token() {
  if [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    return
  fi
  if command -v security > /dev/null 2>&1; then
    CLOUDFLARE_API_TOKEN=$(security find-generic-password \
      -a "$(id -un)" \
      -s is.orflaedi.cloudflare-api-token \
      -w 2> /dev/null || true)
    export CLOUDFLARE_API_TOKEN
  fi
}

# Wait for any running scrapers to finish — we don't want to classify
# mid-scrape and miss half the new items.
while docker compose -f /Users/jokull/mediaserver/docker-compose.yml \
        exec -T orflaedi_scrapy pgrep -f "scrapy crawl" > /dev/null 2>&1; do
  log "scraper busy, waiting 30s..."
  sleep 30
done

# 0) Run host-side Playwright spiders (stormur.is 403s plain HTTP, so it can't
#    live in the Docker-based scrapy runner). Soft-fail so a broken spider
#    doesn't block deploy.
log "running stormur (Playwright)..."
"$ROOT/.venv/bin/python" "$ROOT/scrape/scrapling_spiders/stormur.py" || {
  log "stormur scraper failed; continuing"
}

# 1) Build web data (fetches images, writes models.json)
log "rebuilding web data..."
"$ROOT/.venv/bin/python" "$ROOT/scripts/build_data.py"

# 2) Classify any untagged active bikes. Depends on images existing
#    locally, which step 1 just ensured. Caps bikes/run and total spend
#    so a runaway scraper flooding the DB can't drain the subscription.
log "classifying new/untagged bikes (max=$CLASSIFY_MAX, cost_cap=\$$CLASSIFY_COST_CAP)..."
"$ROOT/.venv/bin/python" "$ROOT/scripts/classify.py" backfill \
  -n "$CLASSIFY_MAX" -c 4 --cost-cap "$CLASSIFY_COST_CAP" || {
  log "classify step reported errors; continuing to deploy what we have"
}

# 3) Rebuild data once more so the fresh classifications reach models.json
log "rebuilding web data with new classifications..."
"$ROOT/.venv/bin/python" "$ROOT/scripts/build_data.py"

# 4) Build Astro and deploy to Cloudflare Workers
log "building Astro..."
cd "$ROOT/web"
pnpm run build

log "deploying to Cloudflare..."
load_cloudflare_token
if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  log "Cloudflare token missing from environment and login Keychain"
  exit 1
fi
pnpm exec wrangler deploy

log "done."
