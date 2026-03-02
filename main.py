from fastapi import FastAPI, HTTPException, Depends
from httpx import put
import uvicorn
from models import UserCreate, UserLogin,SellerCreate, ProductCreate, ProductUpdate, OrderCreate, BankDetails, UserRefresh
from database import sqlite3, create_database
from utils import hash_password, verify_password
from jwt_handler import create_access_token, create_refresh_token, decode_token
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError
from typing import Optional


app = FastAPI()
create_database()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Endpoints for users to register, login, refresh token
@app.post("/register")
def register(data: UserCreate):
    with sqlite3.connect("ecommerce.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (data.email,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
                   (data.name, data.email, hash_password(data.password), "user")
        )
        conn.commit()

        return {"message": "User registered successfully"} 

@app.post("/login")
def login(User: UserLogin):
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? ", (User.email,))

        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=403, detail="Invalid Email")
        print(f"DEBUG: user tuple = {user}, length = {len(user)}")
        is_valid = verify_password(User.password, user["password"])

        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid password")
        
        access_token = create_access_token({
            "sub": user["email"],
            "name": user["name"],
            "role": user["role"]
        })

        refresh_token = create_refresh_token({
            "sub": user["email"],
            "name": user["name"],
            "role": user["role"]
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
@app.post("/refresh")
def refresh(Refresh: UserRefresh):
    
    try:
        payload = decode_token(Refresh.token)
        token_type = payload["token_type"]
    
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        access_token = create_access_token({
            "sub": user["email"],
            "name": user["name"],
            "role": user["role"]
        })

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

# Endpoint for customers to view all products and product details
@app.get("/products")
def list_products(token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        return {
            "message": f"Hello {name}, here are the products",
            "products": [dict(row) for row in products]}
    
@app.get("/products/{product_id}")
def get_product(product_id: int, token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"message": f"Hello {name}, here are your results", "product": dict(product)}
    
# Endpoint for customers to search for products by name, category, price range and gender

@app.get("/searchproducts")
def search_products(query: str, token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE name LIKE ?", (f"%{query}%",))
        products = cursor.fetchall()
        return {"message": f"Hello {name}, here are the products matching your query '{query}'",
                "products": [dict(product) for product in products]}
    
@app.get("/searchproducts/category")
def search_products_by_category(category: str, token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE category LIKE ?", (f"%{category}%",))
        products = cursor.fetchall()
        return {"message": f"Hello {name}, here are the products in category '{category}'", 
                "products": [dict(product) for product in products]}

@app.get("/searchproducts/price")
def search_products_by_price(min_price: float, max_price: float, token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE price BETWEEN ? AND ?", (min_price, max_price))
        products = cursor.fetchall()
        return {"message": f"Hello {name}, here are the products in price range {min_price} - {max_price}",
                "products": [dict(product) for product in products]}
    
@app.get("/searchproducts/gender")
def search_products_by_gender(gender: str, token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE gender=?", (gender,))
        products = cursor.fetchall()
        return {"message": f"Hello {name}, here are the products for gender '{gender}'",
                "products": [dict(product) for product in products]}

@app.get("/filter/products")
def filter_products(category: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, gender: Optional[str] = None, token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        if category:
            query += " AND category=?"
            params.append(category)
        if min_price is not None and max_price is not None:
            query += " AND price BETWEEN ? AND ?"
            params.extend([min_price, max_price])
        if gender:
            query += " AND gender=?"
            params.append(gender)
        cursor.execute(query, params)
        products = cursor.fetchall()
        return {"message": f"Hello {name}, here are the filtered products",
                "products": [dict(product) for product in products]}

@app.get("/notifications")
def get_notifications(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found!")

        cursor.execute("""SELECT * FROM notifications 
                       WHERE user_id=? 
                       ORDER BY created_at DESC""",
                       (user["id"],))
        notifications = cursor.fetchall()

    return {"notifications": [dict(n) for n in notifications]}
# Endpoint for customers to review products and view reviews of products, they can also filter reviews by rating
    
@app.post("/products/{product_id}/review")
def review_product(product_id: int, review: str, rating: float, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    email = payload["sub"]

    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        cursor.execute("INSERT INTO reviews (product_id, user_id, review, rating) VALUES (?, ?, ?, ?)", (product_id, user["id"], review, rating))
        conn.commit()

        return {"message": "Review added to product"}
    
@app.get("/products/{product_id}/reviews")
def get_product_reviews(product_id: int, rating: Optional[float] = None, token: Optional[str] = Depends(oauth2_scheme)):
    name = "Guest"
    if token:
        try:
            payload = decode_token(token)
            name = payload["name"]
        except Exception:
            pass

    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
       
        if rating:
            cursor.execute("SELECT * FROM reviews WHERE product_id=? AND rating>=?", (product_id, rating))
        
        else:
            cursor.execute("SELECT * FROM reviews WHERE product_id=?", (product_id,))
        
        reviews = cursor.fetchall()

        return {"message": f"Hello {name}!",
                "reviews": [dict(review) for review in reviews]}

# Endpoint for customers to place orders, view their orders, cancel orders and make payments for orders
@app.post("/orders")
def place_order(token: str = Depends(oauth2_scheme), order: OrderCreate = None):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "user":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Example order placement logic
        cursor.execute("SELECT price FROM products WHERE id=?", (order.product_id,))
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        total_price = product["price"] * order.quantity
        cursor.execute("INSERT INTO orders (user_id, product_id, quantity, total_price, order_date, status, estimated_delivery, update_time, payment_status, payment_method) VALUES (?, ?, ?, ?, datetime('now'), 'pending', datetime('now', '+7 days'), datetime('now'), 'pending', ?)", (user["id"], order.product_id, order.quantity, total_price, order.payment_method))
        conn.commit()

        return {"message": "Order placed successfully"}
        
@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, user["id"]))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order["status"] != "pending":
            raise HTTPException(status_code=400, detail="Order shipped, cannot be cancelled")
        
        cursor.execute("UPDATE orders SET status='cancelled', update_time=datetime('now') WHERE id=? AND user_id=?", (order_id, user["id"]))
        conn.commit()

        return {"message": f"Order {order_id} cancelled successfully"}
    
@app.post("/wishlist")
def wishlist_products(token: str = Depends(oauth2_scheme), wishlist_product: str = None):
    payload = decode_token(token)
    email = payload["sub"]

    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user: 
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("SELECT price FROM products WHERE id=?", (wishlist_product,))
        product = cursor.fetchone()

        price = product["price"]
        cursor.execute("INSERT INTO wishlists(user_id, product_id, price) VALUES (?, ?, ?)", (user["id"], wishlist_product, price))
        conn.commit()

        return{ "message": "Wishlisted"}
    
@app.put("/orders/{order_id}/pay")
def pay_order(order_id: int, token: str = Depends(oauth2_scheme), bank: BankDetails = None):
    payload = decode_token(token)
    email = payload["sub"]

    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email =?" ,(email,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, user["id"]))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        payment_method = order["payment_method"]
        if payment_method == "online":
            cursor.execute("UPDATE orders SET status='confirmed', update_time=datetime('now'), payment_status='paid' WHERE id=? AND user_id=?", (order_id, user["id"]))
            conn.commit()
            return {"message": "Payment successful, order is being processed"}
        
        elif payment_method == "cod":
            cursor.execute("UPDATE orders SET status='confirmed', update_time=datetime('now') WHERE id=? AND user_id=?", (order_id, user["id"]))
            conn.commit()
            return {"message": "Order confirmed, Pay cash on delivery"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")

# Cart endpoints for customers to add products to cart, view cart, remove items from cart and clear cart

@app.post("/cart/{product_id}")
def cart_product(token:str = Depends(oauth2_scheme), product_id: int = None, quantity: int = None):
    payloadd = decode_token(token)
    email = payloadd["sub"]
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT price FROM products WHERE id=?", (product_id,))
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        price = product["price"]
        cursor.execute("INSERT INTO carts(user_id, product_id, quantity, price, added_at) VALUES (?, ?, ?, ?, datetime('now'))", (user["id"], product_id, quantity, price))
        conn.commit()

        return {"message": "Product added to cart"}

@app.get("/cart")
def get_cart_products(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    email = payload["sub"]

    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("SELECT * FROM carts WHERE user_id=?", (user["id"],))
        cart_items = cursor.fetchall()
        if not cart_items:
            raise HTTPException(status_code=404, detail="Cart is empty")

        return {"cart_items": [dict(cart_item) for cart_item in cart_items]}
    
@app.delete("/cart/{product_id}")
def remove_cart_item(product_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    email = payload["sub"]

    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("DELETE FROM carts WHERE product_id=? AND user_id=?", (product_id, user["id"]))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found in cart")

        conn.commit()
        return {"message": "Item removed from cart"}

@app.delete("/cart")
def clear_cart(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    email = payload["sub"]

    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute("DELETE FROM carts WHERE user_id=?", (user["id"],))
        conn.commit()
        return {"message": "Cart cleared"}

# customer endpoint to view their orders, and delete orders
@app.get("/customer/orders")
def list_customer_orders(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "customer":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("""SELECT orders.id, users.name AS customer_name, products.name AS product_name, orders.quantity, orders.total_price, orders.order_date, orders.status 
                       FROM orders JOIN users ON orders.user_id = users.id JOIN products ON orders.product_id = products.id WHERE orders.user_id=?""", (user["id"],))
        orders = cursor.fetchall()

        return {"orders": [dict(row) for row in orders]}
    
@app.delete("/customer/orders/{order_id}")
def remove_customer_order(order_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "customer":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        conn.commit()

        return {"message": f"Order with id {order_id} has been removed from the platform"}

@app.delete("/customer/orders")
def clear_customer_orders(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "customer":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM orders WHERE user_id=?", (user["id"],))
        conn.commit()
        return {"message": "All your orders have been cleared from the platform"}
 
 # Seller endpoints to create, update and delete products, view their products and orders, update order status to shipped and delivered,view orders of their products,remove orders of their products and clear orders of their products    
@app.post("/register/seller")
def register(data: SellerCreate):
    with sqlite3.connect("ecommerce.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (data.email,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        cursor.execute("INSERT INTO users(name, email, password, role) VALUES (?,?,?,?)",
                   (data.name, data.email, hash_password(data.password), "seller"))

        user_id = cursor.lastrowid

        cursor.execute("INSERT INTO sellers(user_id, business_name, phone, gst_no) VALUES (?,?,?,?)",
                   (user_id, data.business_name, data.phone, data.gst_no))
        conn.commit()

        return {"message": "Seller registered successfully"}
        

@app.post("/create/products")
def create_product(token: str = Depends(oauth2_scheme), product: ProductCreate = None):

    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()

        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("INSERT INTO products(seller_id, name, description, category, price, quantity, gender) VALUES (?,?,?,?,?,?,?)",
                   (seller["id"], product.name, product.description, product.category, product.price,product.quantity, product.gender)
        )
        conn.commit()

        return {"message": "Product created successfully"}
    
@app.put("/products/{product_id}")
def update_product(product_id: int, token: str = Depends(oauth2_scheme), product: ProductUpdate = None):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()
        
        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        cursor.execute("UPDATE products SET name=?, description=?, category=?, price=? WHERE id=?",
                   (product.name, product.description, product.category, product.price, product_id))
        conn.commit()

        return {"message": "Product updated successfully"}
    
@app.delete("/products/{product_id}")
def delete_product(product_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()

        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()

        return {"message": "Product deleted successfully"}
    
@app.get("/seller/products")
def get_seller_products(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()

        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("SELECT * FROM products WHERE seller_id=?", (seller["id"],))
        products = cursor.fetchall()

        return {"products": [dict(product) for product in products]}
    
@app.get("/seller/orders")
def get_seller_orders(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()

        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("SELECT * FROM orders WHERE product_id IN (SELECT id FROM products WHERE seller_id=?)", (seller["id"],))
        orders = cursor.fetchall()

        return {"orders": [dict(order) for order in orders]}
    
@app.post("/cancel/orders/{order_id}")
def cancel_seller_order(order_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()

        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("UPDATE orders SET status='cancelled' WHERE id=? AND product_id IN (SELECT id FROM products WHERE seller_id=?)", (order_id, seller["id"]))
        conn.commit()

        # Check order exists!
        cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found!")

        # created_at automatic!
        cursor.execute("INSERT INTO notifications(user_id, message) VALUES (?, ?)", 
                      (order["user_id"], f"Your order with id {order_id} has been cancelled by the seller"))
        conn.commit()

        return {"message": f"Order {order_id} has been cancelled"}
    
@app.put("/seller/orders/{order_id}/shipped")
def update_order_status(order_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()

        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("UPDATE orders SET status='shipped' WHERE id=? AND product_id IN (SELECT id FROM products WHERE seller_id=?)", (order_id, seller["id"]))
        conn.commit()

        return {"message": f"Order {order_id} status updated to shipped"}
    
@app.put("/seller/orders/{order_id}/delivered")
def mark_order_delivered(order_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("SELECT * FROM sellers WHERE user_id = ?", (user["id"],))
        seller = cursor.fetchone()

        if not seller:
            raise HTTPException(status_code=404, detail="Seller profile not found")
        if user["role"] != "seller" or seller["verification_status"] != "verified" or seller["can_sell"] != 1:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("UPDATE orders SET status=? WHERE id=?", ("delivered", order_id))
        conn.commit()
        cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        orders = cursor.fetchone()

        if not orders:
            raise HTTPException(status_code=404, detail="Order not found")
        if orders["payment_method"] == "cod":
            cursor.execute("UPDATE orders SET payment_status='paid' WHERE id=?", (order_id,))
        conn.commit()

        return {"message": f"Order {order_id} status updated to delivered"}

@app.get("/seller/orders")
def list_seller_orders(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "seller":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("""SELECT orders.id, users.name AS customer_name, products.name AS product_name, orders.quantity, orders.total_price, orders.order_date, orders.status 
                       FROM orders JOIN users ON orders.user_id = users.id JOIN products ON orders.product_id = products.id WHERE products.seller_id=?""", (user["id"],))
        orders = cursor.fetchall()

        return {"orders": [dict(row) for row in orders]}

@app.delete("/sellers/orders/{order_id}")
def remove_seller_order(order_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "seller":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        conn.commit()

        return {"message": f"Order with id {order_id} has been removed from the platform"}

@app.delete("/sellers/orders")
def clear_seller_orders(token: str = Depends(oauth2_scheme)):    
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "seller":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("""DELETE FROM orders WHERE product_id IN (SELECT id FROM products WHERE seller_id=?)""", (user["id"],))
        conn.commit()
        return {"message": "All your orders have been cleared from the platform"}

#Develop admin panel for verification of sellers and products

@app.get("/admin/{email}/{name}")
def make_admin(email: str, name: str):
    with sqlite3.connect("ecommerce.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        cursor.execute("UPDATE users SET role='admin' WHERE email=?", (email,))
        conn.commit()

        return {"message": f"{name} is now an admin"}

#Admin endpoints to verify sellers, reject sellers, remove sellers, list all sellers, list all products, list all users and remove users and products...

@app.put("/admin/verify/seller/{seller_id}")
def verify_seller(seller_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("UPDATE sellers SET verification_status='verified', can_sell=1 WHERE id=?", (seller_id,))
        conn.commit()

        return {"message": f" All details of Seller with id {seller_id} have been verified, they can now sell products on the platform"}
    
@app.put("/admin/reject/seller/{seller_id}")
def reject_seller(seller_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("UPDATE sellers SET verification_status='rejected', can_sell=0 WHERE id=?", (seller_id,))
        conn.commit()

        return {"message": f"Seller with id {seller_id} has been rejected, they cannot sell products on the platform"}
    
@app.delete("/admin/remove/seller/{seller_id}")
def remove_seller(seller_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM sellers WHERE id=?", (seller_id,))
        conn.commit()

        return {"message": f"Seller with id {seller_id} has been removed from the platform"}

@app.get("/admin/sellers")
def list_sellers(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("""SELECT sellers.id, users.name, users.email, sellers.business_name, sellers.phone, sellers.gst_no, sellers.verification_status 
                       FROM sellers JOIN users ON sellers.user_id = users.id""")
        sellers = cursor.fetchall()

        return {"sellers": [dict(row) for row in sellers]}
    
@app.get("/admin/products")
def list_all_products(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("""SELECT products.id, products.name, products.description, products.category, products.price, users.name AS seller_name 
                       FROM products JOIN sellers ON products.seller_id = sellers.id JOIN users ON sellers.user_id = users.id""")
        products = cursor.fetchall()

        return {"products": [dict(row) for row in products]}
    
@app.get("/admin/users")
def list_users(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("SELECT id, name, email, role FROM users")
        users = cursor.fetchall()

        return {"users": [dict(row) for row in users]}
    
@app.delete("/admin/users/{user_id}")
def remove_user(user_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()

        return {"message": f"User with id {user_id} has been removed from the platform"}
    
@app.delete("/admin/product/{product_id}")
def remove_product(product_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()

        return {"message": f"Product with id {product_id} has been removed from the platform"}

@app.get("/admin/orders")
def list_orders(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("""SELECT orders.id, users.name AS customer_name, products.name AS product_name, orders.quantity, orders.total_price, orders.order_date, orders.status 
                       FROM orders JOIN users ON orders.user_id = users.id JOIN products ON orders.product_id = products.id""")
        orders = cursor.fetchall()

        return {"orders": [dict(row) for row in orders]}
    
@app.delete("/admin/orders/{order_id}")
def remove_order(order_id: int, token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        conn.commit()

        return {"message": f"Order with id {order_id} has been removed from the platform"}
    
@app.delete("/admin/orders")
def clear_orders(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    with sqlite3.connect("ecommerce.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (payload["sub"],))
        user = cursor.fetchone()
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        cursor.execute("DELETE FROM orders")
        conn.commit()
        return {"message": "All orders have been cleared from the platform"}
    

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)