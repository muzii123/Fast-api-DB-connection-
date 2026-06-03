

import logging

# ✅ Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ❗ Remove duplicate handlers (IMPORTANT)
if logger.hasHandlers():
    logger.handlers.clear()

# ✅ Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# ✅ File handler
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)

# ✅ Format
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# ✅ Attach handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)


from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models, schemas, crud
from exceptions import NotFoundException
from database import SessionLocal, engine
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import JSONResponse

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)}
    )

@app.post("/cart")
def create_cart(data: schemas.CartCreate, db: Session = Depends(get_db)):
    logger.info(f"Create cart for user: {data.user_id}")
    return crud.create_cart(db, data.user_id)

@app.post("/cart/add")
def add_item(data: schemas.AddItem, db: Session = Depends(get_db)):

    logger.info(f"Request: Add item called with product_id={data.product_id}")
    response = crud.add_item(db, data)   
    logger.info(f"Response: {response}")  
    return response

@app.delete("/cart/remove/{item_id}")
def remove_item(item_id: int, db: Session = Depends(get_db)):

    logger.info(f"Request: Remove item_id={item_id}")

    response = crud.remove_item(db, item_id)

    logger.info(f"Response: {response}")

    return response


@app.post("/cart/checkout")
def checkout(cart_id: int, db: Session = Depends(get_db)):
    logger.info(f"Request: Checkout cart_id={cart_id}")
    response = crud.checkout(db, cart_id)
    logger.info(f"Response: {response}")
    return response


@app.delete("/cart/{cart_id}")
def delete_cart(cart_id: int, db: Session = Depends(get_db)):
     logger.info(f"Request: Checkout cart_id={cart_id}")
     response = crud.checkout(db, cart_id)
     logger.info(f"Response: {response}")
     return response


@app.post("/product")
def create_product(price: int, discount: int = 0, db: Session = Depends(get_db)):
    product = models.Product(price=price, discount=discount)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error occurred: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )