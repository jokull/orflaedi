"""
Ofsi e-bike scraper using StealthyFetcher (bypasses rate limiting)

Run dry:  python scrape/scrapling_spiders/ofsi.py --dry-run
Run live: python scrape/scrapling_spiders/ofsi.py
"""
import re
import time
import argparse
from scrapling import StealthyFetcher

from base import ScraplingPipeline


SPIDER_NAME = "ofsi"

START_URLS = [
    "https://ofsi.is/collections/gain-rafmagnsgotuhjol",
    "https://ofsi.is/collections/vibe-rafmagnsborgarhjol",
    "https://ofsi.is/collections/kemen-rafmagnsborgarhjol-eldri-argerd",
    "https://ofsi.is/collections/kemen-tour-rafmagnsborgarhjol",
    "https://ofsi.is/collections/kemen-adv-rafmagnsborgarhjol",
    "https://ofsi.is/collections/diem-rafmagnsborgarhjol",
    "https://ofsi.is/collections/urrun-rafmagnsfjallahjol-eldri-argerd",
    "https://ofsi.is/collections/urrun-rafmagnsfjallahjol",
    "https://ofsi.is/collections/rise-rafmagnsfjallahjol-eldri-argerd",
    "https://ofsi.is/collections/rise-sl-fulldempad-rafmagnsfjallahjol",
    "https://ofsi.is/collections/rise-lt-fulldempad-rafmagnsfjallahjol",
    "https://ofsi.is/collections/wild-rafmagnsfjallahjol-eldri-argerd",
    "https://ofsi.is/collections/wild-fulldempad-rafmagnsfjallahjol",
]

# Delay between requests to avoid rate limiting
REQUEST_DELAY = 2


def get_product_links(page) -> list[str]:
    """Extract product links from collection page."""
    links = page.css('.grid__item a.full-unstyled-link')
    hrefs = []
    for link in links:
        href = link.attrib.get('href', '')
        if href and '/products/' in href and href not in hrefs:
            hrefs.append(href)
    return hrefs


def scrape_product(page, href: str) -> dict | None:
    """Scrape a single product page."""
    full_url = f'https://ofsi.is{href}' if href.startswith('/') else href
    
    try:
        prod_page = StealthyFetcher.fetch(full_url, headless=True, network_idle=True)
    except Exception as e:
        print(f'  Error loading {full_url}: {e}')
        return None
    
    # Extract make (brand)
    make_el = prod_page.css('.product__info-container .product__text')
    make = make_el[0].text.strip() if make_el else None
    
    # Extract name
    name_el = prod_page.css('.product__info-container .product__title h1')
    name = name_el[0].text.strip() if name_el else None
    
    if not name:
        return None
    
    # Extract SKU from URL
    sku = href.rsplit('/', 1)[-1]
    
    # Extract image
    img_el = prod_page.css('.product__media img')
    image_url = None
    if img_el:
        src = img_el[0].attrib.get('src', '')
        if src:
            image_url = f'https:{src}' if src.startswith('//') else src
    
    # Extract price
    price_el = prod_page.css('.price-item')
    price = 0
    if price_el:
        price_text = price_el[0].text
        price_nums = re.findall(r'\d+', price_text.replace('.', ''))
        if price_nums:
            price = int(''.join(price_nums))
    
    if price == 0:
        return None
    
    return {
        'sku': sku,
        'name': name,
        'make': make,
        'price': price,
        'file_urls': [image_url] if image_url else [],
        'scrape_url': full_url,
        'classification': 'bike_b',
    }


def run(dry_run: bool = False):
    """Run the ofsi spider."""
    pipeline = ScraplingPipeline(SPIDER_NAME, dry_run=dry_run)
    pipeline.open()
    
    all_items = []
    seen_skus = set()
    
    for url in START_URLS:
        print(f'\nScraping: {url}')
        try:
            page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
        except Exception as e:
            print(f'  Error: {e}')
            continue
        
        hrefs = get_product_links(page)
        print(f'  Found {len(hrefs)} products')
        
        for href in hrefs:
            sku = href.rsplit('/', 1)[-1]
            if sku in seen_skus:
                continue
            seen_skus.add(sku)
            
            time.sleep(REQUEST_DELAY)  # Be nice to the server
            
            item = scrape_product(page, href)
            if item:
                all_items.append(item)
                print(f'    {item["make"]} {item["name"]}: {item["price"]:,} kr')
    
    print(f'\nProcessing {len(all_items)} items...')
    for item in all_items:
        pipeline.process_item(item)
    
    pipeline.close()
    print(f'\nDone! Scraped {len(all_items)} e-bikes from {SPIDER_NAME}')
    
    return all_items


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Ofsi e-bikes')
    parser.add_argument('--dry-run', action='store_true', help='Run without database')
    args = parser.parse_args()
    
    run(dry_run=args.dry_run)
