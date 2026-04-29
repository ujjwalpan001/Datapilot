"""Generate a sample sales CSV dataset for testing DataPilot AI."""

import os
import random
import csv
from datetime import datetime, timedelta


def generate_sample_data(output_path: str = "./uploads/sample_sales.csv", num_rows: int = 2000):
    """Generate a sample sales dataset with realistic data."""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    products = [
        "Wireless Mouse", "USB-C Hub", "Mechanical Keyboard", "Monitor Stand",
        "Laptop Sleeve", "Webcam HD", "Desk Lamp", "Bluetooth Speaker",
        "External SSD", "Noise Cancelling Headphones", "Smart Pen", "Tablet Stand",
        "Power Bank", "HDMI Cable", "Ethernet Adapter", "Wireless Charger",
        "Screen Protector", "Phone Mount", "Cable Organizer", "Mouse Pad",
    ]

    categories = ["Electronics", "Accessories", "Office", "Audio", "Storage"]

    regions = ["North", "South", "East", "West"]

    customer_segments = ["Consumer", "Corporate", "Home Office", "Small Business"]

    product_category_map = {
        "Wireless Mouse": "Electronics", "USB-C Hub": "Electronics",
        "Mechanical Keyboard": "Electronics", "Monitor Stand": "Office",
        "Laptop Sleeve": "Accessories", "Webcam HD": "Electronics",
        "Desk Lamp": "Office", "Bluetooth Speaker": "Audio",
        "External SSD": "Storage", "Noise Cancelling Headphones": "Audio",
        "Smart Pen": "Electronics", "Tablet Stand": "Accessories",
        "Power Bank": "Electronics", "HDMI Cable": "Accessories",
        "Ethernet Adapter": "Electronics", "Wireless Charger": "Electronics",
        "Screen Protector": "Accessories", "Phone Mount": "Accessories",
        "Cable Organizer": "Accessories", "Mouse Pad": "Accessories",
    }

    product_price_range = {
        "Wireless Mouse": (15, 45), "USB-C Hub": (20, 60),
        "Mechanical Keyboard": (50, 180), "Monitor Stand": (25, 80),
        "Laptop Sleeve": (12, 40), "Webcam HD": (35, 120),
        "Desk Lamp": (18, 65), "Bluetooth Speaker": (25, 150),
        "External SSD": (45, 200), "Noise Cancelling Headphones": (80, 350),
        "Smart Pen": (30, 100), "Tablet Stand": (15, 50),
        "Power Bank": (20, 75), "HDMI Cable": (5, 25),
        "Ethernet Adapter": (10, 35), "Wireless Charger": (15, 55),
        "Screen Protector": (5, 20), "Phone Mount": (8, 30),
        "Cable Organizer": (5, 20), "Mouse Pad": (8, 35),
    }

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    days_range = (end_date - start_date).days

    rows = []
    for i in range(1, num_rows + 1):
        product = random.choice(products)
        category = product_category_map.get(product, random.choice(categories))
        region = random.choice(regions)
        segment = random.choice(customer_segments)
        quantity = random.randint(1, 20)
        price_min, price_max = product_price_range.get(product, (10, 100))
        unit_price = round(random.uniform(price_min, price_max), 2)
        total_revenue = round(quantity * unit_price, 2)
        order_date = start_date + timedelta(days=random.randint(0, days_range))

        rows.append({
            "order_id": f"ORD-{i:05d}",
            "product_name": product,
            "category": category,
            "region": region,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_revenue": total_revenue,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "customer_segment": segment,
        })

    # Write CSV
    fieldnames = ["order_id", "product_name", "category", "region", "quantity",
                  "unit_price", "total_revenue", "order_date", "customer_segment"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Generated {num_rows} rows -> {output_path}")
    return output_path


if __name__ == "__main__":
    generate_sample_data()
