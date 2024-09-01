from pydantic import BaseModel

class ProductBase(BaseModel):
    ProductSubcategoryKey: int
    ProductSKU: str
    ProductName: str
    ModelName: str
    ProductDescription: str
    ProductColor: str
    ProductSize: str
    ProductStyle: str
    ProductCost: float
    ProductPrice: float

class Product(ProductBase):
    ProductKey: int
