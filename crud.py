from models import Cart, CartItem, Product
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
import json
logger = logging.getLogger(__name__)

def create_cart(db: Session, user_id: int):
    cart = Cart(user_id=user_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def add_item(db, data):

    logger.info(f"Add item API called: cart_id={data.cart_id} product_id={data.product_id} quantity={data.quantity}")

    # your existing logic...
    item = ...   # (whatever you are creating)

    response = {
        "message": "Item added successfully",
        "item_id": item.id,
        "quantity": item.quantity
    }

    # 🔥 ADD THIS (FINAL FIX)
    try:
        log_response = json.dumps(response, default=str)
    except:
        log_response = str(response)

    logger.info(f"Response Body: {log_response}")

    return response

    logger.info(f"Add item called with data: cart_id={data.cart_id} product_id={data.product_id} quantity={data.quantity}")
    
    # Check cart exists
    cart = db.query(Cart).filter(Cart.id == data.cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

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


def remove_item(db, item_id):

    logger.info(f"Remove item called for item_id: {item_id}")

    # your logic...

    response = {"message": "Item removed successfully"}

    logger.info(f"Response Body: {json.dumps(response)}")

    return response


def checkout(db, cart_id):

    logger.info(f"Checkout called for cart_id: {cart_id}")

    # your logic...

    response = {"message": "Checkout successful"}

    logger.info(f"Response Body: {json.dumps(response)}")

    return response


def delete_cart(db, cart_id):

    logger.info(f"Delete cart called for cart_id: {cart_id}")

    # your logic...

    response = {"message": "Cart deleted successfully"}

    logger.info(f"Response Body: {json.dumps(response)}")

    return response

