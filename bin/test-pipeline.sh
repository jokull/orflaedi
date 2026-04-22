#!/bin/bash
# End-to-end test for the scrape → classify → deploy pipeline.
#
# Picks one classified bike from a fast-crawling retailer, hard-deletes
# it from the DB, triggers that retailer's spider, and watches it flow
# back through: re-scraped → re-classified → rebuilt → deployed.
#
# Usage:  bin/test-pipeline.sh [retailer_slug]
#
# Default retailer: ellingsen (~3s crawl, small inventory, API-based).

set -euo pipefail

RETAILER="${1:-ellingsen}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE="/Users/jokull/mediaserver/docker-compose.yml"

psql() {
  PGPASSWORD=orflaedi /opt/homebrew/opt/postgresql@17/bin/psql \
    -h localhost -U orflaedi -d orflaedi -tA "$@"
}

log() { echo "[$(date +%H:%M:%S)] $*"; }

# 1) Pick a canary bike from the target retailer — needs to be classified
#    and active so we can verify classification is restored.
log "picking canary bike from retailer=$RETAILER"
CANARY=$(psql -c "SELECT m.id||'|'||m.sku||'|'||COALESCE(m.make,'')||'|'||m.name||'|'||m.classification::text||'|'||array_to_string(m.tags, ',') FROM models m JOIN retailers r ON m.retailer_id = r.id WHERE r.slug = '$RETAILER' AND m.active AND m.tags IS NOT NULL AND array_length(m.tags, 1) > 0 ORDER BY m.last_scraped DESC LIMIT 1;")
if [ -z "$CANARY" ]; then
  echo "no classified bikes for $RETAILER — run a backfill first"
  exit 1
fi

IFS='|' read -r CID CSKU CMAKE CNAME CCLASS CTAGS <<< "$CANARY"
log "canary: id=$CID sku=$CSKU $CMAKE $CNAME  [$CCLASS, tags=$CTAGS]"

# 2) Hard-delete the row so the scraper sees it as brand new.
log "deleting row (hard delete)..."
DELETED=$(psql -c "DELETE FROM models WHERE id = $CID RETURNING id;")
log "deleted: $DELETED"

# 3) Trigger the single spider (not the full hourly loop).
log "crawling $RETAILER..."
docker compose -f "$COMPOSE" exec -T orflaedi_scrapy \
  sh -c "cd /app && scrapy crawl $RETAILER" > /dev/null 2>&1

# 4) Confirm the bike came back, untagged (pre-classification state).
REINSERT=$(psql -c "SELECT m.id||'|'||m.classification::text||'|'||COALESCE(array_to_string(m.tags, ','),'null') FROM models m JOIN retailers r ON m.retailer_id = r.id WHERE r.slug = '$RETAILER' AND m.sku = '$CSKU';")
if [ -z "$REINSERT" ]; then
  echo "FAIL — bike did not reappear after crawl"
  exit 1
fi
IFS='|' read -r NEW_ID NEW_CLASS NEW_TAGS <<< "$REINSERT"
log "re-scraped: new_id=$NEW_ID class=$NEW_CLASS tags=$NEW_TAGS"
if [ -n "$NEW_TAGS" ] && [ "$NEW_TAGS" != "null" ] && [ "$NEW_TAGS" != "" ]; then
  log "  (already has tags — nothing for classifier to do; will verify deploy still happens)"
fi

# 5) Run the full update-and-deploy pipeline.
log "running update-and-deploy.sh..."
"$ROOT/bin/update-and-deploy.sh"

# 6) Verify classification came back (on the newly-inserted row).
FINAL=$(psql -c "SELECT classification::text||'|'||COALESCE(array_to_string(tags, ','),'null') FROM models WHERE id = $NEW_ID;")
IFS='|' read -r FINAL_CLASS FINAL_TAGS <<< "$FINAL"
log "final: id=$NEW_ID class=$FINAL_CLASS tags=$FINAL_TAGS"
if [ -z "$FINAL_TAGS" ] || [ "$FINAL_TAGS" = "null" ]; then
  echo "FAIL — bike is still untagged after pipeline"
  exit 1
fi

# 7) Check the live Cloudflare deploy picked up this model id. Cloudflare
#    edge propagation takes ~30s after wrangler reports Deployed, so poll.
log "checking live www.orflaedi.is (waiting for edge propagation)..."
LIVE_CHECK=""
for attempt in 1 2 3 4 5 6 7 8; do
  LIVE_CHECK=$(curl -s "https://www.orflaedi.is/hjol/$NEW_ID/" -o /dev/null -w "%{http_code}")
  if [ "$LIVE_CHECK" = "200" ]; then
    log "  attempt $attempt: HTTP 200"
    break
  fi
  log "  attempt $attempt: HTTP $LIVE_CHECK (retrying in 10s)"
  sleep 10
done
if [ "$LIVE_CHECK" != "200" ]; then
  echo "FAIL — bike detail page not live after ~80s (HTTP $LIVE_CHECK)"
  exit 1
fi

echo
echo "✓ PIPELINE TEST PASSED"
echo "  was:   $CID  $CCLASS, $CTAGS"
echo "  now:   $NEW_ID  $FINAL_CLASS, $FINAL_TAGS"
echo "  live:  https://www.orflaedi.is/hjol/$NEW_ID/"
