import os

import imgix
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
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


def get_classification_counts(db):
    return {
        key.value["short"]: value
        for key, value in db.query(
            models.Model.classification, func.count(models.Model.id)
        )
        .filter(models.Model.active == True)
        .group_by(models.Model.classification)
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
    for i, (price_min, price_max) in enumerate(price_ranges):
        q = models_
        if price_min is not None:
            q = q.filter(models.Model.price >= price_min)
        if price_max is not None:
            q = q.filter(models.Model.price <= price_max)
        yield i, (price_min, price_max), q.count()


# An inclusive range of integers for user friendly price categories
price_ranges = (
    (None, 59_999),
    (60_000, 129_999),
    (130_000, 249_999),
    (250_000, 600_000),
    (600_000, None),
)

lett_bifhjol_classes = (models.VehicleClassEnum.lb_1, models.VehicleClassEnum.lb_2)


@app.get("/")
async def get_index(
    request: Request,
    db: Session = Depends(get_db),
    flokkur: str = None,
    verslun: str = None,
    verdbil: int = None,
):
    models_ = db.query(models.Model).filter(
        models.Model.active == True, ~(models.Model.image_url == None)
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

    retailer_counts = get_retailer_counts(db, models_)
    price_range_counts = get_price_range_counts(db, models_)

    if verslun is not None:
        models_ = models_.join(models.Retailer).filter(models.Retailer.slug == verslun)

    if verdbil is not None:
        try:
            price_min, price_max = price_ranges[verdbil]
        except IndexError:
            pass
        else:
            if price_min is not None:
                models_ = models_.filter(models.Model.price >= price_min)
            if price_max is not None:
                models_ = models_.filter(models.Model.price <= price_max)

    # Templates will expect value for all keys
    classification_counts = get_classification_counts(db)
    for enum in models.VehicleClassEnum:
        classification_counts.setdefault(enum.value["short"], 0)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "classification_counts": classification_counts,
            "retailer_counts": retailer_counts,
            "price_range_counts": price_range_counts,
            "models": models_.order_by(models.Model.price),
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
