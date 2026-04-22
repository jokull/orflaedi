#!/bin/bash
# Post-scrape pipeline: classify new untagged bikes, rebuild data,
# deploy to Cloudflare. Safe to run repeatedly — each step is a no-op
# if there's nothing to do.
#
# Usage:  bin/update-and-deploy.sh
#
# Exits 0 on success. Logs each step with timestamps.

set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)

log() { echo "[$(date +%H:%M:%S)] $*"; }

# Wait for any running scrapers to finish — we don't want to classify
# mid-scrape and miss half the new items.
while docker compose -f /Users/jokull/mediaserver/docker-compose.yml \
        exec -T orflaedi_scrapy pgrep -f "scrapy crawl" > /dev/null 2>&1; do
  log "scraper busy, waiting 30s..."
  sleep 30
done

# 1) Build web data (fetches images, writes models.json)
log "rebuilding web data..."
"$ROOT/.venv/bin/python" "$ROOT/scripts/build_data.py"

# 2) Classify any untagged active bikes. Depends on images existing
#    locally, which step 1 just ensured.
log "classifying new/untagged bikes..."
"$ROOT/.venv/bin/python" "$ROOT/scripts/classify.py" backfill -c 4 || {
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
pnpm exec wrangler deploy

log "done."
