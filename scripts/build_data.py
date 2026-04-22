"""Pull active models from Postgres, resize images locally with Pillow (with a
content-addressed disk cache), emit web/src/data/models.json.

Run from repo root:  .venv/bin/python scripts/build_data.py

Env:
    DATABASE_URL   postgresql+asyncpg://... (default: local orflaedi DB)
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import sqlalchemy as sa
from dotenv import load_dotenv
from PIL import Image, ImageChops
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orflaedi import models  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WEB = REPO / "web"
IMAGES_DIR = WEB / "public" / "images"
SOURCE_CACHE = REPO / ".cache" / "source_images"
DATA_FILE = WEB / "src" / "data" / "models.json"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://orflaedi:orflaedi@localhost/orflaedi"
)

VARIANTS = (
    {"suffix": "1x", "width": 400},
    {"suffix": "2x", "width": 800},
    {"suffix": "3x", "width": 1200},
)
TRIM_PAD = 20
CONCURRENCY = 8
USER_AGENT = "orflaedi-build/1.0 (+https://www.orflaedi.is)"


def normalize_url(url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return None


def source_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:20]


def variant_name(url: str, width: int) -> str:
    h = hashlib.sha256()
    h.update(url.encode())
    h.update(f"|w={width}|trim={TRIM_PAD}|fmt=webp".encode())
    return h.hexdigest()[:16] + ".webp"


def trim_borders(img: Image.Image, pad: int = TRIM_PAD) -> Image.Image:
    """Trim near-white borders, like imgproxy's trim:20. Threshold is lenient."""
    if img.mode in ("RGBA", "LA"):
        bg = Image.new(img.mode, img.size, (255,) * len(img.mode))
        diff = ImageChops.difference(img.convert(img.mode), bg)
    else:
        rgb = img.convert("RGB")
        bg = Image.new("RGB", rgb.size, (255, 255, 255))
        diff = ImageChops.difference(rgb, bg)
    diff = ImageChops.add(diff, diff, 2.0, -pad)
    bbox = diff.getbbox()
    if bbox:
        return img.crop(bbox)
    return img


async def fetch_source(client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore) -> bytes | None:
    cache = SOURCE_CACHE / source_hash(url)
    if cache.exists() and cache.stat().st_size > 0:
        return cache.read_bytes()
    async with sem:
        try:
            r = await client.get(url, timeout=30, headers={"User-Agent": USER_AGENT})
        except httpx.HTTPError as e:
            print(f"  ✗ fetch {url}: {e}", file=sys.stderr)
            return None
    if r.status_code != 200 or not r.content:
        print(f"  ✗ fetch {url}: HTTP {r.status_code}", file=sys.stderr)
        return None
    cache.write_bytes(r.content)
    return r.content


def render_variants(src_bytes: bytes, url: str) -> dict[str, str]:
    """Returns {suffix: variant_filename} for all widths. Skips already-rendered."""
    out: dict[str, str] = {}
    needed = [v for v in VARIANTS if not (IMAGES_DIR / variant_name(url, v["width"])).exists()]
    if not needed:
        return {v["suffix"]: variant_name(url, v["width"]) for v in VARIANTS}

    try:
        base = Image.open(io.BytesIO(src_bytes))
        base.load()
    except Exception as e:
        print(f"  ✗ decode {url}: {e}", file=sys.stderr)
        return {}
    trimmed = trim_borders(base)
    if trimmed.mode not in ("RGB", "RGBA"):
        trimmed = trimmed.convert("RGBA" if "A" in trimmed.mode else "RGB")

    for v in VARIANTS:
        name = variant_name(url, v["width"])
        path = IMAGES_DIR / name
        if path.exists():
            out[v["suffix"]] = name
            continue
        w, h = trimmed.size
        if w == 0 or h == 0:
            continue
        tw = v["width"]
        th = max(1, round(h * tw / w))
        resized = trimmed.resize((tw, th), Image.Resampling.LANCZOS)
        resized.save(path, "WEBP", quality=82, method=6)
        out[v["suffix"]] = name
    return out


