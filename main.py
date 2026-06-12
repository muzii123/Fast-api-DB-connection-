import logging
from fastapi import FastAPI, Depends, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models, schemas, crud
from database import SessionLocal, engine
from auth import create_access_token, get_current_user
from models import User
from dotenv import load_dotenv

load_dotenv()

# ── Logger Setup ──────────────────────────────────────────────────────────────
logger = logging.getLogger("cart_api")
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Cart API",
    description="""
## Cart API with JWT Authentication

### How to use:
1. **Register** → `POST /auth/register` — create your account
2. **Login** → `POST /auth/login` — get your JWT token
3. **Authorize** → click the 🔒 **Authorize** button at the top right of this page
4. Enter: `Bearer <your_token>` — then click Authorize
5. Now all protected endpoints will work with your token

All cart, product, and user endpoints require a valid JWT token.
""",
    version="2.0.0",
    # This adds the 🔒 Authorize button in Swagger UI
    swagger_ui_parameters={"persistAuthorization": True},
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        field = error["loc"][-1]
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    logger.warning(f"Validation Error: {', '.join(error_messages)}")
    return JSONResponse(
        status_code=400,
        content={"message": "Bad Request", "detail": error_messages},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal Server Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )


# ── Public Endpoints (no token needed) ───────────────────────────────────────

@app.get("/", tags=["Health"])
def read_root():
    """Public health check — no token required."""
    return {"message": "Cart API is running", "docs": "/docs"}


# ── Auth Endpoints (PUBLIC — these give you the token) ────────────────────────

@app.post("/auth/register", summary="Register", tags=["Auth"], status_code=201)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """
    **Register a new user account.**

    - Provide email, password, contact number, and address
    - Password is stored as a secure bcrypt hash — never plain text
    - Email must be unique
    """
    logger.info(f"Register → email={data.email}")
    user = crud.register_user(db, data)
    logger.info(f"Registered → id={user.id}")
    return {
        "message": "Registration successful. Please login to get your token.",
        "user_id": user.id,
        "email": user.email,
    }


@app.post("/auth/login", summary="Login", tags=["Auth"], response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    **Login with JSON body — use this in Postman.**

    - Send `{"email": "...", "password": "..."}`
    - Returns JWT access token valid for 60 minutes
    """
    logger.info(f"Login attempt → email={data.email}")
    user = crud.authenticate_user(db, data.email, data.password)
    token = create_access_token(data={"sub": user.email})
    logger.info(f"Login success → user_id={user.id}")
    return schemas.TokenResponse(access_token=token)


@app.post("/auth/token", summary="Login for Swagger UI", tags=["Auth"], response_model=schemas.TokenResponse)
def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    **Login via form — used automatically by the 🔒 Authorize button in Swagger UI.**

    - In the Authorize dialog: type your email in the `username` field
    - Type your password in the `password` field
    - Click Authorize — all endpoints will work automatically
    """
    logger.info(f"Swagger login → username={form_data.username}")
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    token = create_access_token(data={"sub": user.email})
    logger.info(f"Swagger login success → user_id={user.id}")
    return schemas.TokenResponse(access_token=token)

# ── Protected Endpoints (JWT token required for all below) ────────────────────
# Every endpoint below has:  current_user: User = Depends(get_current_user)
# This means FastAPI checks the token BEFORE running the endpoint function.


# ── User Endpoints ────────────────────────────────────────────────────────────

@app.get("/users", summary="Get All Users", tags=["Users"])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — returns all users. Requires valid JWT token."""
    logger.info(f"Get users → requested by {current_user.email}")
    users = db.query(models.User).all()
    return users


# ── Product Endpoints ─────────────────────────────────────────────────────────

@app.post("/product", summary="Create Product", tags=["Products"], status_code=201)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — create a new product. Requires valid JWT token."""
    logger.info(f"Create product → price={product.price} by {current_user.email}")
    db_product = models.Product(price=product.price, discount=product.discount)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products", summary="Get Products", tags=["Products"])
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — get all products. Requires valid JWT token."""
    products = db.query(models.Product).all()
    return products


# ── Cart Endpoints ────────────────────────────────────────────────────────────

@app.post("/cart", summary="Create Cart", tags=["Cart"])
def create_cart(
    data: schemas.CartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — create a cart for a user. Requires valid JWT token."""
    logger.info(f"Create cart → user_id={data.user_id} by {current_user.email}")
    response = crud.create_cart(db, data.user_id)
    return response


@app.post("/cart/add", summary="Add Item", tags=["Cart"])
def add_item(
    data: schemas.AddItem,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — add a product to a cart. Requires valid JWT token."""
    logger.info(f"Add item → cart={data.cart_id} product={data.product_id} by {current_user.email}")
    return crud.add_item(db, data)


@app.delete("/cart/remove/{item_id}", summary="Remove Item", tags=["Cart"])
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — remove an item from a cart. Requires valid JWT token."""
    logger.info(f"Remove item → item_id={item_id} by {current_user.email}")
    return crud.remove_item(db, item_id)


@app.post("/cart/checkout", summary="Checkout", tags=["Cart"])
def checkout(
    cart_id: int = Query(..., gt=0, description="Cart ID to checkout"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — checkout a cart. Requires valid JWT token."""
    logger.info(f"Checkout → cart_id={cart_id} by {current_user.email}")
    return crud.checkout(db, cart_id)


@app.delete("/cart/{cart_id}", summary="Delete Cart", tags=["Cart"])
def delete_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — delete a cart. Requires valid JWT token."""
    logger.info(f"Delete cart → cart_id={cart_id} by {current_user.email}")
    return crud.delete_cart(db, cart_id)


@app.get("/cart/{cart_id}", summary="Get Cart", tags=["Cart"])
def get_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """🔒 Protected — get cart details. Requires valid JWT token."""
    logger.info(f"Get cart → cart_id={cart_id} by {current_user.email}")
    return crud.get_cart(db, cart_id)
