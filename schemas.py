from pydantic import BaseModel, Field
from typing import Optional


# ── Auth Schemas ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Used for POST /auth/register — creates account with password"""
    email: str = Field(..., description="User email — must be unique")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    contact_no: str = Field(..., description="Contact phone number")
    address: str = Field(..., description="Delivery address")


class LoginRequest(BaseModel):
    """Used for POST /auth/login — returns JWT token"""
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Your password")


class TokenResponse(BaseModel):
    """Returned after successful login"""
    access_token: str
    token_type: str = "bearer"
    message: str = "Login successful"


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Legacy user creation without password (kept for compatibility)"""
    email: str = Field(..., description="User email address")
    contact_no: str = Field(..., description="Contact phone number")
    address: str = Field(..., description="Delivery address")


# ── Cart Schemas ──────────────────────────────────────────────────────────────

class CartCreate(BaseModel):
    user_id: int = Field(gt=0, description="User ID must be positive")


class AddItem(BaseModel):
    cart_id: int = Field(gt=0, description="Cart ID must be positive")
    product_id: int = Field(gt=0, description="Product ID must be positive")
    quantity: int = Field(gt=0, le=1000, description="Quantity must be between 1 and 1000")


class RemoveItem(BaseModel):
    item_id: int = Field(gt=0, description="Item ID must be positive")


# ── Product Schemas ───────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    price: int = Field(gt=0, description="Price must be positive")
    discount: int = Field(ge=0, le=100, description="Discount must be between 0 and 100")
