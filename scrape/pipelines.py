import os
import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapy.utils.project import get_project_settings

from orflaedi.models import Model, Retailer


def get_or_create_retailer(db, slug):
    retailer = db.query(Retailer).filter(Retailer.slug == slug).first()
    if retailer is None:
        retailer = Retailer(slug=slug, name=slug)
        db.add(retailer)
        db.commit()
    return retailer


def get_connection_string():
    database_url = get_project_settings().get("DATABASE_URL")
    if database_url is not None:
        return database_url
    return os.environ.get("DATABASE_URL", "postgresql://orflaedi:@localhost/orflaedi")


class DatabasePipeline(object):
    def __init__(self):
        self.scraped_skus = set()

    def open_spider(self, spider):
        connection_string = spider.settings.get("DATABASE_URL")
        if connection_string is None:
            connection_string = get_connection_string()
        engine = create_engine(connection_string, connect_args={})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        self.retailer = get_or_create_retailer(self.db, slug=spider.name)

    def close_spider(self, spider):
        # we can deactivate these since they are no longer available
        if not getattr(spider, "skip", False):
            self.db.query(Model).filter(
                ~Model.sku.in_(self.scraped_skus), Model.retailer == self.retailer
            ).update({"active": False}, synchronize_session=False)
        self.db.commit()
        self.db.close()

    def process_item(self, item, spider):
        model = (
            self.db.query(Model)
            .filter(Model.sku == item["sku"], Model.retailer == self.retailer)
            .first()
        )
        if model is None:
            model = Model(retailer=self.retailer, sku=item["sku"])
            # Name and make can have been tweaked after scraping by editors so
            # don’t overwrite
            model.name = item["name"]
            model.make = item.get("make")
        model.last_scraped = dt.datetime.utcnow()
        model.scrape_url = item["scrape_url"]
        model.price = item["price"]
        model.image_url = len(item["file_urls"]) and item["file_urls"][0] or None
        model.active = True
        model.name = model.name or item.get("name")
        if not model.make:
            model.make = item.get("make") or ""
        if not model.motor_model:
            model.motor_model = item.get("motor_model") or None
        if model.name and model.make:
            if model.name.startswith(model.make):
                model.name = model.name[len(model.make) :]
        model.name = model.name.strip()
        if item.get("classification"):
            model.classification = item["classification"]
        self.db.add(model)
        self.db.commit()
        self.scraped_skus.add(item["sku"])
        return item
