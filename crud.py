from models import Cart, CartItem, Product
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
logger = logging.getLogger(__name__)

def create_cart(db: Session, user_id: int):
    cart = Cart(user_id=user_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def add_item(db, data):

    # ✅ get product first
    product = db.query(Product).filter(Product.id == data.product_id).first()

    # ✅ THEN check
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check product exists
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check existing item
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == data.cart_id,
        CartItem.product_id == data.product_id
    ).first()

    if existing_item:
        existing_item.quantity = (existing_item.quantity or 0) + data.quantity
        db.commit()
        db.refresh(existing_item)
        return {"message": "Quantity updated", "item": existing_item}

    new_item = CartItem(**data.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {"message": "Item added", "item": new_item}


def remove_item(db: Session, item_id: int):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return {"message": "Item removed successfully"}


def checkout(db: Session, cart_id: int):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()

    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    cart.status = "checked_out"
    db.commit()

    return {"message": "Checkout successful"}


def delete_cart(db: Session, cart_id: int):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    db.delete(cart)
    db.commit()

    return {"message": "Cart deleted successfully"}

