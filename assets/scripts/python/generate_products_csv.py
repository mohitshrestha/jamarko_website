"""
generate_products_csv.py
------------------------

Generates a realistic synthetic product catalog for Quarto with:

- Exactly 100 rows (parents + variants)
- Ensures all product types are represented
- Multiple images per product (pipe-delimited)
- Variant-specific SKU, price, slug, and options
- Quantity, restock_threshold, and availability logic
- Optional discounts (~20%)
- Randomized product_dimensions and product_weight
- Stock location and supplier_name included
- Additional_details always non-empty to prevent CSV parsing issues
- Shipping info: cost, ETA, regions
- Columns rearranged for intuitive data entry:
    restock_threshold immediately after stock_availability_status
- Progress bar and execution timing for UX
"""

import csv
import random
import itertools
import re
import time
from tqdm import tqdm

# -------------------------------
# Configuration
# -------------------------------
TOTAL_ROWS = 100

# Define product types and codes
PRODUCT_TYPES = {
    "notebooks": "nb",
    "greeting_cards": "gc",
    "paper_bags": "bag",
    "photo_frames": "pf",
    "lampshades": "ls",
    "wrapping_papers": "wp",
    "boxes": "bx",
    "jewelry_boxes": "jb",
    "pencils": "ps",
    "uncategorized": "uc",
}

CURRENCIES = ["NPR", "INR", "USD", "EUR", "CAD", "AUD"]

# Variant attributes for permutation
SIZES = ["a5", "a4", "small", "medium", "large"]
COLORS = ["black", "white", "brown", "beige", "blue", "green"]
PATTERNS = ["floral", "geometric", "plain", "striped"]
MATERIALS = ["paper", "linen", "wood", "metal", "fabric", "leather"]
FINISHES = ["matte", "glossy", "textured"]

VARIANT_ATTRIBUTES = [
    ["size"], ["color"], ["material"], ["pattern"],
    ["size", "color"], ["size", "pattern"], ["color", "pattern"],
    ["material", "finish"], ["size", "material"]
]

# Shipping realistic ranges
SHIPPING_COST_RANGE = (2.0, 15.0)  # Could be NPR, USD etc.
SHIPPING_ETA_RANGE = (2, 14)       # Days
SHIPPING_REGIONS_DEFAULT = ["Nepal"]

# Other probabilities
DISCOUNT_PROBABILITY = 0.2
RESTOCK_THRESHOLD_PROB = 0.7

# -------------------------------
# Helper Functions
# -------------------------------

def slugify(text: str) -> str:
    """Return a URL-safe slug for Quarto."""
    if not text:
        return "product"
    normalized = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "-", normalized).strip("-")

def pipe_join(values: list) -> str:
    """Join list of strings into a pipe-delimited string."""
    return " | ".join(values)

def placeholder_image(text: str) -> str:
    """Return a placeholder image URL for a given identifier."""
    return f"https://placehold.co/600x600?text={text.replace('_','+')}"

def generate_variant_combinations(attributes: list) -> list:
    """
    Generate up to 3 random permutations of the provided variant attributes.
    Ensures variety in size/color/material/pattern combinations.
    """
    pools = []
    for attr in attributes:
        if attr == "size": pools.append(SIZES)
        elif attr == "color": pools.append(COLORS)
        elif attr == "pattern": pools.append(PATTERNS)
        elif attr == "material": pools.append(MATERIALS)
        elif attr == "finish": pools.append(FINISHES)
    all_combos = list(itertools.product(*pools))
    return [dict(zip(attributes, combo)) for combo in random.sample(all_combos, min(len(all_combos), 3))]

def generate_discount_price(price: float) -> str:
    """Randomly apply discount with given probability."""
    if random.random() <= DISCOUNT_PROBABILITY:
        discount = round(price * random.uniform(0.05, 0.25), 2)
        return str(round(max(0.99, price - discount), 2))
    return ""

def generate_restock_threshold(quantity: int) -> str:
    """Randomly assign restock threshold based on probability."""
    if random.random() <= RESTOCK_THRESHOLD_PROB:
        return str(max(1, int(quantity * random.uniform(0.2, 0.4))))
    return ""

def compute_availability_status(quantity: int, restock_threshold: str = "") -> str:
    """Determine stock availability based on quantity and restock threshold."""
    if quantity == 0:
        return random.choice(["Out of Stock","Backorder","Preorder"])
    try:
        if restock_threshold and quantity <= int(restock_threshold):
            return "Low Stock"
    except ValueError:
        pass
    return "In Stock"

def generate_shipping_cost() -> float:
    return round(random.uniform(*SHIPPING_COST_RANGE), 2)

def generate_shipping_eta() -> str:
    return f"{random.randint(*SHIPPING_ETA_RANGE)} days"

def generate_product_dimensions() -> str:
    """Random product dimensions as L x W x H in inches."""
    return f"{random.randint(3,20)} x {random.randint(3,20)} x {random.randint(1,10)} in"

def generate_product_weight() -> str:
    """Random product weight in lbs."""
    return f"{round(random.uniform(0.5, 15.0),2)} lb"

def generate_stock_location() -> str:
    return random.choice(["Jamarko Warehouse","Jamarko Retail Store A","Jamarko Retail Store B"])

def generate_supplier_name() -> str:
    return "Jamarko"

def generate_additional_details(product_name: str, variant_options: str = "") -> str:
    """Generate bullet-pointed additional details, always non-empty."""
    bullets = [
        f"- Material: {random.choice(MATERIALS)}",
        f"- Dimensions: {generate_product_dimensions()}",
        f"- Weight: {generate_product_weight()}",
        f"- Options: {variant_options}" if variant_options else "",
        f"- High-quality {product_name.replace('_',' ')} product"
    ]
    bullets = [b for b in bullets if b]
    return " ".join(bullets)