async def process_model(
    client: httpx.AsyncClient, image_url: str, sem: asyncio.Semaphore
) -> dict[str, str]:
    # Short-circuit: if all variants already exist, skip network entirely.
    if all((IMAGES_DIR / variant_name(image_url, v["width"])).exists() for v in VARIANTS):
        return {v["suffix"]: variant_name(image_url, v["width"]) for v in VARIANTS}
    src = await fetch_source(client, image_url, sem)
    if not src:
        return {}
    return await asyncio.to_thread(render_variants, src, image_url)


async def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_CACHE.mkdir(parents=True, exist_ok=True)
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(DATABASE_URL)
    session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as db:
        retailer_rows = (await db.execute(sa.select(models.Retailer))).scalars().all()
        model_rows = (
            await db.execute(
                sa.select(models.Model)
                .where(models.Model.active == True, models.Model.image_url != None)  # noqa
                .order_by(models.Model.price, models.Model.make, models.Model.created.desc())
            )
        ).scalars().all()

    sem = asyncio.Semaphore(CONCURRENCY)
    normalized = [normalize_url(m.image_url) for m in model_rows]
    async with httpx.AsyncClient(follow_redirects=True) as client:
        coros = [
            process_model(client, url, sem) if url else asyncio.sleep(0, result={})
            for url in normalized
        ]
        results = await asyncio.gather(*coros)

    retailers_by_id = {
        r.id: {"id": r.id, "name": r.name, "slug": r.slug, "website_url": r.website_url}
        for r in retailer_rows
    }

    rendered: list[dict] = []
    referenced: set[str] = set()
    n_missing = 0
    for m, imgs in zip(model_rows, results):
        if not imgs or "1x" not in imgs:
            n_missing += 1
            continue
        referenced.update(imgs.values())
        tags = [t.name if hasattr(t, "name") else str(t) for t in (m.tags or [])]
        classification = m.classification.value["short"] if m.classification else None
        rendered.append(
            {
                "id": m.id,
                "name": m.admin_name or m.name,
                "make": m.admin_make or m.make,
                "classification": classification,
                "price": m.admin_price or m.price,
                "retailer_id": m.retailer_id,
                "tags": tags,
                "scrape_url": m.scrape_url,
                "images": {k: f"/images/{v}" for k, v in imgs.items()},
            }
        )

    retailer_ids_used = {m["retailer_id"] for m in rendered}
    retailers = sorted(
        (retailers_by_id[rid] for rid in retailer_ids_used if rid in retailers_by_id),
        key=lambda r: r["name"].lower(),
    )

    swept = 0
    for p in IMAGES_DIR.iterdir():
        if p.is_file() and p.name not in referenced:
            p.unlink()
            swept += 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "retailers": retailers,
        "models": rendered,
        "classifications": [
            {"short": c.value["short"], "long": c.value["long"]}
            for c in models.VehicleClassEnum
        ],
        "tags": [{"name": t.name, "label": t.value} for t in models.TagEnum],
        "price_ranges": [
            ["Undir 60 þ.kr.", None, 59_999],
            ["60 - 130 þ.kr.", 60_000, 130_000 - 1],
            ["130 - 250 þ.kr.", 130_000, 250_000 - 1],
            ["250 - 400 þ.kr.", 250_000, 400_000 - 1],
            ["400 - 550 þ.kr.", 400_000, 550_000 - 1],
            ["550 - 700 þ.kr.", 550_000, 700_000 - 1],
            ["Yfir 700 þ.kr.", 700_000, None],
        ],
    }
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False))

    size_mb = sum(p.stat().st_size for p in IMAGES_DIR.iterdir() if p.is_file()) / 1024 / 1024
    print(
        f"wrote {DATA_FILE.relative_to(REPO)}  "
        f"models: {len(rendered)}/{len(model_rows)} ok ({n_missing} skipped)  "
        f"images: {len(referenced)} files, {size_mb:.1f} MB, {swept} swept"
    )


if __name__ == "__main__":
    asyncio.run(main())
