

import pytest



@pytest.fixture
def cart(client):
    """Creates a cart, returns its ID."""
    res = client.post("/cart", json={"user_id": 1})
    print("CART RESPONSE:", res.json())  
    return res.json()["id"]  


@pytest.fixture
def product(client): 
    """Creates a product, returns its ID."""
   
    res = client.post("/product?price=100&discount=10")
    print("PRODUCT RESPONSE:", res.json())
    return res.json()["id"]   




def test_create_cart_success(client):
    """TC-01 ✅ Valid user_id creates cart."""
    res = client.post("/cart", json={"user_id": 1})
    assert res.status_code in (200, 201)

def test_create_cart_has_id_in_response(client):
    """TC-02 ✅ Response must contain an id."""
    res = client.post("/cart", json={"user_id": 1})
    data = res.json()
    assert "id" in data  

def test_create_cart_missing_user_id(client):
    """TC-03 ❌ No user_id → 422."""
    res = client.post("/cart", json={})
    assert res.status_code == 422

def test_create_cart_no_body(client):
    """TC-04 ❌ No body at all → 422."""
    res = client.post("/cart")
    assert res.status_code == 422




def test_add_item_success(client, cart, product):
    """TC-05 ✅ Add valid product to valid cart."""
    res = client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": 2
    })
    assert res.status_code in (200, 201)

def test_add_item_invalid_cart(client, product):
    """TC-06 ❌ Non-existent cart → 404."""
    res = client.post("/cart/add", json={
        "cart_id": 9999,
        "product_id": product,
        "quantity": 1
    })
    assert res.status_code == 404

def test_add_item_missing_quantity(client, cart, product):
    """TC-07 ❌ No quantity field → 422."""
    res = client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product
    })
    assert res.status_code == 422

def test_add_item_zero_quantity(client, cart, product):
    """TC-08 ❌ Quantity of 0 → 400 or 422."""
    res = client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": 0
    })
    assert res.status_code in (400, 422)

def test_add_item_negative_quantity(client, cart, product):
    """TC-09 ❌ Negative quantity → 400 or 422."""
    res = client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": -3
    })
    assert res.status_code in (400, 422)

def test_add_item_invalid_product(client, cart):
    """TC-10 ❌ Non-existent product → 404."""
    res = client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": 9999,
        "quantity": 1
    })
    assert res.status_code == 404




def test_remove_item_success(client, cart, product):
    """TC-11 ✅ Remove an item that was added."""
    add = client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": 1
    })
    item_id = add.json()["id"]   
    res = client.delete(f"/cart/remove/{item_id}")
    assert res.status_code == 200

def test_remove_nonexistent_item(client):
    """TC-12 ❌ item_id that doesn't exist → 404."""
    res = client.delete("/cart/remove/99999")
    assert res.status_code == 404

def test_remove_item_twice(client, cart, product):
    """TC-13 ❌ Remove same item twice → 404 on second."""
    add = client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": 1
    })
    item_id = add.json()["id"]
    client.delete(f"/cart/remove/{item_id}")         
    res = client.delete(f"/cart/remove/{item_id}")   
    assert res.status_code == 404

def test_remove_item_string_id(client):
    """TC-14 ❌ String instead of int in URL → 422."""
    res = client.delete("/cart/remove/abc")
    assert res.status_code == 422




def test_checkout_success(client, cart, product):
    """TC-15 ✅ Checkout cart with items."""
    client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": 1
    })

    res = client.post(f"/cart/checkout?cart_id={cart}")
    assert res.status_code == 200

def test_checkout_empty_cart(client, cart):
    """TC-16 ❌ Empty cart checkout → 400."""
    res = client.post(f"/cart/checkout?cart_id={cart}")
    assert res.status_code == 400

def test_checkout_invalid_cart(client):
    """TC-17 ❌ Non-existent cart → 404."""
    res = client.post("/cart/checkout?cart_id=99999")
    assert res.status_code == 404

def test_checkout_missing_cart_id(client):
    """TC-18 ❌ No cart_id at all → 422."""
    res = client.post("/cart/checkout")
    assert res.status_code == 422

def test_checkout_twice(client, cart, product):
    """TC-19 ❌ Double checkout → 400 or 409."""
    client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": 1
    })
    client.post(f"/cart/checkout?cart_id={cart}")         
    res = client.post(f"/cart/checkout?cart_id={cart}")   
    assert res.status_code in (400, 409)

def test_checkout_string_cart_id(client):
    """TC-20 ❌ String cart_id → 422."""
    res = client.post("/cart/checkout?cart_id=abc")
    assert res.status_code == 422



def test_delete_cart_success(client, cart):
    """TC-21 ✅ Delete existing cart."""
    res = client.delete(f"/cart/{cart}")
    assert res.status_code == 200

def test_delete_cart_with_items(client, cart, product):
    """TC-22 ✅ Delete cart that has items."""
    client.post("/cart/add", json={
        "cart_id": cart,
        "product_id": product,
        "quantity": 2
    })
    res = client.delete(f"/cart/{cart}")
    assert res.status_code == 200

def test_delete_nonexistent_cart(client):
    """TC-23 ❌ Non-existent cart → 404."""
    res = client.delete("/cart/99999")
    assert res.status_code == 404

def test_delete_cart_twice(client, cart):
    """TC-24 ❌ Delete same cart twice → 404 second time."""
    client.delete(f"/cart/{cart}")          
    res = client.delete(f"/cart/{cart}")    
    assert res.status_code == 404

def test_delete_cart_string_id(client):
    """TC-25 ❌ String cart_id in URL → 422."""
    res = client.delete("/cart/abc")
    assert res.status_code == 422




def test_create_product_success(client):
    """TC-26 ✅ Valid price creates product."""
    res = client.post("/product?price=500")
    assert res.status_code in (200, 201)

