import polars as pl
import yaml

def validate_data(products):
    with open('data/schema.yml', 'r') as f:
        schema = yaml.safe_load(f)
    
    for product in products.iter_rows(named=True):
        for field in schema['products']:
            if field not in product:
                print(f"Missing field: {field}")
                return False
    return True
