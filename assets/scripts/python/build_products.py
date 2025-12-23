"""
build_products.py
-----------------
Generates Quarto product pages from CSV product data with fully functional
variant dropdowns, gallery thumbnails, pricing display, cost breakdown,
progress bar, and execution timing.

Design goals:
- Clean, maintainable, readable code
- Minimal repetition
- Fully functional variant page navigation
- Locale-aware pricing and multiple currency support
- GitHub Pages compatible (no server-side templating)
"""

from pathlib import Path
from typing import Dict, List, Optional
import unicodedata
import re
import polars as pl
import locale
import time
from tqdm import tqdm

# ============================================================
# Paths & Defaults
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "data" / "products.csv"
TEMPLATE_PATH = BASE_DIR / "shop" / "_templates" / "product_template.qmd"
OUTPUT_DIR = BASE_DIR / "shop"

DEFAULT_LANGUAGE = "en"
DEFAULT_CURRENCY = "npr"
DEFAULT_PRODUCT_TYPE = "uncategorized"

# ============================================================
# Currency Configuration
# ============================================================

CURRENCY_CONFIG = {
    "usd": {"symbol": "$", "locale": "en_US.UTF-8"},
    "npr": {"symbol": "रू", "locale": "ne_NP.UTF-8"},
    "inr": {"symbol": "₹", "locale": "en_IN.UTF-8"},
    "eur": {"symbol": "€", "locale": "de_DE.UTF-8"},
    "cad": {"symbol": "CA$", "locale": "en_CA.UTF-8"},
    "aud": {"symbol": "A$", "locale": "en_AU.UTF-8"},
}

# ============================================================
# Cost Fields (single source of truth)
# ============================================================

COST_FIELDS = {
    "price",
    "discount_price",
    "shipping_cost",
    "tax_amount",
    "handling_fee",
}

# ============================================================
# Utility Functions
# ============================================================

def slugify(text: Optional[str]) -> str:
    if not text:
        return "product"
    normalized = unicodedata.normalize("NFKD", text.lower())
    cleaned = re.sub(r"[^\w\s-]", "", normalized)
    collapsed = re.sub(r"[\s_-]+", "-", cleaned)
    return collapsed.strip("-")

def parse_pipe_separated(value: Optional[str]) -> List[str]:
    return [item.strip() for item in value.split("|")] if value else []

def get_currency_config(currency_code: str) -> Dict[str, str]:
    return CURRENCY_CONFIG.get(currency_code.lower(), CURRENCY_CONFIG[DEFAULT_CURRENCY])

def format_price(value: Optional[float], currency_code: str) -> str:
    if value is None or value == "":
        return ""
    config = get_currency_config(currency_code)
    try:
        locale.setlocale(locale.LC_ALL, config["locale"])
        return f"{config['symbol']}{locale.currency(float(value), False, True)}"
    except Exception:
        return f"{config['symbol']}{float(value):,.2f}"

def format_cost(value: Optional[float], currency_code: str) -> str:
    return format_price(value, currency_code)

def format_duration(seconds: float) -> str:
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{int(hours)}h {int(mins)}m {secs:.2f}s"
    if mins:
        return f"{int(mins)}m {secs:.2f}s"
    return f"{secs:.2f}s"

def get_availability_label(stock_status: Optional[str]) -> str:
    return f"Availability: {stock_status}" if stock_status else "Availability: Unknown"

# ============================================================
# HTML Generators
# ============================================================

def generate_gallery_thumbnails(images: List[str], alt_text: str) -> str:
    return "\n".join(
        f'<img src="{img}" class="thumbnail" alt="{alt_text}" loading="lazy" data-thumb />'
        for img in images
    )

def generate_price_html(product: Dict) -> str:
    currency = product.get("currency", DEFAULT_CURRENCY)
    if product.get("discount_price"):
        return (
            f'<span class="price-discount">{format_price(product["discount_price"], currency)}</span>'
            f'<span class="price-original">{format_price(product["price"], currency)}</span>'
        )
    return f'<span class="price">{format_price(product["price"], currency)}</span>'

def generate_variants_html(variants: List[Dict]) -> str:
    if not variants:
        return ""
    options = []
    for v in variants:
        name = v.get("variant_name", "Option").replace('"', "&quot;")
        options.append(
            f'<option value="{v["slug"]}" data-sku="{v["sku"]}" data-price="{v["price"]}">{name}</option>'
        )
    return (
        '<select class="product-variants" id="variantSelect" onchange="onVariantChange(this)">\n'
        + "\n".join(options)
        + "\n</select>"
    )

