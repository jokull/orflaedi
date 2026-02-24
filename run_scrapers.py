#!/usr/bin/env python3
"""
Hybrid scraper runner for orflaedi.
- Uses Scrapy for static sites (fast)
- Uses Scrapling/Playwright for JS-rendered sites

Usage:
  python run_scrapers.py              # Run all scrapers
  python run_scrapers.py --dry-run    # Dry run (no DB writes)
  python run_scrapers.py --only elko  # Run specific spider(s)
  python run_scrapers.py --list       # List all spiders and their status
"""
import os
import sys
import argparse
import subprocess
from typing import Literal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Spider configuration
# Static sites use Scrapy, JS sites use Scrapling/Playwright
SPIDERS = {
    # Working Scrapy spiders (static HTML)
    "tri": {"engine": "scrapy", "status": "working"},
    "orninn": {"engine": "scrapy", "status": "working"},
    "kria": {"engine": "scrapy", "status": "working"},
    "ofsi": {"engine": "scrapling", "status": "working"},  # StealthyFetcher to bypass 429s
    "markid": {"engine": "scrapy", "status": "working"},
    "peloton": {"engine": "scrapy", "status": "working"},
    "hjolasprettur": {"engine": "scrapy", "status": "working"},
    "everest": {"engine": "scrapy", "status": "working"},
    "hvellur": {"engine": "scrapy", "status": "working"},
    "rafmagnshjol": {"engine": "scrapy", "status": "working"},
    
    # JS-rendered sites - use Scrapling/Playwright
    "ellingsen": {"engine": "scrapling", "status": "working"},
    
    # TODO: Need Scrapling migration
    "elko": {"engine": "scrapling", "status": "working"},
    "bike": {"engine": "scrapling", "status": "todo"},  # fjallakofinn.is
    "berlin": {"engine": "scrapling", "status": "todo"},
    "gap": {"engine": "scrapling", "status": "todo"},
    "gastec": {"engine": "scrapling", "status": "todo"},
    "husasmidjan": {"engine": "scrapling", "status": "todo"},
    "kuldi": {"engine": "scrapling", "status": "todo"},
    "sensa": {"engine": "scrapling", "status": "todo"},
    "skidathjonustan": {"engine": "scrapling", "status": "todo"},
    "t2": {"engine": "scrapling", "status": "todo"},
    "thruman": {"engine": "scrapling", "status": "todo"},
}


def run_scrapy_spider(name: str, dry_run: bool = False) -> bool:
    """Run a Scrapy spider."""
    print(f"\n{'='*60}")
    print(f"Running Scrapy spider: {name}")
    print('='*60)
    
    cmd = ["scrapy", "crawl", name]
    if dry_run:
        cmd.extend(["-s", "ITEM_PIPELINES={}"])
    
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(__file__), timeout=300)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Spider {name} timed out!")
        return False
    except Exception as e:
        print(f"Error running {name}: {e}")
        return False


def run_scrapling_spider(name: str, dry_run: bool = False) -> bool:
    """Run a Scrapling/Playwright spider."""
    print(f"\n{'='*60}")
    print(f"Running Scrapling spider: {name}")
    print('='*60)
    
    spider_path = os.path.join(
        os.path.dirname(__file__), 
        "scrape", "scrapling_spiders", f"{name}.py"
    )
    
    if not os.path.exists(spider_path):
        print(f"Spider file not found: {spider_path}")
        return False
    
    cmd = ["python", spider_path]
    if dry_run:
        cmd.append("--dry-run")
    
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(__file__), timeout=300)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Spider {name} timed out!")
        return False
    except Exception as e:
        print(f"Error running {name}: {e}")
        return False


def list_spiders():
    """List all spiders and their status."""
    print("\nSpider Status:")
    print("-" * 60)
    
    for engine in ["scrapy", "scrapling"]:
        print(f"\n{engine.upper()} spiders:")
        for name, config in SPIDERS.items():
            if config["engine"] == engine:
                status_icon = "✅" if config["status"] == "working" else "❌"
                print(f"  {status_icon} {name}: {config['status']}")


def run_all(dry_run: bool = False, only: list[str] = None):
    """Run all working spiders."""
    results = {"success": [], "failed": [], "skipped": []}
    
    for name, config in SPIDERS.items():
        # Filter by --only if specified
        if only and name not in only:
            continue
        
        # Skip non-working spiders unless explicitly requested
        if config["status"] != "working" and not only:
            results["skipped"].append(name)
            continue
        
        # Run the appropriate engine
        if config["engine"] == "scrapy":
            success = run_scrapy_spider(name, dry_run)
        else:
            success = run_scrapling_spider(name, dry_run)
        
        if success:
            results["success"].append(name)
        else:
            results["failed"].append(name)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Success: {len(results['success'])} - {', '.join(results['success']) or 'none'}")
    print(f"❌ Failed:  {len(results['failed'])} - {', '.join(results['failed']) or 'none'}")
    print(f"⏭️  Skipped: {len(results['skipped'])} - {', '.join(results['skipped']) or 'none'}")
    
    return len(results["failed"]) == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run orflaedi scrapers")
    parser.add_argument("--dry-run", action="store_true", help="Run without database writes")
    parser.add_argument("--only", nargs="+", help="Run only specific spider(s)")
    parser.add_argument("--list", action="store_true", help="List all spiders")
    args = parser.parse_args()
    
    if args.list:
        list_spiders()
        sys.exit(0)
    
    success = run_all(dry_run=args.dry_run, only=args.only)
    sys.exit(0 if success else 1)
