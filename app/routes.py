from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Optional
from models import ProductBase, Product
from auth import (
    get_current_active_user,
    authenticate_user,
    create_access_token,
    admin_required,
    Token,
    User,
    fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from database import get_db
from logging_config import logger

router = APIRouter()


### Rota para Autenticação ###

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


### Rota inicial ###
@router.get("/")
def read_root():
    return {"Message": "Use swagger on http://localhost:8000/docs#/"}

### Rota para READ ###

@router.get("/products")
async def get_products(
    db=Depends(get_db),
    page: Optional[int] = 0,
    page_size: Optional[int] = 0,
    typeFilter: Optional[str] = None,
    searchFilter: Optional[str] = None,
    orderBy: Optional[str] = None,
):
    query = "SELECT * FROM products"

    params = []
    if typeFilter is not None and searchFilter is not None:
        print(ProductBase.__annotations__)
        print(typeFilter)
        if (
            typeFilter in ProductBase.__annotations__
            or typeFilter in Product.__annotations__
        ):
            query += " WHERE {} LIKE %s".format(typeFilter)
            params.append(f"%{searchFilter}%")
        else:
            raise HTTPException(status_code=400, detail="Filter not in product table")

    if orderBy is not None:
        if (
            orderBy in ProductBase.__annotations__
            or orderBy in Product.__annotations__
        ):
            query += " ORDER BY {}".format(orderBy)
        else:
            raise HTTPException(status_code=400, detail="Order not in product table")

    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query += " LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

    cursor = db.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    return result


@router.get("/products/{id}")
async def get_product(
    id: int,
    db=Depends(get_db),
):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products WHERE ProductKey = {}".format(id))
    result = cursor.fetchone()
    cursor.close()
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


### Rota para CREATE ###

@router.post("/products", response_model=Product, status_code=201)
async def add_product(
    product: ProductBase,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db=Depends(get_db),
    _=Depends(admin_required),
):
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO products (ProductSubcategoryKey, ProductSku, ProductName, ModelName, ProductDescription, ProductColor, ProductSize, ProductStyle, ProductCost, ProductPrice) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                product.ProductSubcategoryKey,
                product.ProductSKU,
                product.ProductName,
                product.ModelName,
                product.ProductDescription,
                product.ProductColor,
                product.ProductSize,
                product.ProductStyle,
                product.ProductCost,
                product.ProductPrice,
            ),
        )
        db.commit()
        cursor.close()
        logger.info(f"Product added by user {current_user.username}: {product}")
        return {**product.model_dump(), "ProductKey": cursor.lastrowid}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add product: {e} by user {current_user.username}")
        raise HTTPException(status_code=500, detail="Erro on adding product")


### Rota para DELETE ###

@router.delete("/products/{id}")
async def delete_product(
    id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db=Depends(get_db),
    _=Depends(admin_required),
):
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM products WHERE ProductKey = {}".format(id))
        if cursor.rowcount == 0:
            logger.warning(
                f"Product with id {id} not found for deletion by user {current_user.username}"
            )
            raise HTTPException(status_code=404, detail="Product not found")
        db.commit()
        cursor.close()
        logger.info(f"Product with id {id} deleted by user {current_user.username}")
        return {"detail": "Product deleted"}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to delete product with id {id}: {e} by user {current_user.username}"
        )
        raise HTTPException(status_code=500, detail="Error on delecting product")


### Rota para UPDATE ###

@router.put("/products/{id}", response_model=Product)
async def update_product(
    id: int,
    product: ProductBase,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db=Depends(get_db),
    _=Depends(admin_required),
):
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE products SET ProductSubcategoryKey = %s, ProductSku = %s, ProductName = %s, ModelName = %s, ProductDescription = %s, ProductColor = %s, ProductSize = %s, ProductStyle = %s, ProductCost = %s, ProductPrice = %s WHERE ProductKey = %s",
            (
                product.ProductSubcategoryKey,
                product.ProductSKU,
                product.ProductName,
                product.ModelName,
                product.ProductDescription,
                product.ProductColor,
                product.ProductSize,
                product.ProductStyle,
                product.ProductCost,
                product.ProductPrice,
                id,
            ),
        )
        db.commit()
        cursor.close()
        if cursor.rowcount == 0:
            logger.warning(
                f"Product with id {id} not found for update by user {current_user.username}"
            )
            raise HTTPException(status_code=404, detail="Product not found")
        logger.info(
            f"Product with id {id} updated by user {current_user.username}: {product}"
        )
        return {**product.model_dump(), "ProductKey": id}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to update product with id {id}: {e} by user {current_user.username}"
        )
        raise HTTPException(status_code=500, detail="Error when updating product")


