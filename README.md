# Development

You will need yarn, Poetry installed and Postgres running locally

```bash
> yarn
> yarn run watch
```

In another tab

```bash
> poetry install
> uvicorn main:app --reload
```

Use something like this for black formating in a `.vscode/settings.json` file.

```json
{
  "python.pythonPath": "~/Library/Caches/pypoetry/virtualenvs/orflaedi-dZ_pPhTz-py3.7",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.formatting.blackArgs": ["--line-length=100"]
}
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

_TODO_

- http://www.gastec.is/vorur/p/TA8z9YCkyT/wQpl8dtKLw/sidney/
- https://www.pukinn.com/ghost-e-bikes

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

The project is hosted on Render on `www.orflaedi.is`. There is a Scrapy spider
for each of the retailer websites that is run a few times a day.

```bash
> poetry export --without-hashes -f requirements.txt > requirements.txt
> NODE_ENV=production yarn run build
```

- Update the requirements.txt (we’re using Poetry which uses a proper lockfile,
  but this is required for Render)
- Run a production build (it will slim down tailwindcss)

Next add a commit and push. It will autodeploy.

Images are served via imgix proxy (all bike images are references to the
external URL, never persisted locally).
