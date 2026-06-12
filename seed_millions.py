"""
seed_millions.py
────────────────────────────────────────────────────────────────────────────────
Bulk data seeding script — inserts millions of records into cart_db
using batched inserts for high performance.

Tables seeded (in order to satisfy FK constraints):
  1. users       → 100 000 rows
  2. products    → 100 000 rows
  3. carts       → 500 000 rows  (each references a real user)
  4. cart_items  → 1 000 000 rows (each references a real cart + product)

Total: ~1.7 million records

Run:
  python seed_millions.py
────────────────────────────────────────────────────────────────────────────────
"""

import random
import time

from faker import Faker
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from tqdm import tqdm

# Import the SAME engine & session used by the FastAPI app
# This guarantees we write into cart_db — not a new database
from database import engine, SessionLocal
from models import User, Product, Cart, CartItem

fake = Faker()

# ── Configuration ──────────────────────────────────────────────────────────────
BATCH_SIZE = 5_000       # rows flushed per DB round-trip

TOTAL_USERS = 100_000
TOTAL_PRODUCTS = 100_000
TOTAL_CARTS = 500_000
TOTAL_CART_ITEMS = 1_000_000
# ──────────────────────────────────────────────────────────────────────────────


def _bulk_insert(model, rows: list[dict]) -> None:
    """Insert a list of dicts into the given model's table (SQLAlchemy 2.x safe)."""
    with engine.begin() as conn:
        conn.execute(model.__table__.insert(), rows)


def seed_users(count: int) -> list[int]:
    """Seed users and return their generated IDs."""
    print(f"\n👤  Seeding {count:,} users  (batch={BATCH_SIZE:,}) …")
    start = time.time()
    batch: list[dict] = []

    for _ in tqdm(range(count), desc="Users", unit="row"):
        batch.append(
            {
                "email": fake.unique.email(),
                "contact_no": fake.numerify("03#########"),
                "address": fake.address().replace("\n", ", "),
            }
        )
        if len(batch) >= BATCH_SIZE:
            _bulk_insert(User, batch)
            batch.clear()

    if batch:
        _bulk_insert(User, batch)

    elapsed = time.time() - start
    print(f"   ✅ {count:,} users  — {elapsed:.1f}s  ({count/elapsed:,.0f} rows/s)")

    # Fetch the IDs we just inserted so carts can reference them
    with SessionLocal() as db:
        ids = [r[0] for r in db.execute(text("SELECT id FROM users")).fetchall()]
    return ids


def seed_products(count: int) -> list[int]:
    """Seed products and return their IDs."""
    print(f"\n📦  Seeding {count:,} products  (batch={BATCH_SIZE:,}) …")
    start = time.time()
    batch: list[dict] = []

    discounts = [0, 5, 10, 15, 20, 25, 30, 40, 50]

    for _ in tqdm(range(count), desc="Products", unit="row"):
        batch.append(
            {
                "price": random.randint(10, 10_000),
                "discount": random.choice(discounts),
            }
        )
        if len(batch) >= BATCH_SIZE:
            _bulk_insert(Product, batch)
            batch.clear()

    if batch:
        _bulk_insert(Product, batch)

    elapsed = time.time() - start
    print(f"   ✅ {count:,} products — {elapsed:.1f}s  ({count/elapsed:,.0f} rows/s)")

    with SessionLocal() as db:
        ids = [r[0] for r in db.execute(text("SELECT id FROM products")).fetchall()]
    return ids


def seed_carts(count: int, user_ids: list[int]) -> list[int]:
    """Seed carts referencing real user IDs."""
    print(f"\n🛒  Seeding {count:,} carts  (batch={BATCH_SIZE:,}) …")
    start = time.time()
    batch: list[dict] = []
    statuses = ["active", "active", "active", "checked_out"]  # 75% active

    for _ in tqdm(range(count), desc="Carts", unit="row"):
        batch.append(
            {
                "user_id": random.choice(user_ids),
                "status": random.choice(statuses),
                "coupon": fake.bothify("DEAL-??##") if random.random() < 0.2 else None,
            }
        )
        if len(batch) >= BATCH_SIZE:
            _bulk_insert(Cart, batch)
            batch.clear()

    if batch:
        _bulk_insert(Cart, batch)

    elapsed = time.time() - start
    print(f"   ✅ {count:,} carts  — {elapsed:.1f}s  ({count/elapsed:,.0f} rows/s)")

    with SessionLocal() as db:
        ids = [r[0] for r in db.execute(text("SELECT id FROM carts")).fetchall()]
    return ids


