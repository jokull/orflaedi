# Development

You will need pnpm and Postgres running locally.

Web frontend (Astro, in `web/`):

```bash
> cd web
> pnpm install
> pnpm run dev
```

The frontend is a static site built from `web/src/data/models.json`, which is
generated from the Postgres database by `scripts/build_data.py`.

Scrapers run in Docker (via the compose file in `mediaserver`):

```bash
> docker compose -f /Users/jokull/mediaserver/docker-compose.yml up -d orflaedi_scrapy
```

JS-heavy retailer sites that can't be scraped over plain HTTP (e.g. stormur.is)
use host-side Scrapling/Playwright spiders in `scrape/scrapling_spiders/`,
run with the repo venv:

```bash
> .venv/bin/python scrape/scrapling_spiders/stormur.py
```

# Scrapers

This project scrapes Icelandic e-bike retailer websites

- ellingsen.s4s.is
- orninn.is
- kriacycles.is
- tri.is
- rafmagnshjol.is
- reidhjolaverzlunin.is
- markid.is
- gap.is
- peloton.is
- ofsi.is
- hjolasprettur.is
- hvellur.com
- bike.is (Fjallakofinn)
- everest.is
- nova.is
- skidathjonustan.com (Akureyri)
- elko.is
- sensabikes.is
- gastec.is
- scb.is
- unno.is

**TODO**

- https://arcticebike.com/collections/e-bikes
- https://www.pukinn.com/ghost-e-bikes
- http://topphjol.is

## Data

Vehicles can be browsed on these dimensions

- Price
  - Below 60.000 kr
  - Between 60.000 and 130.000 kr
  - Between 130.000 and 250.000 kr
  - Between 250.000 and 600.000 kr
  - Above 600.000 kr
- Vehicle classification
  - Reiðhjól C (mostly scooters)
  - Reiðhjól B (e-bikes)
  - Létt bifhjól (light two wheeler above 250w)
  - Hraðhjól (also called Létt bifhjól 2, light two wheeler above 25km/h top
    speed)
- Retailer
  - see websites above

In the future it would be good to connect vehicles to electribikereview.com to
get frame types, purpose (gravel, city, cargo etc.). I scraped the bike brand
name too. Could add a filter for that to the UI.

# Deployment

The site is hosted on Cloudflare Workers (`www.orflaedi.is`). Every hour a
launchd agent (`com.orflaedi.update-and-deploy`) runs
`bin/update-and-deploy.sh`, which:

1. waits for any running scrapers to finish
2. runs the host-side Playwright spiders
3. rebuilds `web/src/data/models.json` from Postgres (`scripts/build_data.py`)
4. classifies new/untagged bikes with Claude (`scripts/classify.py`)
5. rebuilds the data and runs the Astro build
6. deploys to Cloudflare with `wrangler deploy`

Scraper Python dependencies live in `requirements.txt` (installed by
`Dockerfile.scrapy` and the Scrapy Cloud image via `scrapinghub.yml`). The
legacy FastAPI/starlette web app was retired when the frontend moved to Astro.
