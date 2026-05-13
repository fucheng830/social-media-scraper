# social-media-scraper

Playwright-based social media scraping engine with DB-stored rules.

## Installation

```bash
pip install -e .
playwright install
```

## Quick Start

```python
from social_media_scraper import PlatformPost, BaseScraper

# Implement a platform-specific scraper by extending BaseScraper
class MyScraper(BaseScraper):
    platform = "myplatform"
    ...
```