def seed_cart_items(count: int, cart_ids: list[int], product_ids: list[int]) -> None:
    """Seed cart_items referencing real carts and products."""
    print(f"\n🛍️   Seeding {count:,} cart items  (batch={BATCH_SIZE:,}) …")
    start = time.time()
    batch: list[dict] = []

    for _ in tqdm(range(count), desc="Cart Items", unit="row"):
        batch.append(
            {
                "cart_id": random.choice(cart_ids),
                "product_id": random.choice(product_ids),
                "quantity": random.randint(1, 20),
                "selected": random.choice([True, True, True, False]),  # 75% selected
            }
        )
        if len(batch) >= BATCH_SIZE:
            _bulk_insert(CartItem, batch)
            batch.clear()

    if batch:
        _bulk_insert(CartItem, batch)

    elapsed = time.time() - start
    print(f"   ✅ {count:,} cart items — {elapsed:.1f}s  ({count/elapsed:,.0f} rows/s)")


def print_stats() -> None:
    """Print current row counts from every table."""
    with SessionLocal() as db:
        users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        products = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
        carts = db.execute(text("SELECT COUNT(*) FROM carts")).scalar()
        items = db.execute(text("SELECT COUNT(*) FROM cart_items")).scalar()

    print("\n" + "=" * 55)
    print("  📊  DATABASE STATISTICS  —  cart_db")
    print("=" * 55)
    print(f"  👤  Users      : {users:>12,}")
    print(f"  📦  Products   : {products:>12,}")
    print(f"  🛒  Carts      : {carts:>12,}")
    print(f"  🛍️   Cart Items : {items:>12,}")
    print("=" * 55)


def main() -> None:
    print("=" * 55)
    print("  🚀  BULK SEEDER — cart_db")
    print("=" * 55)
    print(f"  Batch size  : {BATCH_SIZE:,}")
    print(f"  Users       : {TOTAL_USERS:,}")
    print(f"  Products    : {TOTAL_PRODUCTS:,}")
    print(f"  Carts       : {TOTAL_CARTS:,}")
    print(f"  Cart Items  : {TOTAL_CART_ITEMS:,}")
    print(f"  Total rows  : {TOTAL_USERS + TOTAL_PRODUCTS + TOTAL_CARTS + TOTAL_CART_ITEMS:,}")
    print("=" * 55)

    # Show what's already in the DB before we start
    print_stats()

    answer = input("\n⚠️  Insert all records into cart_db? (y/n): ").strip().lower()
    if answer != "y":
        print("❌ Aborted. No data was inserted.")
        return

    grand_start = time.time()

    # ── Seed in FK-safe order ──────────────────────────────────────────────────
    user_ids = seed_users(TOTAL_USERS)
    product_ids = seed_products(TOTAL_PRODUCTS)
    cart_ids = seed_carts(TOTAL_CARTS, user_ids)
    seed_cart_items(TOTAL_CART_ITEMS, cart_ids, product_ids)
    # ──────────────────────────────────────────────────────────────────────────

    grand_elapsed = time.time() - grand_start
    total_rows = TOTAL_USERS + TOTAL_PRODUCTS + TOTAL_CARTS + TOTAL_CART_ITEMS

    print("\n" + "=" * 55)
    print("  ✅  SEEDING COMPLETE!")
    print("=" * 55)
    print(f"  ⏱️   Total time : {grand_elapsed / 60:.2f} min")
    print(f"  📊  Total rows : {total_rows:,}")
    print(f"  ⚡  Speed      : {total_rows / grand_elapsed:,.0f} rows/s")
    print("=" * 55)

    # Show final counts
    print_stats()


if __name__ == "__main__":
    main()
