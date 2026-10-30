"""Audit trail: one line per order with its revenue (audit_2025.csv)."""

import os

import pandas as pd

DATA = os.environ.get("DATA", os.path.expanduser("~/data/sales_2025.csv"))
OUT = os.environ.get("OUT", os.path.expanduser("~/data/out"))
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "audit_2025.csv")

orders = pd.read_csv(DATA, usecols=["order_id", "region", "quantity", "unit_price"])
orders["revenue"] = orders["quantity"] * orders["unit_price"]

open(path, "w").close()
with open(path, "w") as f:
    for order in orders.itertuples():
        f.write(f"{order.order_id},{order.region},{order.revenue:.2f}\n")
  # now instead of opening the file, writing and close the file for every single line,
  # we keep the file open, write write write until the buffer is full, it is then
  # flushed by the OS and writen to output file (not directly after flushing though;
  # may take some time.
print(f"audit: {len(orders):,} lines written")
