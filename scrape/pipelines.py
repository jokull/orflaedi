import datetime as dt
from orflaedi.database import SessionLocal, engine
from orflaedi.models import Base, Model, Retailer


Base.metadata.create_all(bind=engine)


def get_or_create_retailer(db, slug):
    retailer = db.query(Retailer).filter(Retailer.slug == slug).first()
    if retailer is None:
        retailer = Retailer(slug=slug, name=slug)
        db.add(retailer)
        db.commit()
    return retailer


class DatabasePipeline(object):
    def __init__(self):
        self.scraped_skus = set()

    def open_spider(self, spider):
        self.db = SessionLocal()
        self.retailer = get_or_create_retailer(self.db, slug=spider.name)

    def close_spider(self, spider):
        # we can deactivate these since they are no longer available
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
            # Name and make can have been tweaked after scraping by editors so don’t overwrite
            model.name = item["name"]
            model.make = item.get("make")
        model.last_scraped = dt.datetime.utcnow()
        model.price = item["price"]
        model.image_url = len(item["file_urls"]) and item["file_urls"][0] or None
        model.active = True
        if model.name is None:
            model.name = item.get("name")
        if not model.make:
            model.make = item.get("make") or ""
        if not model.motor_model:
            model.motor_model = item.get("motor_model") or None
        self.db.add(model)
        self.scraped_skus.add(item["sku"])
        return item
