from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class InvoiceStatus(StrEnum):
    issued = "issued"
    paid = "paid"
    void = "void"


@dataclass(frozen=True, slots=True)
class Invoice:
    id: int
    order_id: (
        int  # reference to the orders service by id only - never a foreign key across databases
    )
    customer_id: str
    amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime
