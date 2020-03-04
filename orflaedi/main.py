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
from .scrape import scrape

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/scrape")
def get_scrape(db: Session = Depends(get_db)):
    scraped = []
    """
    for name, status in scrape(db):
        scraped.append([name, status])
    """
    return {"scraped": scraped}


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
        ).group_by(models.Model.classification)
    }


def get_retailer_counts(db):
    return (
        db.query(models.Retailer, func.count(models.Model.id))
        .join(models.Model)
        .group_by(models.Retailer.id)
        .order_by(models.Retailer.name)
    )


def get_price_range_counts(db):
    for i, (price_min, price_max) in enumerate(price_ranges):
        q = db.query(func.count(models.Model.id))
        if price_min is not None:
            q = q.filter(models.Model.price >= price_min)
        if price_max is not None:
            q = q.filter(models.Model.price <= price_max)
        yield i, (price_min, price_max), q.scalar()


# An inclusive range of integers for user friendly price categories
price_ranges = (
    (None, 59_999),
    (60_000, 129_999),
    (130_000, 249_999),
    (250_000, 600_000),
    (600_000, None),
)


@app.get("/")
async def get_index(
    request: Request,
    db: Session = Depends(get_db),
    flokkur: str = None,
    verslun: str = None,
    verdbil: int = None,
):
    models_ = db.query(models.Model).filter(models.Model.active == True)

    if flokkur is not None:
        vclass = getattr(models.VehicleClassEnum, flokkur)
        if vclass is not None:
            models_ = models_.filter(models.Model.classification == vclass)

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

    if verslun is not None:
        models_ = models_.join(models.Retailer).filter(models.Retailer.slug == verslun)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "classification_counts": get_classification_counts(db),
            "retailer_counts": get_retailer_counts(db),
            "price_range_counts": get_price_range_counts(db),
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
