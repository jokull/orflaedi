"""
Elko e-scooter/e-bike scraper using Playwright (handles JS-rendered Next.js)

Run dry:  python scrape/scrapling_spiders/elko.py --dry-run
Run live: python scrape/scrapling_spiders/elko.py
"""
import re
import argparse
from playwright.sync_api import sync_playwright

from base import ScraplingPipeline


SPIDER_NAME = "elko"

START_URLS = [
    "https://elko.is/voruflokkar/farartaeki-339?categories=188",  # Farartæki
    "https://elko.is/voruflokkar/lett-bifhjol-287",  # Létt bifhjól
]

# Minimum price to filter accessories
MIN_PRICE = 30000


def get_product_links(page) -> list[str]:
    """Get all unique product links from a category page."""
    link_els = page.query_selector_all('a[href*="/vorur/"]')
    hrefs = []
    for link in link_els:
        href = link.get_attribute('href')
        if href and href not in hrefs:
            hrefs.append(href)
    return hrefs


def scrape_product(page, href: str) -> dict | None:
    """Scrape a single product page."""
    full_url = f'https://elko.is{href}' if href.startswith('/') else href
    
    try:
        page.goto(full_url, timeout=60000)
        page.wait_for_load_state('networkidle', timeout=30000)
    except Exception as e:
        print(f'Error loading {full_url}: {e}')
        return None
    
    # Get title from h2 or og:title
    h2 = page.query_selector('h2')
    if h2:
        title = h2.inner_text().strip()
    else:
        og_title = page.query_selector('meta[property="og:title"]')
        title = og_title.get_attribute('content').replace(' | ELKO', '') if og_title else None
    
    if not title:
        return None
    
    # Parse make and name from title
    # Title format: "Xiaomi Scooter 5 rafmagnshlaupahjól - Svart"
    title_clean = title.split(' - ')[0]  # Remove color suffix
    parts = title_clean.split(' ', 1)
    make = parts[0] if len(parts) > 1 else None
    name = parts[1] if len(parts) > 1 else title_clean
    
    # Get price - look for the main price element first, fallback to regex
    price = 0
    
    # Try to find the primary price display (usually has "large" or specific price class)
    price_el = page.query_selector('[class*="large"]')
    if price_el:
        price_text = price_el.inner_text()
        price_nums = re.findall(r'\d+', price_text.replace('.', ''))
        if price_nums:
            price = int(''.join(price_nums))
    
    # Fallback: find prices in content, take the one most likely to be the product price
    if price == 0:
        content = page.content()
        price_matches = re.findall(r'(\d{1,3}(?:\.\d{3})*)\s*kr', content)
        # Filter to reasonable product prices (30k-500k range for e-scooters/bikes)
        prices = [int(p.replace('.', '')) for p in price_matches 
                  if 30000 <= int(p.replace('.', '')) <= 500000]
        price = prices[0] if prices else 0  # Take first (usually the main price)
    
    if price < MIN_PRICE:
        return None
    
    # Get SKU from URL
    sku = href.split('/')[-1]
    
    # Get image
    img = page.query_selector('img[src*="cdn.contextsuite"]')
    img_url = img.get_attribute('src') if img else None
    
    # Determine classification based on title keywords
    title_lower = title.lower()
    if 'rafmagnshlaupahjól' in title_lower or 'hlaupahjól' in title_lower or 'scooter' in title_lower:
        classification = 'bike_c'  # E-scooter
    elif 'létt bifhjól' in title_lower or 'hraðhjól' in title_lower:
        classification = 'lb_2'  # Light moped
    else:
        classification = 'bike_b'  # Default to e-bike
    
    # Clean name
    for word in ['rafmagnshlaupahjól', 'rafmagnsbifhjól', 'rafhjól', 'létt bifhjól']:
        name = name.replace(word, '').strip()
    
    return {
        'sku': sku,
        'name': name.strip(),
        'make': make,
        'price': price,
        'file_urls': [img_url] if img_url else [],
        'scrape_url': full_url,
        'classification': classification,
    }


def run(dry_run: bool = False):
    """Run the elko spider."""
    pipeline = ScraplingPipeline(SPIDER_NAME, dry_run=dry_run)
    pipeline.open()
    
    all_items = []
    seen_skus = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for url in START_URLS:
            print(f'\nScraping category: {url}')
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            hrefs = get_product_links(page)
            print(f'Found {len(hrefs)} product links')
            
            for href in hrefs:
                sku = href.split('/')[-1]
                if sku in seen_skus:
                    continue
                seen_skus.add(sku)
                
                item = scrape_product(page, href)
                if item:
                    all_items.append(item)
                    print(f'  {item["make"]} {item["name"]}: {item["price"]:,} kr')
        
        browser.close()
    
    print(f'\nProcessing {len(all_items)} items...')
    for item in all_items:
        pipeline.process_item(item)
    
    pipeline.close()
    print(f'\nDone! Scraped {len(all_items)} items from {SPIDER_NAME}')
    
    return all_items


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Elko e-scooters/e-bikes')
    parser.add_argument('--dry-run', action='store_true', help='Run without database')
    args = parser.parse_args()
    
    run(dry_run=args.dry_run)
