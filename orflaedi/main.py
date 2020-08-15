from orflaedi.models import TagEnum
import os

import imgix
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


app.mount("/static", StaticFiles(directory="static"), name="static")

builder = imgix.UrlBuilder("orflaedi.imgix.net", sign_key=os.getenv("IMGIX_TOKEN"))


def imgix_create_url(url, params):
    if url.startswith("//"):
        url = "https:{}".format(url)
    return builder.create_url(url, params)


templates = Jinja2Templates(directory="templates")
templates.env.globals["imgix_url"] = imgix_create_url
templates.env.globals["tag_enum"] = models.TagEnum


def get_classification_counts(db):
    return {
        key.value["short"]: value
        for key, value in db.query(
            models.Model.classification, func.count(models.Model.id)
        )
        .filter(models.Model.active == True)
        .group_by(models.Model.classification)
    }


def get_tag_counts(db):
    return {
        TagEnum.__members__[tag]: count
        for tag, count in db.execute(
            text(
                "select tags.tag, count(models.id) "
                "from (select unnest(enum_range(NULL::tagenum)) as tag) as tags "
                "left join models on tags.tag=ANY(models.tags) group by tags.tag "
                "order by tags.tag"
            )
        ).fetchall()
    }


def get_retailer_counts(db, models_):
    sq = models_.subquery()
    return (
        db.query(models.Retailer, func.count(sq.c.id))
        .join(sq, models.Retailer.id == sq.c.retailer_id)
        .group_by(models.Retailer.id)
        .order_by(models.Retailer.name)
    )


def get_price_range_counts(db, models_):
    for i, (label, price_min, price_max) in enumerate(price_ranges):
        q = models_
        if price_min is not None:
            q = q.filter(models.Model.price >= price_min)
        if price_max is not None:
            q = q.filter(models.Model.price <= price_max)
        yield i, label, (price_min, price_max), q.count()


# An inclusive range of integers for user friendly price categories
price_ranges = (
    ("Undir 60.000 kr", None, 59_999),
    ("60 - 130.000 kr", 60_000, 130_000 - 1),
    ("130 - 250.000 kr", 130_000, 250_000 - 1),
    ("250 - 400.000 kr", 250_000, 400_000 - 1),
    ("400 - 550.000 kr", 400_000, 550_000 - 1),
    ("550 - 700.000 kr", 550_000, 700_000 - 1),
    ("Yfir 700.000 kr", 700_000, None),
)

lett_bifhjol_classes = (models.VehicleClassEnum.lb_1, models.VehicleClassEnum.lb_2)


def get_url_query(request: Request, **kwargs):
    query = dict(request.query_params)
    for k, v in kwargs.items():
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
    models_ = db.query(models.Model).filter(
        models.Model.active == True, ~(models.Model.image_url == None)  # noqa
    )

    if flokkur is not None:
        vclass = getattr(models.VehicleClassEnum, flokkur)
        if vclass is not None:
            if vclass in lett_bifhjol_classes:
                models_ = models_.filter(
                    models.Model.classification.in_(lett_bifhjol_classes)
                )
            else:
                models_ = models_.filter(models.Model.classification == vclass)

    if tag is not None and tag in TagEnum.__members__:
        models_ = models_.filter(tag == models.Model.tags.any_())

    retailer_counts = get_retailer_counts(db, models_)
    price_range_counts = get_price_range_counts(db, models_)

    if verslun is not None:
        models_ = models_.join(models.Retailer).filter(models.Retailer.slug == verslun)

    if verdbil is not None:
        try:
            _, price_min, price_max = price_ranges[verdbil]
        except IndexError:
            pass
        else:
            if price_min is not None:
                models_ = models_.filter(models.Model.price >= price_min)
            if price_max is not None:
                models_ = models_.filter(models.Model.price <= price_max)

    # Templates will expect value for all keys
    classification_counts = get_classification_counts(db)
    tag_counts = get_tag_counts(db)
    for enum in models.VehicleClassEnum:
        classification_counts.setdefault(enum.value["short"], 0)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "classification_counts": classification_counts,
            "tag": tag,
            "tag_counts": tag_counts,
            "retailer_counts": retailer_counts,
            "price_range_counts": price_range_counts,
            "models": models_.order_by(models.Model.price, models.Model.created.desc()),
            "admin": bool(admin),
            "get_url_query": get_url_query,
        },
    )


@app.get("/hjol/{id}")
async def get_model(request: Request, id: int, db: Session = Depends(get_db)):
    model = (
        db.query(models.Model)
        .filter(models.Model.active == True, models.Model.id == id)
        .first()
    )
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(
        "model.html",
        {
            "request": request,
            "model": model,
            "classification_counts": get_classification_counts(db),
        },
    )


@app.post("/models/{id}/tags/{tag}")
async def add_tag(request: Request, tag: str, id: int, db: Session = Depends(get_db)):
    model = db.query(models.Model).get(id)
    if model is None or tag not in TagEnum.__members__:
        raise HTTPException(status_code=404, detail="Model not found")
    _tag = TagEnum.__members__[tag]
    model.tags = model.tags or []
    if _tag not in model.tags:
        model.tags.append(_tag)
        db.add(model)
        db.commit()
    return {}


@app.delete("/models/{id}/tags/{tag}")
async def remove_tag(request: Request, tag: str, id: int, db: Session = Depends(get_db)):
    model = db.query(models.Model).get(id)
    if model is None or tag not in TagEnum.__members__:
        raise HTTPException(status_code=404, detail="Model not found")
    _tag = TagEnum.__members__[tag]
    model.tags = model.tags or []
    if _tag in model.tags:
        model.tags.remove(_tag)
        db.add(model)
        db.commit()
    return {}
