import logging
from fastapi import FastAPI, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine
import json
from dotenv import load_dotenv
from pydantic import BaseModel




class ProductCreate(BaseModel):
    price: float
    discount: float = 0.0  

load_dotenv()

# ✅ Create and configure logger
logger = logging.getLogger("cart_api")
logger.setLevel(logging.INFO)

# ❗ Remove duplicate handlers
if logger.hasHandlers():
    logger.handlers.clear()

# ✅ Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# ✅ File handler
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)

# ✅ Format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# ✅ Attach handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

#models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Custom validation error handler - logs to both terminal and app.log
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        field = error['loc'][-1]
        message = error['msg']
        error_messages.append(f"{field}: {message}")
    
    # 🔥 LOG THE ERROR to both terminal and app.log
    error_msg = "Bad Request - " + ", ".join(error_messages)
    logger.warning(f"Validation Error: {error_msg}")
    
    return JSONResponse(
        status_code=400,
        content={"message": "Bad Request", "detail": error_messages}
    )

# ✅ Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal Server Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)}
    )

@app.post("/cart")
def create_cart(data: schemas.CartCreate, db: Session = Depends(get_db)):
    logger.info(f"Request: Create cart for user_id={data.user_id}")
    response = crud.create_cart(db, data.user_id)
    logger.info("Success: Cart created successfully")
    return response

@app.post("/cart/add")
def add_item(data: schemas.AddItem, db: Session = Depends(get_db)):
    logger.info(f"Request: product_id={data.product_id}, cart_id={data.cart_id}, quantity={data.quantity}")
    response = crud.add_item(db, data)
    logger.info(f"Success: {response.get('message', 'Item added successfully')}")
    return response

@app.delete("/cart/remove/{item_id}")
def remove_item(item_id: int, db: Session = Depends(get_db)):
    logger.info(f"Request: remove item_id={item_id}")
    response = crud.remove_item(db, item_id)
    logger.info(f"Success: {response.get('message', 'Item removed successfully')}")
    return response

@app.post("/cart/checkout")
def checkout(cart_id: int, db: Session = Depends(get_db)):
    logger.info(f"Request: checkout cart_id={cart_id}")
    response = crud.checkout(db, cart_id)
    logger.info(f"Success: {response.get('message', 'Checkout successful')}")
    return response

@app.delete("/cart/{cart_id}")
def delete_cart(cart_id: int, db: Session = Depends(get_db)):
    logger.info(f"Request: delete cart_id={cart_id}")
    response = crud.delete_cart(db, cart_id)
    logger.info(f"Success: {response.get('message', 'Cart deleted successfully')}")
    return response

@app.post("/product")
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    logger.info(f"Request: create product price={product.price}, discount={product.discount}")
    db_product = models.Product(price=product.price, discount=product.discount)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    logger.info("Success: Product created successfully")
    return db_product

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    logger.info("Request: get all products")
    products = db.query(models.Product).all()
    logger.info(f"Success: Retrieved {len(products)} products")
    return products