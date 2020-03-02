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

- tri.is
- kriacycles.is
- ellingsen.s4s.is
- rafmagnshjol.is
- orninn.is
- reidhjolaverzlunin.is
- markid.is
- gap.is
- hjolasprettur.is
- bike.is (Fjallakofinn)
- peleton.is
- hvellur.com
- ofsi.is
- skidathjonustan.com
- everest.is
