# Development

You will need yarn, Poetry installed and Postgres running locally

```bash
> yarn
> yarn run watch
```

In another tab

```bash
> poetry install
> uvicorn orflaedi.main:app --reload
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