def generate_cost_breakdown(product: Dict) -> str:
    currency = product.get("currency", DEFAULT_CURRENCY)
    rows = []
    for field in COST_FIELDS - {"price", "discount_price"}:
        if product.get(field):
            label = field.replace("_", " ").title()
            value = format_cost(product[field], currency)
            rows.append(
                f"<div class='cost-row'><span>{label}</span><span>{value}</span></div>"
            )
    return "\n".join(rows)

# ============================================================
# Template Context
# ============================================================

def build_template_context(
    product: Dict,
    slug: str,
    images: List[str],
    variants: List[Dict]
) -> Dict[str, str]:

    currency = product.get("currency", DEFAULT_CURRENCY)
    context = {}

    for key, value in product.items():
        if key in COST_FIELDS:
            context[f"product.{key}"] = format_cost(value, currency)
        else:
            context[f"product.{key}"] = str(value or "")

    context.update({
        "product.slug": slug,
        "product.main_image": images[0] if images else "",
        "product.gallery_images": "|".join(images),
        "product.gallery_thumbnails": generate_gallery_thumbnails(
            images, product.get("image_alt_text", "")
        ),
        "product.price_html": generate_price_html(product),
        "product.availability": get_availability_label(
            product.get("stock_availability_status")
        ),
        "product.variants_html": generate_variants_html(variants),
        "product.cost_breakdown": generate_cost_breakdown(product),
    })

    return context

# ============================================================
# File Writers
# ============================================================

def render_template(template: str, context: Dict[str, str]) -> str:
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{ {key} }}}}", value)
    return rendered

def write_product_page(product_type: str, slug: str, content: str) -> None:
    out_dir = OUTPUT_DIR / slugify(product_type) / "products"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.qmd").write_text(content, encoding="utf-8")

def write_product_type_index(product_type: str) -> None:
    index_content = f"""---
title: "{product_type.capitalize()}"
listing:
  contents: "products"
  fields: [image, title, categories]
  image-placeholder: ..\\..\\assets\\media\\images\\logos_and_banners\\logo.png
  feed: 
    items: 10
  sort:
    - "date"
    - "title asc"
  type: grid
  categories: true
  sort-ui: [title, date]
  filter-ui: [title, date]
---
"""
    out_dir = OUTPUT_DIR / slugify(product_type)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.qmd").write_text(index_content, encoding="utf-8")

# ============================================================
# Orchestrator
# ============================================================

def build_product_pages(df: pl.DataFrame) -> int:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    seen_types = set()
    page_count = 0

    for record in tqdm(
        df.iter_rows(named=True),
        total=df.height,
        desc="Building product pages",
        unit="product"
    ):
        slug = slugify(record.get("product_url_slug") or record.get("product_name"))
        images = parse_pipe_separated(record.get("product_images"))
        product_types = parse_pipe_separated(record.get("product_type")) or [DEFAULT_PRODUCT_TYPE]

        parent_id = record.get("parent_product_id") or record.get("product_id")
        variants_rows = df.filter(pl.col("parent_product_id") == parent_id).to_dicts()
        variants = [
            {
                "variant_name": " | ".join(parse_pipe_separated(v.get("variant_options"))),
                "sku": v.get("sku"),
                "price": v.get("price"),
                "slug": slugify(v.get("product_url_slug") or v.get("product_name"))
            }
            for v in variants_rows
        ] if variants_rows else []

        context = build_template_context(record, slug, images, variants)
        rendered_page = render_template(template, context)

        for product_type in product_types:
            write_product_page(product_type, slug, rendered_page)
            seen_types.add(product_type)
            page_count += 1

    for product_type in seen_types:
        write_product_type_index(product_type)

    return page_count

# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    start = time.perf_counter()

    df = pl.read_csv(DATA_PATH)
    df.columns = [c.lower().strip() for c in df.columns]

    total_pages = build_product_pages(df)

    elapsed = time.perf_counter() - start

    print("\n✅ Build completed successfully")
    print(f"📄 Total product pages generated: {total_pages}")
    print(f"⏱️  Time taken: {format_duration(elapsed)}")
