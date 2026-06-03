from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    contact_no = Column(String)
    address = Column(String)

class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    status = Column(String, default="active")
    coupon = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    price = Column(Integer)
    discount = Column(Integer)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    selected = Column(Boolean, default=True)