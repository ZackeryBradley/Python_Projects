import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
db_path = os.path.join(BASE_DIR, "ecommerce.db")

print("Creating DB at:", db_path)

conn = sqlite3.connect(db_path)


# Load CSV files
customers = pd.read_csv("customers.csv")
orders = pd.read_csv("orders.csv")
items = pd.read_csv("order_items.csv")
products = pd.read_csv("products.csv")
payments = pd.read_csv("payments.csv")
reviews = pd.read_csv("order_reviews.csv")

# Write to SQL tables
customers.to_sql("customers", conn, if_exists="replace", index=False)
orders.to_sql("orders", conn, if_exists="replace", index=False)
items.to_sql("order_items", conn, if_exists="replace", index=False)
products.to_sql("products", conn, if_exists="replace", index=False)
payments.to_sql("payments", conn, if_exists="replace", index=False)
reviews.to_sql("order_reviews", conn, if_exists="replace", index=False)

print("✅ Database created successfully!")