import sqlite3

def create_database():

   conn = sqlite3.connect("ecommerce.db")
   cursor = conn.cursor()

   cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  email TEXT UNIQUE,
                  password TEXT,
                  role TEXT)
                """)
    
   cursor.execute("""CREATE TABLE IF NOT EXISTS sellers(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER UNIQUE NOT NULL,
                  business_name TEXT,
                  phone INTEGER,
                  gst_no TEXT,
                  verification_status TEXT DEFAULT 'pending',
                  can_sell BOOLEAN DEFAULT 0
                )
                """)
    
   cursor.execute("""CREATE TABLE IF NOT EXISTS products(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  seller_id INTEGER,
                  name TEXT,
                  description TEXT,
                  category TEXT,
                  price REAL,
                  quantity INTEGER,
                  gender TEXT
                  )
                   """)
    
   cursor.execute("""CREATE TABLE IF NOT EXISTS orders(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER ,
                  product_id INTEGER,
                  quantity INTEGER,
                  total_price REAL,
                  order_date TEXT,
                  status TEXT DEFAULT 'pending',
                  estimated_delivery TEXT,
                  update_time TEXT,
                  payment_status TEXT DEFAULT 'pending',
                  payment_method TEXT
                  
               )
                  """)
    

   cursor.execute("""CREATE TABLE IF NOT EXISTS wishlists(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  product_id INTEGER,
                  price REAL
                  )
                  """)
   cursor.execute("""CREATE TABLE IF NOT EXISTS carts(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  product_id INTEGER,
                  quantity INTEGER,
                  price REAL,
                  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                  """)
   
   cursor.execute("""CREATE TABLE IF NOT EXISTS reviews(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER,
                  user_id INTEGER,
                  rating INTEGER,
                  review TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                  """)
   
   cursor.execute("""CREATE TABLE IF NOT EXISTS notifications(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  message TEXT,
                  is_read BOOLEAN DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

   conn.commit()
   conn.close()