### Tarefa 3 ###

@router.get("/sales/top-products/category/{category}")
async def top10_produtos_mais_vendidos(category: int, db=Depends(get_db)):
    cursor = db.cursor()
    query = """
    select comb.ProductKey, comb.ProductName, sum(vendas) as total_vendas from(
    select prod.ProductKey, prod.ProductName, count(prod.ProductKey) as vendas from products as prod 
    inner join product_subcategories as ps on ps.ProductSubcategoryKey = prod.ProductSubcategoryKey
    inner join sales_2016 as s16 on s16.ProductKey = prod.ProductKey where ps.ProductCategoryKey = %s
    group by prod.Productkey
    union all
    select prod.ProductKey, prod.ProductName, count(prod.ProductKey) as vendas from products as prod 
    inner join product_subcategories as ps on ps.ProductSubcategoryKey = prod.ProductSubcategoryKey
    inner join sales_2017 as s17 on s17.ProductKey = prod.ProductKey where ps.ProductCategoryKey = %s
    group by prod.Productkey
    union all
    select prod.ProductKey, prod.ProductName, count(prod.ProductKey) as vendas from products as prod 
    inner join product_subcategories as ps on ps.ProductSubcategoryKey = prod.ProductSubcategoryKey
    inner join sales_2015 as s15 on s15.ProductKey = prod.ProductKey where ps.ProductCategoryKey = %s
    group by prod.Productkey
    ) as comb group by comb.ProductKey, comb.ProductName order by total_vendas desc limit 10;
    """
    cursor.execute(
        query,
        (
            category,
            category,
            category,
        ),
    )
    result = cursor.fetchall()
    cursor.close()
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return result


@router.get("/sales/best-customer/")
async def cliente_com_mais_pedidos(db=Depends(get_db)):
    cursor = db.cursor()
    query = """
    select comb.CustomerKey, comb.FirstName, comb.LastName, sum(compras) as total_compras from(
    select cus.CustomerKey, cus.FirstName, cus.LastName, count(cus.CustomerKey) as compras from customers as cus
    inner join sales_2015 as s15 on s15.CustomerKey = cus.CustomerKey
    group by cus.CustomerKey
    union all
    select cus.CustomerKey, cus.FirstName, cus.LastName, count(cus.CustomerKey) as compras from customers as cus
    inner join sales_2016 as s16 on s16.CustomerKey = cus.CustomerKey
    group by cus.CustomerKey
    union all
    select cus.CustomerKey, cus.FirstName, cus.LastName, count(cus.CustomerKey) as compras from customers as cus
    inner join sales_2017 as s17 on s17.CustomerKey = cus.CustomerKey
    group by cus.CustomerKey
    )as comb group by comb.CustomerKey, comb.FirstName, comb.LastName order by total_compras desc limit 1;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result


@router.get("/sales/busiest-month/")
async def mes_com_mais_venda(db=Depends(get_db)):
    cursor = db.cursor()
    query = """
    select comb.mes, sum(valor) as total_valor from(
    select month(str_to_date(s15.OrderDate, '%m/%d/%Y')) as mes, round(sum(prod.ProductPrice),2) as valor from sales_2015 as s15
    inner join products as prod on prod.ProductKey = s15.ProductKey group by mes
    union all
    select month(str_to_date(s16.OrderDate, '%m/%d/%Y')) as mes, round(sum(prod.ProductPrice),2) as valor from sales_2016 as s16
    inner join products as prod on prod.ProductKey = s16.ProductKey group by mes
    union all
    select month(str_to_date(s17.OrderDate, '%m/%d/%Y')) as mes, round(sum(prod.ProductPrice),2) as valor from sales_2017 as s17
    inner join products as prod on prod.ProductKey = s17.ProductKey group by mes
    )as comb group by comb.mes order by total_valor desc limit 1;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result


@router.get("/sales/top-territories/")
async def territorios_com_vendas_acima_da_media(db=Depends(get_db)):
    cursor = db.cursor()
    query = """
    select s17.TerritoryKey, round(sum(prod.ProductPrice),2) as valor_acima_media from sales_2017 as s17
    inner join products as prod on prod.ProductKey = s17.Productkey group by s17.TerritoryKey
    having round(sum(prod.ProductPrice),2) >= (
    select round(sum(prod.ProductPrice),2) / count(distinct TerritoryKey) as valor from sales_2017 as s17
    inner join products as prod on prod.ProductKey = s17.Productkey
    ) order by valor_acima_media desc;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result
