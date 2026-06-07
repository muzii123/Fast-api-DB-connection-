from pydantic import BaseModel, Field

class CartCreate(BaseModel):
    user_id: int = Field(gt=0, description="User ID must be positive")

class AddItem(BaseModel):
    cart_id: int = Field(gt=0, description="Cart ID must be positive")
    product_id: int = Field(gt=0, description="Product ID must be positive")
    quantity: int = Field(gt=0, le=1000, description="Quantity must be between 1 and 1000")

class RemoveItem(BaseModel):
    item_id: int = Field(gt=0, description="Item ID must be positive")

class ProductCreate(BaseModel):
    price: int = Field(gt=0, description="Price must be positive")
    discount: int = Field(ge=0, le=100, description="Discount must be between 0 and 100")