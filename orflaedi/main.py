import os

import imgix
import sqlalchemy as sa
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import models
from .database import session

app = FastAPI()


# Dependency
async def get_db():
    async with session() as db:
        yield db


app.mount("/static", StaticFiles(directory="static"), name="static")

builder = imgix.UrlBuilder("orflaedi.imgix.net", sign_key=os.getenv("IMGIX_TOKEN"))


def imgix_create_url(url, params):
    if url.startswith("//"):
        url = f"https:{url}"
    return builder.create_url(url, params)


templates = Jinja2Templates(directory="templates")
templates.env.globals["imgix_url"] = imgix_create_url
templates.env.globals["tag_enum"] = models.TagEnum
templates.env.globals["DEBUG"] = os.getenv("DEBUG") == "true"


async def get_classification_counts(db):
    counts_query_statement = (
        sa.select(models.Model.classification, func.count(models.Model.id))
        .where(models.Model.active == True)  # noqa
        .group_by(models.Model.classification)
    )
    counts = {
        key.value["short"]: value
        for key, value in (list((await db.execute(counts_query_statement))))
    }

    for enum in models.VehicleClassEnum:
        counts.setdefault(enum.value["short"], 0)
    return counts


async def get_tag_counts(db):
    return {
        models.TagEnum.__members__[tag]: count
        for tag, count in (
            await db.execute(
                text(
                    "select tags.tag, count(models.id) "
                    "from (select unnest(enum_range(NULL::tagenum)) as tag) as tags "
                    "left join models on tags.tag=ANY(models.tags) "
                    "where models.active = true "
                    "group by tags.tag "
                    "order by tags.tag"
                )
            )
        ).fetchall()
    }


async def get_retailer_counts(db, models_):
    sq = models_.subquery()
    statement = (
        sa.select((models.Retailer, func.count(sq.c.id)))
        .join(sq, models.Retailer.id == sq.c.retailer_id)
        .group_by(models.Retailer.id)
        .order_by(models.Retailer.name)
    )
    return await db.execute(statement)


async def get_price_range_counts(db, statements):
    for i, (label, price_min, price_max) in enumerate(price_ranges):
        q = statements
        if price_min is not None:
            q = q.where(models.Model.price >= price_min)
        if price_max is not None:
            q = q.where(models.Model.price <= price_max)
        yield i, label, (price_min, price_max), (len(list(((await db.execute(q)).scalars()))))


# An inclusive range of integers for user friendly price categories
price_ranges = (
    ("Undir 60 þ.kr.", None, 59_999),
    ("60 - 130 þ.kr.", 60_000, 130_000 - 1),
    ("130 - 250 þ.kr.", 130_000, 250_000 - 1),
    ("250 - 400 þ.kr.", 250_000, 400_000 - 1),
    ("400 - 550 þ.kr.", 400_000, 550_000 - 1),
    ("550 - 700 þ.kr.", 550_000, 700_000 - 1),
    ("Yfir 700 þ.kr.", 700_000, None),
)


def get_url_query(request: Request, **kwargs):
    query = dict(request.query_params)
    for k, v in kwargs.items():
        if v is None:
            query.pop(k, None)
        else:
            query[k] = v
    return "&".join((f"{k}={v}" for k, v in query.items()))


