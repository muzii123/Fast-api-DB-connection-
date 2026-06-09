"""
Bulk Data Seeding Script
Inserts millions of records using buffering/batching for optimal performance
"""

from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Product, Cart, CartItem
from tqdm import tqdm
import random
import time

# Initialize Faker
fake = Faker()

# Configuration
BATCH_SIZE = 10000  # Buffer size - records inserted at once
TOTAL_PRODUCTS = 100000  # 100k products
TOTAL_CARTS = 50000  # 50k carts
TOTAL_CART_ITEMS = 200000  # 200k cart items

def seed_products(count: int):
    """Insert products in batches using buffering"""
    print(f"\n📦 Inserting {count:,} products with buffer size {BATCH_SIZE:,}...")
    
    batch = []
    start_time = time.time()
    
    for i in tqdm(range(count), desc="Products"):
        product = {
            "price": random.randint(10, 1000),
            "discount": random.choice([0, 5, 10, 15, 20, 25, 30])
        }
        batch.append(product)
        
        # Flush buffer when it reaches BATCH_SIZE
        if len(batch) >= BATCH_SIZE:
            with Session(engine) as db:
                db.bulk_insert_mappings(Product, batch)
                db.commit()
            batch = []  # Clear buffer
    
    # Insert remaining records
    if batch:
        with Session(engine) as db:
            db.bulk_insert_mappings(Product, batch)
            db.commit()
    
    elapsed = time.time() - start_time
    print(f"✅ Inserted {count:,} products in {elapsed:.2f} seconds ({count/elapsed:.0f} records/sec)")

def seed_carts(count: int):
    """Insert carts in batches using buffering"""
    print(f"\n🛒 Inserting {count:,} carts with buffer size {BATCH_SIZE:,}...")
    
    batch = []
    start_time = time.time()
    
    for i in tqdm(range(count), desc="Carts"):
        cart = {
            "user_id": random.randint(1, 100000)  # Random user IDs
        }
        batch.append(cart)
        
        if len(batch) >= BATCH_SIZE:
            with Session(engine) as db:
                db.bulk_insert_mappings(Cart, batch)
                db.commit()
            batch = []
    
    if batch:
        with Session(engine) as db:
            db.bulk_insert_mappings(Cart, batch)
            db.commit()
    
    elapsed = time.time() - start_time
    print(f"✅ Inserted {count:,} carts in {elapsed:.2f} seconds ({count/elapsed:.0f} records/sec)")

def seed_cart_items(count: int):
    """Insert cart items in batches using buffering"""
    print(f"\n🛍️ Inserting {count:,} cart items with buffer size {BATCH_SIZE:,}...")
    
    # Get existing cart and product IDs
    with Session(engine) as db:
        cart_ids = [row[0] for row in db.query(Cart.id).all()]
        product_ids = [row[0] for row in db.query(Product.id).all()]
    
    if not cart_ids or not product_ids:
        print("❌ No carts or products found. Run seed_products and seed_carts first!")
        return
    
    batch = []
    start_time = time.time()
    
    for i in tqdm(range(count), desc="Cart Items"):
        cart_item = {
            "cart_id": random.choice(cart_ids),
            "product_id": random.choice(product_ids),
            "quantity": random.randint(1, 10)
        }
        batch.append(cart_item)
        
        if len(batch) >= BATCH_SIZE:
            with Session(engine) as db:
                db.bulk_insert_mappings(CartItem, batch)
                db.commit()
            batch = []
    
    if batch:
        with Session(engine) as db:
            db.bulk_insert_mappings(CartItem, batch)
            db.commit()
    
    elapsed = time.time() - start_time
    print(f"✅ Inserted {count:,} cart items in {elapsed:.2f} seconds ({count/elapsed:.0f} records/sec)")

def get_stats():
    """Show current database statistics"""
    with Session(engine) as db:
        products = db.query(Product).count()
        carts = db.query(Cart).count()
        cart_items = db.query(CartItem).count()
    
    print("\n" + "="*60)
    print("📊 DATABASE STATISTICS")
    print("="*60)
    print(f"📦 Products:    {products:,}")
    print(f"🛒 Carts:       {carts:,}")
    print(f"🛍️ Cart Items:  {cart_items:,}")
    print("="*60 + "\n")

def main():
    """Main seeding function"""
    print("="*60)
    print("🚀 BULK DATA SEEDING WITH BUFFERING")
    print("="*60)
    print(f"Configuration:")
    print(f"  • Batch Size: {BATCH_SIZE:,}")
    print(f"  • Products:   {TOTAL_PRODUCTS:,}")
    print(f"  • Carts:      {TOTAL_CARTS:,}")
    print(f"  • Cart Items: {TOTAL_CART_ITEMS:,}")
    print("="*60)
    
    # Show initial stats
    get_stats()
    
    # Confirm before proceeding
    print("⚠️  This will insert millions of records. Continue? (y/n): ", end="")
    # For automated runs, skip confirmation
    # response = input().lower()
    # if response != 'y':
    #     print("❌ Aborted.")
    #     return
    
    start_time = time.time()
    
    # Seed data
    seed_products(TOTAL_PRODUCTS)
    seed_carts(TOTAL_CARTS)
    seed_cart_items(TOTAL_CART_ITEMS)
    
    # Show final stats
    total_time = time.time() - start_time
    total_records = TOTAL_PRODUCTS + TOTAL_CARTS + TOTAL_CART_ITEMS
    
    print("\n" + "="*60)
    print("✅ SEEDING COMPLETE!")
    print("="*60)
    print(f"⏱️  Total Time:    {total_time/60:.2f} minutes")
    print(f"📊 Total Records:  {total_records:,}")
    print(f"⚡ Speed:          {total_records/total_time:.0f} records/second")
    print("="*60)
    
    get_stats()

if __name__ == "__main__":
    main()