def test_create_product_with_discount(client):
    """TC-27 ✅ Price + discount both work."""
    res = client.post("/product?price=1000&discount=100")
    assert res.status_code in (200, 201)

def test_create_product_zero_discount(client):
    """TC-28 ✅ discount defaults to 0 if not sent."""
    res = client.post("/product?price=200")
    assert res.status_code in (200, 201)

def test_create_product_has_id(client):
    """TC-29 ✅ Response has an id field."""
    res = client.post("/product?price=300")
    assert "id" in res.json()   # adjust key

def test_create_product_missing_price(client):
    """TC-30 ❌ No price → 422."""
    res = client.post("/product")
    assert res.status_code == 422

def test_create_product_negative_price(client):
    """TC-31 ❌ Negative price → 400 or 422."""
    res = client.post("/product?price=-50")
    assert res.status_code in (400, 422)

def test_create_product_string_price(client):
    """TC-32 ❌ String price → 422."""
    res = client.post("/product?price=abc")
    assert res.status_code == 422

def test_create_product_negative_discount(client):
    """TC-33 ❌ Negative discount → 400 or 422."""
    res = client.post("/product?price=100&discount=-10")
    assert res.status_code in (400, 422)

def test_create_product_discount_exceeds_price(client):
    """TC-34 ❌ Discount larger than price → 400."""
    res = client.post("/product?price=50&discount=100")
    assert res.status_code == 400




def test_get_products_empty(client):
    """TC-35 ✅ Empty DB returns empty list."""
    res = client.get("/products")
    assert res.status_code == 200
    assert res.json() == []

def test_get_products_after_create(client):
    """TC-36 ✅ Returns list after product is created."""
    client.post("/product?price=100")
    res = client.get("/products")
    assert res.status_code == 200
    assert len(res.json()) == 1

def test_get_products_returns_list(client):
    """TC-37 ✅ Response is always a list."""
    res = client.get("/products")
    assert isinstance(res.json(), list)

def test_get_products_multiple(client):
    """TC-38 ✅ Multiple products all appear."""
    client.post("/product?price=100")
    client.post("/product?price=200")
    client.post("/product?price=300")
    res = client.get("/products")
    assert len(res.json()) == 3

def test_get_products_wrong_method(client):
    """TC-39 ❌ POST on /products → 405."""
    res = client.post("/products")
    assert res.status_code == 405

def test_get_products_each_has_price(client):
    """TC-40 ✅ Each product has a price field."""
    client.post("/product?price=500")
    res = client.get("/products")
    products = res.json()
    assert all("price" in p for p in products)


def test_full_flow(client):
    """TC-41 ✅ Full flow: create cart → add item → checkout."""
    prod = client.post("/product?price=200").json()["id"]
    cart_id = client.post("/cart", json={"user_id": 1}).json()["id"]
    client.post("/cart/add", json={
        "cart_id": cart_id, "product_id": prod, "quantity": 1
    })
    res = client.post(f"/cart/checkout?cart_id={cart_id}")
    assert res.status_code == 200

def test_delete_then_checkout(client, cart, product):
    """TC-42 ❌ Delete cart then try to checkout → 404."""
    client.delete(f"/cart/{cart}")
    res = client.post(f"/cart/checkout?cart_id={cart}")
    assert res.status_code == 404

def test_add_item_after_checkout(client, cart, product):
    """TC-43 ❌ Add item to checked-out cart → 400 or 404."""
    client.post("/cart/add", json={
        "cart_id": cart, "product_id": product, "quantity": 1
    })
    client.post(f"/cart/checkout?cart_id={cart}")
    res = client.post("/cart/add", json={
        "cart_id": cart, "product_id": product, "quantity": 1
    })
    assert res.status_code in (400, 404)

def test_large_quantity(client, cart, product):
    """TC-44 ✅ Very large quantity is accepted."""
    res = client.post("/cart/add", json={
        "cart_id": cart, "product_id": product, "quantity": 10000
    })
    assert res.status_code in (200, 201)

def test_remove_then_add_again(client, cart, product):
    """TC-45 ✅ Remove item then add same product again."""
    add = client.post("/cart/add", json={
        "cart_id": cart, "product_id": product, "quantity": 1
    })
    item_id = add.json()["id"]
    client.delete(f"/cart/remove/{item_id}")
    res = client.post("/cart/add", json={
        "cart_id": cart, "product_id": product, "quantity": 1
    })
    assert res.status_code in (200, 201)

def test_two_carts_same_user(client, product):
    """TC-46 ✅ Same user can have two carts."""
    c1 = client.post("/cart", json={"user_id": 1}).json()["id"]
    c2 = client.post("/cart", json={"user_id": 1}).json()["id"]
    assert c1 != c2

def test_checkout_response_has_total(client, cart, product):
    """TC-47 ✅ Checkout response contains total amount."""
    client.post("/cart/add", json={
        "cart_id": cart, "product_id": product, "quantity": 2
    })
    res = client.post(f"/cart/checkout?cart_id={cart}")
    data = res.json()
    assert "total" in data   # adjust to your response key

def test_add_item_float_quantity(client, cart, product):
    """TC-48 ❌ Float quantity like 1.5 → 422."""
    res = client.post("/cart/add", json={
        "cart_id": cart, "product_id": product, "quantity": 1.5
    })
    assert res.status_code == 422

def test_product_price_stored_correctly(client):
    """TC-49 ✅ Price in response matches what was sent."""
    client.post("/product?price=750")
    products = client.get("/products").json()
    assert products[0]["price"] == 750

def test_invalid_route(client):
    """TC-50 ❌ Unknown route returns 404."""
    res = client.get("/this-route-does-not-exist")
    assert res.status_code == 404