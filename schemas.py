from pydantic import BaseModel, Field

class CartCreate(BaseModel):
    user_id: int

class AddItem(BaseModel):
    cart_id: int
    product_id: int
    quantity: int = Field(gt=0)  # must be > 0

class RemoveItem(BaseModel):
    item_id: int