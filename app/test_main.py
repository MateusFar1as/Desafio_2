import sqlite3
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

@pytest.fixture(scope="module")
def dbTest():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE products (
        ProductKey INTEGER PRIMARY KEY,
        ProductSubcategoryKey INT NOT NULL,
        ProductSKU VARCHAR(15),
        ProductName TEXT,
        ModelName TEXT,
        ProductDescription TEXT,
        ProductColor VARCHAR(25),
        ProductSize VARCHAR(5),
        ProductStyle CHAR(1) CHECK(length(ProductStyle) <= 1),
        ProductCost DECIMAL(15,4),
        ProductPrice DECIMAL(15,4)
    )
    ''')

    cursor.execute('''
    INSERT INTO products (ProductKey, ProductSubcategoryKey, ProductSKU, ProductName, ModelName, ProductDescription, ProductColor, ProductSize, ProductStyle, ProductCost, ProductPrice) VALUES
    (1, 1, 'abc', 'abc', 'abc', 'abc', 'abc', 'abc', 'a', 100, 200)
    ''')

    conn.commit()
    
    def override_get_db():
        return conn

    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield conn
    finally:
        conn.close()


client = TestClient(app)

def get_access_token(username: str, password: str):
    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

def get_access_token_fail(username: str, password: str):
    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 401


### Testes READ ###

def test_get_products():
    response = client.get("/products")
    assert response.status_code == 200

def test_get_product():
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json() == {
        "ProductKey": 1,
        "ProductSubcategoryKey": 1,
        "ProductSKU": "abc",
        "ProductName": "abc",
        "ModelName": "abc",
        "ProductDescription": "abc",
        "ProductColor": "abc",
        "ProductSize": "abc",
        "ProductStyle": "a",
        "ProductCost": 100.0,
        "ProductPrice": 200.0
    }

def test_get_product_fail():
    response = client.get("products/-1")
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


### Testes CREATE ###

def test_add_product():
    token = get_access_token("admin", "secret")

    new_product = {
        "ProductSubcategoryKey": 1,
        "ProductSKU": "testsku",
        "ProductName": "Test Product",
        "ModelName": "Test Model",
        "ProductDescription": "Test Description",
        "ProductColor": "Blue",
        "ProductSize": "M",
        "ProductStyle": "A",
        "ProductCost": 50.00,
        "ProductPrice": 100.00
    }

    response = client.post(
        "/products",
        json=new_product,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201

def test_add_product_unauthorized():
    token = get_access_token_fail("admin", "nenhuma")

    new_product = {
        "ProductSubcategoryKey": 1,
        "ProductSKU": "testsku",
        "ProductName": "Test Product",
        "ModelName": "Test Model",
        "ProductDescription": "Test Description",
        "ProductColor": "Blue",
        "ProductSize": "M",
        "ProductStyle": "A",
        "ProductCost": 50.00,
        "ProductPrice": 100.00
    }

    response = client.post(
        "/products",
        json=new_product,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401

def test_add_product_fail():
    token = get_access_token("admin", "secret")

    new_product = {
        "ProductSubcategoryKey": 1,
        "ProductSKU": "testsku",
        "ProductName": "Test Product",
        "ModelName": "Test Model",
        "ProductDescription": "Test Description",
        "ProductColor": "Blue",
        "ProductSize": "M",
        "ProductStyle": "ABCDE",
        "ProductCost": 50.00,
        "ProductPrice": 100.00
    }

    response = client.post(
        "/products",
        json=new_product,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 500


### Testes DELETE ###

def test_delete_product():
    token = get_access_token("admin", "secret")
    response = client.delete(
        "/products/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Product deleted"}

def test_delete_product_unauthourized():
    token = get_access_token_fail("admin", "nenhuma")
    response = client.delete(
        "/products/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

def test_delete_product_fail():
    token = get_access_token("admin", "secret")
    response = client.delete(
        "/products/-1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}


### Testes UPDATE ###

def test_put_product():
    token = get_access_token("admin", "secret")

    new_product = {
        "ProductSubcategoryKey": 1,
        "ProductSKU": "testsku",
        "ProductName": "Test Product",
        "ModelName": "Test Model",
        "ProductDescription": "Test Description",
        "ProductColor": "Blue",
        "ProductSize": "M",
        "ProductStyle": "A",
        "ProductCost": 50.00,
        "ProductPrice": 100.00
    }

    response = client.put(
        "/products/1",
        json=new_product,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

def test_put_product_unauthorized():
    token = get_access_token_fail("admin", "nenhuma")

    new_product = {
        "ProductSubcategoryKey": 1,
        "ProductSKU": "testsku",
        "ProductName": "Test Product",
        "ModelName": "Test Model",
        "ProductDescription": "Test Description",
        "ProductColor": "Blue",
        "ProductSize": "M",
        "ProductStyle": "A",
        "ProductCost": 50.00,
        "ProductPrice": 100.00
    }

    response = client.put(
        "/products/1",
        json=new_product,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401

def test_put_product_fail():
    token = get_access_token("admin", "secret")

    new_product = {
        "ProductSubcategoryKey": 1,
        "ProductSKU": "testsku",
        "ProductName": "Test Product",
        "ModelName": "Test Model",
        "ProductDescription": "Test Description",
        "ProductColor": "Blue",
        "ProductSize": "M",
        "ProductStyle": "A",
        "ProductCost": 50.00,
        "ProductPrice": 100.00
    }

    response = client.put(
        "/products/-1",
        json=new_product,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}
