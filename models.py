from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserRefresh(BaseModel):
    token: str
    
class SellerCreate(BaseModel):
    name: str
    email: str
    password: str
    business_name: str
    phone: int
    gst_no: str


class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    price: float
    quantity: int
    gender: str

class ProductUpdate(BaseModel):
    name: str
    description: str
    category: str
    price: float

class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    payment_method: str

class BankDetails(BaseModel):
    user_id: int
    bank_name: str
    account_number: str
    ifsc_code: str