@app.get("/")
async def get_index(
    request: Request,
    db: Session = Depends(get_db),
    flokkur: str = None,
    verslun: str = None,
    verdbil: int = None,
    tag: str = None,
    admin: str = None,
):
    statement = sa.select(models.Model).where(
        models.Model.active == True, ~(models.Model.image_url == None)
    )

    retailer = None
    if verslun:
        results = (
            await db.execute(sa.select(models.Retailer).where(models.Retailer.slug == verslun))
        ).one()
        if len(results) > 0:
            retailer = results[0]

    def filter_retailers(statement):
        if verslun is None:
            return statement
        return statement.join(models.Retailer).where(models.Retailer.slug == verslun)

    def filter_price_range(statement):
        if verdbil is None:
            return statement
        try:
            _, price_min, price_max = price_ranges[verdbil]
        except IndexError:
            return statement
        else:
            if price_min is not None:
                statement = statement.where(models.Model.price >= price_min)
            if price_max is not None:
                statement = statement.where(models.Model.price <= price_max)
        return statement

    def filter_classification(statement):
        if flokkur is None:
            return statement
        vclass = getattr(models.VehicleClassEnum, flokkur)
        if vclass is not None:
            if vclass in (models.VehicleClassEnum.lb_1, models.VehicleClassEnum.lb_2):
                statement = statement.where(
                    (models.Model.classification == models.VehicleClassEnum.lb_1)
                    | (models.Model.classification == models.VehicleClassEnum.lb_2)
                )
            else:
                statement = statement.where(models.Model.classification == vclass)
        return statement

    def filter_tag(statement):
        if tag is None:
            return statement
        if tag in models.TagEnum.__members__:
            return statement.where(sa.text(f"'{tag}' = ANY (models.tags)"))
        return statement

    retailer_counts = await get_retailer_counts(
        db, filter_tag(filter_classification(filter_price_range(statement)))
    )

    price_statement = filter_tag(
        filter_classification(
            filter_retailers(
                sa.select(models.Model.id).where(
                    models.Model.active == True, ~(models.Model.image_url == None)
                )
            )
        )
    )

    price_range_counts = [_ async for _ in get_price_range_counts(db, price_statement)]
    classification_counts = await get_classification_counts(db)
    tag_counts = await get_tag_counts(db)

    statement = filter_retailers(statement)
    statement = filter_price_range(statement)
    statement = filter_classification(statement)
    statement = filter_tag(statement)

    # Templates will expect value for all keys

    tag_enum = getattr(models.TagEnum, tag) if tag else None
    classification_enum = getattr(models.VehicleClassEnum, flokkur) if flokkur else None

    _models = await db.execute(
        statement.order_by(models.Model.price, models.Model.make, models.Model.created.desc())
    )

    models_count = (
        await db.execute(
            statement.select_from(models.Model).with_only_columns(func.count()).order_by(None)
        )
    ).one()[0]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "classification": classification_enum,
            "classification_counts": classification_counts,
            "retailer": retailer,
            "tag": tag_enum,
            "tag_counts": tag_counts,
            "retailer_counts": retailer_counts,
            "price_range_counts": price_range_counts,
            "models_count": models_count,
            "models": _models.scalars(),
            "admin": bool(admin),
            "get_url_query": get_url_query,
        },
    )


@app.get("/hjol/{id}")
async def get_model(request: Request, id: int, db: Session = Depends(get_db)):
    statement = sa.select(models.Model).where(models.Model.active == True, models.Model.id == id)
    model = (await db.execute(statement)).scalars().first()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(
        "model.html",
        {
            "request": request,
            "model": model,
            "classification_counts": await get_classification_counts(db),
        },
    )


@app.post("/models/{id}/tags/{tag}")
async def add_tag(request: Request, tag: str, id: int, db: Session = Depends(get_db)):
    statement = sa.select(models.Model).where(models.Model.id == id)
    model = (await db.execute(statement)).scalars().first()
    if model is None or tag not in models.TagEnum.__members__:
        raise HTTPException(status_code=404, detail="Model not found")
    _tag = models.TagEnum.__members__[tag]
    model.tags = model.tags or []
    if _tag not in model.tags:
        model.tags = list(model.tags) + [_tag]
        db.add(model)
        await db.commit()
    return {}


@app.delete("/models/{id}/tags/{tag}")
async def remove_tag(request: Request, tag: str, id: int, db: Session = Depends(get_db)):
    statement = sa.select(models.Model).where(models.Model.id == id)
    model = (await db.execute(statement)).scalars().first()
    if model is None or tag not in models.TagEnum.__members__:
        raise HTTPException(status_code=404, detail="Model not found")
    _tag = models.TagEnum.__members__[tag]
    model.tags = model.tags or []
    if _tag in model.tags:
        tags = list(model.tags)
        tags.remove(_tag)
        model.tags = tags
        db.add(model)
        await db.commit()
    return {}
