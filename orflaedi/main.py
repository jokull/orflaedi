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


templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    models_ = db.query(models.Model).filter(models.Model.active == True).all()
    return templates.TemplateResponse("index.html", {"request": request, "models": models_})
