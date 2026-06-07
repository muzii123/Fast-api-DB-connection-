from models import Cart, CartItem, Product
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging

logger = logging.getLogger("cart_api")

def create_cart(db: Session, user_id: int):
    cart = Cart(user_id=user_id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart

def add_item(db: Session, data):
    # Check cart exists
    cart = db.query(Cart).filter(Cart.id == data.cart_id).first()
    if not cart:
        logger.warning("Error: Cart not found")
        raise HTTPException(status_code=404, detail="Cart not found")

    # Check product exists
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        logger.warning("Error: Product not found")
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
        return {"message": "Quantity updated successfully"}

    new_item = CartItem(cart_id=data.cart_id, product_id=data.product_id, quantity=data.quantity)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {"message": "Item added successfully"}

def remove_item(db: Session, item_id: int):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        logger.warning("Error: Item not found")
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Item removed successfully"}

def checkout(db: Session, cart_id: int):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        logger.warning("Error: Cart not found")
        raise HTTPException(status_code=404, detail="Cart not found")
    
    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    if not items:
        logger.warning("Error: Cart is empty")
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Clear cart items after successful checkout
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.commit()
    
    return {"message": "Checkout successful"}

def delete_cart(db: Session, cart_id: int):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        logger.warning("Error: Cart not found")
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Delete associated items first
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.delete(cart)
    db.commit()
    
    return {"message": "Cart deleted successfully"}