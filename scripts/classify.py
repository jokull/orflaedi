"""
Bike classifier that shells out to `claude -p` (uses the user's Claude
subscription) and writes classification + tags back to Postgres.

Modes:
    --validate [N]    Run the classifier on N random manually-tagged bikes
                      (default 20), compare predictions to the human labels,
                      and print an accuracy report. No DB writes.

    --backfill [N]    Classify N random untagged active bikes (default all).
                      Writes classification + tags to the DB.

    --id <model_id>   Classify a single bike by id (prints result only).

Image source: web/public/images/<hash>.webp (already built by build_data.py).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orflaedi import models as M  # noqa: E402

load_dotenv()

REPO = Path(__file__).resolve().parent.parent
WEB_DATA = REPO / "web" / "src" / "data" / "models.json"
IMAGES_DIR = REPO / "web" / "public" / "images"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://orflaedi:orflaedi@localhost/orflaedi"
).replace("postgresql+asyncpg://", "postgresql://")

CLASSES = [c.name for c in M.VehicleClassEnum]
TAGS = [t.name for t in M.TagEnum]

PROMPT_TEMPLATE = """\
You are a bike-classification labeler. Reply with a single minified JSON object, nothing else.

Read {image_path}.

Context (may be wrong, trust the image): name={name!r} make={make!r}

Classification options (choose exactly one):
- bike_b: pedelec e-bike (pedal-assist ≤250W, ≤25km/h)
- bike_c: electric scooter or kick scooter (standing platform, no saddle)
- lb_1: light motorbike (>250W, ≤25km/h)
- lb_2: hraðhjól / speed pedelec (>25km/h, up to 45km/h)

Tag options (zero or more, from this enum — never invent new tags):
- mountain: knobby tires and suspension; off-road geometry
- road: drop handlebars, racing geometry
- city: flat bars, upright commuter/utility
- cargo: extended frame, front or rear cargo box or long rack
- open_frame: step-through frame (low top tube, no crossbar)

Common combinations:
- A step-through commuter is city + open_frame
- A long-tail cargo bike is cargo + city (often + open_frame)
- A full-suspension e-MTB is mountain alone

Output exactly: {{"classification":"...","tags":["...","..."]}}
"""


def load_image_map() -> dict[int, str]:
    """Map model.id -> absolute image path from the built web data."""
    if not WEB_DATA.exists():
        raise RuntimeError(
            f"{WEB_DATA} missing — run `.venv/bin/python scripts/build_data.py` first."
        )
    data = json.loads(WEB_DATA.read_text())
    out: dict[int, str] = {}
    for m in data["models"]:
        imgs = m.get("images") or {}
        name = imgs.get("1x") or imgs.get("2x") or imgs.get("3x")
        if name:
            out[m["id"]] = str(IMAGES_DIR / name.replace("/images/", ""))
    return out


async def classify_one(image_path: str, name: str, make: str | None) -> dict | None:
    prompt = PROMPT_TEMPLATE.format(
        image_path=image_path, name=name or "", make=make or ""
    )
    proc = await asyncio.create_subprocess_exec(
        "claude",
        "-p",
        "--output-format",
        "json",
        "--disallowedTools",
        "Bash Edit Write WebFetch WebSearch Grep Glob",
        "--effort",
        "low",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate(prompt.encode())
    try:
        wrapper = json.loads(stdout.decode())
    except json.JSONDecodeError:
        return None
    if wrapper.get("is_error"):
        return None
    result = (wrapper.get("result") or "").strip()
    if result.startswith("```"):
        result = result.strip("`").lstrip("json").strip()
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        return None
    if parsed.get("classification") not in CLASSES:
        return None
    parsed["tags"] = [t for t in (parsed.get("tags") or []) if t in TAGS]
    parsed["_cost"] = wrapper.get("total_cost_usd", 0)
    parsed["_duration_ms"] = wrapper.get("duration_ms", 0)
    return parsed


async def bounded_classify(sem: asyncio.Semaphore, image_path, name, make):
    async with sem:
        return await classify_one(image_path, name, make)


async def validate(sample_size: int, concurrency: int = 4) -> None:
    engine = sa.create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        rows = (
            db.execute(
                sa.select(M.Model)
                .where(
                    M.Model.active.is_(True),
                    M.Model.tags.isnot(None),
                    sa.func.array_length(M.Model.tags, 1) > 0,
                )
                .order_by(sa.func.random())
                .limit(sample_size)
            )
            .scalars()
            .all()
        )

    image_map = load_image_map()
    targets = [m for m in rows if m.id in image_map]
    if not targets:
        print("No manually-tagged bikes with images found.")
        return

    print(f"Validating on {len(targets)} manually-tagged bikes...\n")

    sem = asyncio.Semaphore(concurrency)
    tasks = [
        bounded_classify(sem, image_map[m.id], m.name or "", m.make or "")
        for m in targets
    ]
    predictions = await asyncio.gather(*tasks)

    per_tag_truth: Counter = Counter()
    per_tag_pred: Counter = Counter()
    per_tag_tp: Counter = Counter()
    correct_class = 0
    total_cost = 0.0
    disagreements: list[tuple[M.Model, dict]] = []

    for model, pred in zip(targets, predictions):
        if pred is None:
            print(f"  ✗ {model.id} {model.make} {model.name[:40]}  [classify failed]")
            continue

        total_cost += pred.get("_cost", 0)
        truth_tags = set(t.name if hasattr(t, "name") else str(t) for t in (model.tags or []))
        pred_tags = set(pred.get("tags") or [])
        truth_class = model.classification.name if model.classification else None
        pred_class = pred.get("classification")

        for t in truth_tags:
            per_tag_truth[t] += 1
        for t in pred_tags:
            per_tag_pred[t] += 1
        for t in truth_tags & pred_tags:
            per_tag_tp[t] += 1

        class_match = truth_class == pred_class
        tags_match = truth_tags == pred_tags
        if class_match:
            correct_class += 1

        marker = "✓" if class_match and tags_match else ("~" if class_match else "✗")
        print(
            f"  {marker} {model.id} {(model.make or '?')[:14]:<14} "
            f"{(model.name or '')[:32]:<32}  "
            f"truth: {truth_class} {sorted(truth_tags)}  "
            f"pred: {pred_class} {sorted(pred_tags)}"
        )
        if not (class_match and tags_match):
            disagreements.append((model, pred))

    print(f"\n--- Summary ({len(targets)} bikes) ---")
    print(f"Classification accuracy: {correct_class}/{len(targets)} = {correct_class/len(targets):.0%}")
    print(f"\nPer-tag precision / recall:")
    for tag in TAGS:
        truth = per_tag_truth.get(tag, 0)
        pred = per_tag_pred.get(tag, 0)
        tp = per_tag_tp.get(tag, 0)
        precision = tp / pred if pred else float("nan")
        recall = tp / truth if truth else float("nan")
        print(
            f"  {tag:<12} truth={truth:>3}  pred={pred:>3}  "
            f"precision={precision:.2f}  recall={recall:.2f}"
        )
    print(f"\nTotal cost: ${total_cost:.2f}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="Validate against manually-tagged bikes")
    v.add_argument("-n", type=int, default=20)
    v.add_argument("-c", "--concurrency", type=int, default=4)

    args = parser.parse_args()
    if args.cmd == "validate":
        asyncio.run(validate(args.n, args.concurrency))


if __name__ == "__main__":
    main()
