"""
Base classes for Scrapling spiders with database integration.
Mirrors the Scrapy pipeline behavior.
"""
import os
import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from orflaedi.models import Model, Retailer, VehicleClassEnum


def get_connection_string():
    return os.environ.get("DATABASE_URL", "postgresql://orflaedi:@localhost/orflaedi")


def get_or_create_retailer(db, slug):
    retailer = db.query(Retailer).filter(Retailer.slug == slug).first()
    if retailer is None:
        retailer = Retailer(slug=slug, name=slug)
        db.add(retailer)
        db.commit()
    return retailer


class ScraplingPipeline:
    """Database pipeline for Scrapling spiders - matches Scrapy pipeline behavior."""
    
    def __init__(self, spider_name: str, dry_run: bool = False):
        self.spider_name = spider_name
        self.dry_run = dry_run
        self.scraped_skus = set()
        self.db = None
        self.retailer = None
    
    def open(self):
        if self.dry_run:
            print(f"[DRY RUN] Would connect to database")
            return
        
        connection_string = get_connection_string()
        engine = create_engine(connection_string)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        self.retailer = get_or_create_retailer(self.db, slug=self.spider_name)
        print(f"Connected to database, retailer: {self.retailer.slug}")
    
    def process_item(self, item: dict):
        """Process a single scraped item."""
        self.scraped_skus.add(item["sku"])
        
        if self.dry_run:
            print(f"[DRY RUN] {item['make']} {item['name']}: {item['price']:,} kr")
            return item
        
        # Find or create model
        model = (
            self.db.query(Model)
            .filter(Model.sku == item["sku"], Model.retailer == self.retailer)
            .first()
        )
        if model is None:
            model = Model(retailer=self.retailer, sku=item["sku"])
        
        # Track price changes
        new_price = item["price"]
        if model.id and model.price and model.price != new_price:
            self.db.execute(text('''
                INSERT INTO price_history (model_id, price, recorded_at)
                VALUES (:model_id, :price, NOW())
            '''), {'model_id': model.id, 'price': new_price})
            print(f"  📊 Price change: {model.price:,} → {new_price:,} kr")
        
        # Update fields
        model.name = item["name"]
        model.make = item.get("make") or model.make
        model.last_scraped = dt.datetime.utcnow()
        model.scrape_url = item["scrape_url"]
        model.price = new_price
        model.image_url = item["file_urls"][0] if item.get("file_urls") else None
        model.active = True
        
        # Handle classification
        classification = item.get("classification", "bike_b")
        if isinstance(classification, str):
            classification = VehicleClassEnum[classification]
        model.classification = classification
        
        # Clean up name
        if model.name and model.make:
            if model.name.startswith(model.make):
                model.name = model.name[len(model.make):].strip()
        
        self.db.add(model)
        self.db.commit()
        
        print(f"  ✓ {model.make} {model.name}: {model.price:,} kr")
        return item
    
    def close(self):
        """Deactivate models no longer found and close connection."""
        if self.dry_run:
            print(f"[DRY RUN] Would deactivate models not in {len(self.scraped_skus)} scraped SKUs")
            return
        
        if self.db and self.scraped_skus:
            # Deactivate models not found in this scrape
            deactivated = self.db.query(Model).filter(
                ~Model.sku.in_(self.scraped_skus),
                Model.retailer == self.retailer
            ).update({"active": False}, synchronize_session=False)
            
            self.db.commit()
            print(f"Deactivated {deactivated} old models")
        
        if self.db:
            self.db.close()
            print("Database connection closed")
