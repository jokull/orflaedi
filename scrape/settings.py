SPIDER_MODULES = ["scrape.spiders"]
ITEM_PIPELINES = {
    "scrape.pipelines.DatabasePipeline": 100,
}
