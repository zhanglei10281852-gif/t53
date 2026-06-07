import csv
import random
from datetime import date, timedelta

PRODUCTS = [
    ("黄芪", "500g/包", 24, 45.0),
    ("当归", "250g/包", 36, 68.0),
    ("党参", "500g/包", 24, 52.0),
    ("白术", "500g/包", 24, 38.0),
    ("茯苓", "500g/包", 36, 42.0),
    ("甘草", "500g/包", 48, 28.0),
    ("白芍", "500g/包", 36, 46.0),
    ("熟地黄", "500g/包", 36, 58.0),
    ("川芎", "250g/包", 24, 35.0),
    ("枸杞子", "250g/袋", 18, 48.0),
    ("红枣", "500g/袋", 12, 25.0),
    ("桂圆肉", "250g/袋", 12, 55.0),
    ("山药", "500g/包", 24, 32.0),
    ("薏苡仁", "500g/包", 18, 26.0),
    ("莲子", "500g/包", 18, 42.0),
    ("陈皮", "250g/袋", 48, 30.0),
    ("半夏", "250g/包", 36, 58.0),
    ("枳实", "250g/包", 24, 36.0),
    ("厚朴", "250g/包", 36, 40.0),
    ("木香", "250g/包", 24, 65.0),
    ("砂仁", "100g/瓶", 24, 88.0),
    ("白豆蔻", "100g/瓶", 24, 75.0),
    ("金银花", "100g/袋", 18, 60.0),
    ("连翘", "250g/包", 24, 45.0),
    ("板蓝根", "500g/包", 24, 32.0),
    ("菊花", "100g/袋", 12, 35.0),
    ("薄荷", "100g/袋", 18, 28.0),
    ("桑叶", "250g/包", 24, 22.0),
    ("柴胡", "250g/包", 36, 50.0),
    ("黄芩", "250g/包", 36, 42.0),
]

REFERENCE_DATE = date(2026, 6, 7)


def random_past_date(days_ago_min, days_ago_max):
    days = random.randint(days_ago_min, days_ago_max)
    return REFERENCE_DATE - timedelta(days=days)


def generate_batch(name, spec, shelf_life, price, shelf_prefix, batch_suffix, expiry_category):
    if expiry_category == "expired":
        shelf_life_days = shelf_life * 30
        production_days_ago = shelf_life_days + random.randint(10, 200)
    elif expiry_category == "red_alert":
        shelf_life_days = shelf_life * 30
        production_days_ago = shelf_life_days - random.randint(1, 90)
    elif expiry_category == "yellow_alert":
        shelf_life_days = shelf_life * 30
        production_days_ago = shelf_life_days - random.randint(91, 180)
    else:
        shelf_life_days = shelf_life * 30
        production_days_ago = shelf_life_days - random.randint(181, shelf_life_days - 30)

    production_date = REFERENCE_DATE - timedelta(days=production_days_ago)
    batch_number = f"{production_date.strftime('%Y%m')}{batch_suffix:03d}"
    quantity = round(random.uniform(0, 50), 1)
    location = f"{shelf_prefix}{random.randint(1, 5):02d}-{random.randint(1, 4):02d}"

    return {
        "品名": name,
        "规格": spec,
        "批次号": batch_number,
        "生产日期": production_date.strftime("%Y-%m-%d"),
        "保质期月数": shelf_life,
        "库存数量": quantity,
        "存放位置": location,
        "单价": price,
    }


def main():
    random.seed(42)
    rows = []

    categories = ["normal", "normal", "yellow_alert", "red_alert", "expired"]

    batch_counter = 1
    for i, (name, spec, shelf_life, price) in enumerate(PRODUCTS):
        num_batches = random.choice([2, 2, 3])
        shelf_prefix = chr(ord('A') + (i // 10))

        for b in range(num_batches):
            if b == 0:
                category = categories[i % len(categories)]
            else:
                category = random.choice(categories)

            row = generate_batch(
                name, spec, shelf_life, price, shelf_prefix, batch_counter, category
            )
            rows.append(row)
            batch_counter += 1

    rows[5]["库存数量"] = 0

    oos_product = PRODUCTS[14][0]
    for row in rows:
        if row["品名"] == oos_product:
            row["库存数量"] = 0

    with open("inventory.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "品名",
                "规格",
                "批次号",
                "生产日期",
                "保质期月数",
                "库存数量",
                "存放位置",
                "单价",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows with {len(PRODUCTS)} products")


if __name__ == "__main__":
    main()
