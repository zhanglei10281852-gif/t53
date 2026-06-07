from dataclasses import dataclass
from datetime import date
from enum import Enum


class ExpiryStatus(str, Enum):
    EXPIRED = "已过期"
    RED_ALERT = "近效期红色预警"
    YELLOW_ALERT = "近效期黄色提醒"
    NORMAL = "正常"

    @classmethod
    def from_days_remaining(cls, days_remaining: int) -> "ExpiryStatus":
        if days_remaining < 0:
            return cls.EXPIRED
        elif days_remaining <= 90:
            return cls.RED_ALERT
        elif days_remaining <= 180:
            return cls.YELLOW_ALERT
        else:
            return cls.NORMAL

    @property
    def priority(self) -> int:
        priority_map = {
            ExpiryStatus.EXPIRED: 0,
            ExpiryStatus.RED_ALERT: 1,
            ExpiryStatus.YELLOW_ALERT: 2,
            ExpiryStatus.NORMAL: 3,
        }
        return priority_map[self]


@dataclass
class InventoryItem:
    name: str
    specification: str
    batch_number: str
    production_date: date
    shelf_life_months: int
    quantity: float
    location: str
    unit_price: float

    @property
    def total_value(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class InventoryItemWithExpiry(InventoryItem):
    expiry_date: date
    days_remaining: int
    expiry_status: ExpiryStatus


@dataclass
class ProductSummary:
    name: str
    total_quantity: float
    total_value: float
    batch_count: int
    earliest_expiry_date: date
    earliest_expiry_status: ExpiryStatus
    is_out_of_stock: bool = False


@dataclass
class ValidationError:
    row_number: int
    field: str
    message: str
