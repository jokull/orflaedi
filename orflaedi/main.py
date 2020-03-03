import os

import imgix
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
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


@app.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    models_ = db.query(models.Model).filter(models.Model.active == True)
    return templates.TemplateResponse(
        "index.html", {"request": request, "models": models_}
    )


@app.get("/models/{id}")
async def get_model(request: Request, id: int, db: Session = Depends(get_db)):
    model = (
        db.query(models.Model)
        .filter(models.Model.active == True, models.Model.id == id)
        .first()
    )
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(
        "model.html", {"request": request, "model": model}
    )
