from models import Cart, CartItem, Product, User
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging

logger = logging.getLogger("cart_api")


# ─── Auth ──────────────────────────────────────────────────────────────────────

def register_user(db: Session, data):
    """
    Register a new user with hashed password.
    Raises 400 if email already exists.
    """
    from auth import hash_password

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        contact_no=data.contact_no,
        address=data.address,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str):
    """
    Verify email + password.
    Returns the User if valid, raises 401 if not.
    """
    from auth import verify_password

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user


# ─── User ──────────────────────────────────────────────────────────────────────

def create_user(db: Session, data):
    user = User(email=data.email, contact_no=data.contact_no, address=data.address)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── Cart ──────────────────────────────────────────────────────────────────────

def create_cart(db: Session, user_id: int):
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"Error: User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    cart = Cart(user_id=user_id, status="active")
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def get_cart(db: Session, cart_id: int):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        logger.warning(f"Error: Cart {cart_id} not found")
        raise HTTPException(status_code=404, detail="Cart not found")

    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    return {
        "cart_id": cart.id,
        "user_id": cart.user_id,
        "status": cart.status,
        "coupon": cart.coupon,
        "items": [
            {
                "item_id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "selected": item.selected,
            }
            for item in items
        ],
    }


def add_item(db: Session, data):
    # Check cart exists
    cart = db.query(Cart).filter(Cart.id == data.cart_id).first()
    if not cart:
        logger.warning(f"Error: Cart {data.cart_id} not found")
        raise HTTPException(status_code=404, detail="Cart not found")

    # Check product exists
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        logger.warning(f"Error: Product {data.product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if item already in cart — update quantity
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == data.cart_id,
        CartItem.product_id == data.product_id,
    ).first()

    if existing_item:
        existing_item.quantity = (existing_item.quantity or 0) + data.quantity
        db.commit()
        db.refresh(existing_item)
        return {"message": "Quantity updated successfully", "item_id": existing_item.id}

    new_item = CartItem(
        cart_id=data.cart_id,
        product_id=data.product_id,
        quantity=data.quantity,
        selected=True,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {"message": "Item added successfully", "item_id": new_item.id}


def remove_item(db: Session, item_id: int):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        logger.warning(f"Error: Item {item_id} not found")
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item removed successfully"}


def checkout(db: Session, cart_id: int):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        logger.warning(f"Error: Cart {cart_id} not found")
        raise HTTPException(status_code=404, detail="Cart not found")

    if cart.status == "checked_out":
        raise HTTPException(status_code=400, detail="Cart already checked out")

    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    if not items:
        logger.warning(f"Error: Cart {cart_id} is empty")
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Mark cart as checked out and clear items
    cart.status = "checked_out"
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.commit()

    return {"message": "Checkout successful", "cart_id": cart_id}


def delete_cart(db: Session, cart_id: int):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        logger.warning(f"Error: Cart {cart_id} not found")
        raise HTTPException(status_code=404, detail="Cart not found")

    # Delete associated items first, then the cart
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.delete(cart)
    db.commit()

    return {"message": "Cart deleted successfully"}
