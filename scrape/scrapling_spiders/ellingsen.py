"""
Ellingsen e-bike scraper using Playwright (handles JS-rendered s4s.is)

Run dry:  python scrape/scrapling_spiders/ellingsen.py --dry-run
Run live: python scrape/scrapling_spiders/ellingsen.py
"""
import re
import argparse
from playwright.sync_api import sync_playwright

from base import ScraplingPipeline


SPIDER_NAME = "ellingsen"

START_URLS = [
    "https://s4s.is/ellingsen/rafhjol/oell-rafhjol",
]

# Minimum price to filter out accessories (100,000 ISK)
MIN_PRICE = 100000

STRIPWORDS = [
    "svart", "hvítt", "blátt", "gult", "rautt", "brúnt", "grátt",
    "17.5ah", "36v", "ebike", "rafhlaupahjól", "rafhjól", "fjallarafhjól",
]


def scrape_page(page, url) -> list[dict]:
    """Scrape a single category page."""
    items = []
    
    page.goto(url, timeout=60000)
    page.wait_for_load_state('networkidle', timeout=45000)
    
    cards = page.query_selector_all('.productCard')
    print(f'Found {len(cards)} product cards on {url}')
    
    for card in cards:
        try:
            # Get product link
            link = card.query_selector('a')
            if not link:
                continue
            href = link.get_attribute('href')
            
            # Extract image
            image_el = card.query_selector('.productImage')
            image_url = image_el.get_attribute('src') if image_el else None
            if image_url:
                # Get higher resolution
                image_url = image_url.replace('855', '5000').replace('925', '5000')
            
            # Extract brand/make
            brand_el = card.query_selector('.productBrand')
            make = brand_el.inner_text().strip() if brand_el else None
            
            # Extract price
            price_el = card.query_selector('.productPrice')
            price_text = price_el.inner_text() if price_el else '0'
            price = int(''.join(re.findall(r'\d+', price_text))) if price_text else 0
            
            # Extract name
            name_el = card.query_selector('.productName')
            name = name_el.inner_text().strip() if name_el else None
            
            # Filter: skip items with no name, no price, or low price (accessories)
            if not name or price == 0 or price < MIN_PRICE:
                continue
            
            # Clean up make
            if make == "Riese & Muller":
                make = "Riese & Müller"
            
            # Remove make from name if duplicated
            if make and make in name:
                name = name.replace(make, '').strip()
            
            # Remove color/spec words from name
            name = ' '.join(w for w in name.split() if w.lower() not in STRIPWORDS)
            
            # Generate SKU from URL (productNumber class no longer exists on site)
            sku = href.split('ProductId=')[-1] if 'ProductId=' in href else href.split('/')[-1]
            
            # Determine classification (e-scooters vs e-bikes)
            classification = 'bike_c' if 'rafhlaupahjol' in url else 'bike_b'
            
            item = {
                'sku': sku,
                'name': name,
                'make': make,
                'price': price,
                'file_urls': [image_url] if image_url else [],
                'scrape_url': f'https://s4s.is{href}' if href.startswith('/') else href,
                'classification': classification,
            }
            items.append(item)
            
        except Exception as e:
            print(f'Error processing card: {e}')
            continue
    
    return items


def run(dry_run: bool = False):
    """Run the ellingsen spider."""
    pipeline = ScraplingPipeline(SPIDER_NAME, dry_run=dry_run)
    pipeline.open()
    
    all_items = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for url in START_URLS:
            items = scrape_page(page, url)
            all_items.extend(items)
        
        browser.close()
    
    print(f'\nProcessing {len(all_items)} items...')
    for item in all_items:
        pipeline.process_item(item)
    
    pipeline.close()
    print(f'\nDone! Scraped {len(all_items)} e-bikes from {SPIDER_NAME}')
    
    return all_items


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Ellingsen e-bikes')
    parser.add_argument('--dry-run', action='store_true', help='Run without database')
    args = parser.parse_args()
    
    run(dry_run=args.dry_run)
