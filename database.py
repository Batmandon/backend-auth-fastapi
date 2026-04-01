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
   conn.commit()
   conn.close()