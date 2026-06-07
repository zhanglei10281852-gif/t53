import calendar
import csv
from datetime import date, datetime
from typing import List, Dict, Tuple

from models import (
    InventoryItem,
    InventoryItemWithExpiry,
    ProductSummary,
    ExpiryStatus,
    ValidationError,
)


def add_months(start_date: date, months: int) -> date:
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_expiry(item: InventoryItem, reference_date: date) -> date:
    return add_months(item.production_date, item.shelf_life_months)


def calculate_days_remaining(expiry_date: date, reference_date: date) -> int:
    return (expiry_date - reference_date).days


def enrich_inventory_items(
    items: List[InventoryItem], reference_date: date
) -> List[InventoryItemWithExpiry]:
    result = []
    for item in items:
        expiry_date = calculate_expiry(item, reference_date)
        days_remaining = calculate_days_remaining(expiry_date, reference_date)
        expiry_status = ExpiryStatus.from_days_remaining(days_remaining)
        result.append(
            InventoryItemWithExpiry(
                name=item.name,
                specification=item.specification,
                batch_number=item.batch_number,
                production_date=item.production_date,
                shelf_life_months=item.shelf_life_months,
                quantity=item.quantity,
                location=item.location,
                unit_price=item.unit_price,
                expiry_date=expiry_date,
                days_remaining=days_remaining,
                expiry_status=expiry_status,
            )
        )
    return result


def summarize_by_product(
    items: List[InventoryItemWithExpiry],
) -> List[ProductSummary]:
    product_map: Dict[str, List[InventoryItemWithExpiry]] = {}
    for item in items:
        if item.name not in product_map:
            product_map[item.name] = []
        product_map[item.name].append(item)

    summaries = []
    for name, product_items in product_map.items():
        total_quantity = sum(item.quantity for item in product_items)
        total_value = sum(item.total_value for item in product_items)
        batch_count = len(product_items)

        sorted_items = sorted(product_items, key=lambda x: x.expiry_date)
        earliest_item = sorted_items[0]
        earliest_expiry_date = earliest_item.expiry_date
        earliest_expiry_status = earliest_item.expiry_status

        is_out_of_stock = total_quantity <= 0

        summaries.append(
            ProductSummary(
                name=name,
                total_quantity=total_quantity,
                total_value=total_value,
                batch_count=batch_count,
                earliest_expiry_date=earliest_expiry_date,
                earliest_expiry_status=earliest_expiry_status,
                is_out_of_stock=is_out_of_stock,
            )
        )

    summaries.sort(key=lambda s: s.earliest_expiry_status.priority)
    return summaries


def read_inventory(file_path: str) -> List[InventoryItem]:
    items = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            production_date = datetime.strptime(
                row["生产日期"], "%Y-%m-%d"
            ).date()
            shelf_life_months = int(row["保质期月数"])
            quantity = float(row["库存数量"])
            unit_price = float(row["单价"])
            items.append(
                InventoryItem(
                    name=row["品名"],
                    specification=row["规格"],
                    batch_number=row["批次号"],
                    production_date=production_date,
                    shelf_life_months=shelf_life_months,
                    quantity=quantity,
                    location=row["存放位置"],
                    unit_price=unit_price,
                )
            )
    return items


def validate_inventory(file_path: str) -> List[ValidationError]:
    errors = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            for field in [
                "品名",
                "规格",
                "批次号",
                "生产日期",
                "保质期月数",
                "库存数量",
                "存放位置",
                "单价",
            ]:
                if field not in row or row[field].strip() == "":
                    errors.append(
                        ValidationError(
                            row_number=row_num,
                            field=field,
                            message=f"字段缺失值",
                        )
                    )

            if "生产日期" in row and row["生产日期"].strip():
                try:
                    datetime.strptime(row["生产日期"], "%Y-%m-%d")
                except ValueError:
                    errors.append(
                        ValidationError(
                            row_number=row_num,
                            field="生产日期",
                            message=f"日期格式错误，应为YYYY-MM-DD",
                        )
                    )

            if "保质期月数" in row and row["保质期月数"].strip():
                try:
                    val = int(row["保质期月数"])
                    if val <= 0:
                        errors.append(
                            ValidationError(
                                row_number=row_num,
                                field="保质期月数",
                                message="必须为正整数",
                            )
                        )
                except ValueError:
                    errors.append(
                        ValidationError(
                            row_number=row_num,
                            field="保质期月数",
                            message="必须为正整数",
                        )
                    )

            if "库存数量" in row and row["库存数量"].strip():
                try:
                    val = float(row["库存数量"])
                    if val < 0:
                        errors.append(
                            ValidationError(
                                row_number=row_num,
                                field="库存数量",
                                message="必须为非负数",
                            )
                        )
                except ValueError:
                    errors.append(
                        ValidationError(
                            row_number=row_num,
                            field="库存数量",
                            message="必须为数字",
                        )
                    )

            if "单价" in row and row["单价"].strip():
                try:
                    val = float(row["单价"])
                    if val < 0:
                        errors.append(
                            ValidationError(
                                row_number=row_num,
                                field="单价",
                                message="必须为非负数",
                            )
                        )
                except ValueError:
                    errors.append(
                        ValidationError(
                            row_number=row_num,
                            field="单价",
                            message="必须为数字",
                        )
                    )

    return errors


def get_alert_items(
    items: List[InventoryItemWithExpiry],
) -> List[InventoryItemWithExpiry]:
    alert_items = [
        item
        for item in items
        if item.expiry_status in (ExpiryStatus.EXPIRED, ExpiryStatus.RED_ALERT)
    ]
    alert_items.sort(key=lambda x: x.days_remaining)
    return alert_items


def get_totals(
    items: List[InventoryItemWithExpiry],
) -> Tuple[int, int, float]:
    product_count = len(set(item.name for item in items))
    batch_count = len(items)
    total_value = sum(item.total_value for item in items)
    return product_count, batch_count, total_value