# -------------------------------
# Main CSV Generation
# -------------------------------

def generate_products_csv(filename: str = "products.csv"):
    rows = []
    row_count = 0
    product_counter = 1
    start_time = time.time()

    # Ensure all product types are represented at least once
    product_type_cycle = list(PRODUCT_TYPES.keys())
    random.shuffle(product_type_cycle)

    with tqdm(total=TOTAL_ROWS, desc="Generating products", unit="product") as pbar:
        while row_count < TOTAL_ROWS:
            # Cycle through product types first to ensure coverage
            if product_type_cycle:
                product_type = product_type_cycle.pop()
            else:
                product_type = random.choice(list(PRODUCT_TYPES.keys()))
            code = PRODUCT_TYPES[product_type]
            pid = f"{code}{product_counter:03d}"
            sku = f"{code}-{product_counter:03d}"
            base_price = round(random.uniform(2.99, 39.99), 2)
            currency = random.choice(CURRENCIES)
            parent_slug = slugify(f"{product_type}_{product_counter}")

            # Multi-image array
            image_count = random.randint(2,5)
            images = [placeholder_image(f"{pid}_{i}") for i in range(1,image_count+1)]
            image_array = pipe_join(images)

            # Shipping info
            shipping_cost = generate_shipping_cost()
            shipping_eta = generate_shipping_eta()
            shipping_regions = pipe_join(SHIPPING_REGIONS_DEFAULT)

            # Descriptions & metadata
            short_desc = f"High quality {product_type.replace('_',' ')}"
            long_desc = f"High quality {product_type.replace('_',' ')} with multiple variants."
            meta_title = f"{product_type.title()} Product"
            meta_desc = f"Buy premium {product_type} online"
            primary_keyword = product_type
            image_alt_text = f"{product_type} image"

            # ----------------------
            # Variant generation
            # ----------------------
            variant_rows = []
            total_quantity = 0

            if row_count < TOTAL_ROWS and random.random() < 0.8:
                attr_set = random.choice(VARIANT_ATTRIBUTES)
                variant_combos = generate_variant_combinations(attr_set)
                for combo in variant_combos:
                    if row_count >= TOTAL_ROWS:
                        break
                    values = list(combo.values())
                    variant_id = f"{pid}-{'-'.join(values)}"
                    variant_sku = f"{sku}-{'-'.join(values)}"
                    variant_price = round(max(0.99, base_price + base_price*random.uniform(-0.10,0.20)),2)
                    variant_images = [placeholder_image(f"{variant_id}_{i}") for i in range(1, random.randint(2,4)+1)]
                    variant_options_str = pipe_join([f"{k}:{v}" for k,v in combo.items()])
                    variant_quantity = random.randint(0, 20)
                    restock_threshold = generate_restock_threshold(variant_quantity)
                    availability_status = compute_availability_status(variant_quantity, restock_threshold)
                    discount_price = generate_discount_price(variant_price)
                    additional_details = generate_additional_details(product_type, variant_options_str)
                    
                    variant_row = [
                        variant_id, pid, f"{product_type}_{product_counter}", variant_sku, variant_options_str,
                        variant_price, currency, variant_quantity, availability_status, restock_threshold,
                        product_type, slugify(f"{parent_slug}-{'-'.join(values)}"), short_desc, long_desc, 
                        pipe_join(variant_images), meta_title, meta_desc, primary_keyword, image_alt_text,
                        round(random.uniform(4.2,4.9),1), random.randint(5,300), discount_price,
                        round(variant_price*random.uniform(0.5,0.8),2), "30 day return", generate_product_dimensions(),
                        generate_product_weight(), generate_stock_location(), generate_supplier_name(),
                        additional_details, shipping_cost, shipping_eta, shipping_regions
                    ]
                    variant_rows.append(variant_row)
                    total_quantity += variant_quantity
                    row_count += 1
                    pbar.update(1)

            # ----------------------
            # Parent product row
            # ----------------------
            parent_availability = compute_availability_status(total_quantity)
            parent_row = [
                pid, "", f"{product_type}_{product_counter}", sku, "",
                base_price, currency, total_quantity, parent_availability,
                generate_restock_threshold(total_quantity),
                product_type, parent_slug, short_desc, long_desc, image_array,
                meta_title, meta_desc, primary_keyword, image_alt_text,
                round(random.uniform(4.2,4.9),1), random.randint(5,300), "", 
                round(base_price*random.uniform(0.5,0.8),2), "30 day return", generate_product_dimensions(),
                generate_product_weight(), generate_stock_location(), generate_supplier_name(),
                generate_additional_details(product_type), shipping_cost, shipping_eta, shipping_regions
            ]
            rows.append(parent_row)
            rows.extend(variant_rows)
            row_count += 1
            pbar.update(1)
            product_counter += 1

    # ----------------------
    # CSV Header
    # ----------------------
    header = [
        "product_id","parent_product_id","product_name","sku","variant_options","price","currency",
        "quantity_available","stock_availability_status","restock_threshold","product_type","product_url_slug",
        "product_short_description","product_description","product_images","meta_title","meta_description",
        "primary_keyword","image_alt_text","product_rating","review_count","discount_price","cost_price",
        "return_policy","product_dimensions","product_weight","stock_location","supplier_name",
        "additional_details","shipping_cost","shipping_time_eta","shipping_regions"
    ]

    # ----------------------
    # Write CSV
    # ----------------------
    with open(filename,"w",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    # Execution timing
    end_time = time.time()
    duration = end_time - start_time
    mins, secs = divmod(int(duration), 60)
    print(f"\n✅ {filename} generated with {len(rows)} rows in {mins}m {secs}s.")

# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    generate_products_csv()
