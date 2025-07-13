import time
import sqlite3
import functools


# ✅ Decorator to manage DB connection
def with_db_connection(func):
   @functools.wraps(func)
   def wrapper(*args, **kwargs):
       conn = sqlite3.connect('users.db')
       try:
           return func(conn, *args, **kwargs)
       finally:
           conn.close()
   return wrapper


# ✅ Decorator to retry on failure
def retry_on_failure(retries=3, delay=2):
   def decorator(func):
       @functools.wraps(func)
       def wrapper(*args, **kwargs):
           attempt = 0
           while attempt < retries:
               try:
                   return func(*args, **kwargs)
               except Exception as e:
                   attempt += 1
                   print(f"[Retry {attempt}] Failed due to: {e}")
                   if attempt == retries:
                       print("[ERROR] Max retries reached. Operation failed.")
                       raise
                   time.sleep(delay)
       return wrapper
   return decorator


@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
   cursor = conn.cursor()
   cursor.execute("SELECT * FROM users")
   return cursor.fetchall()


# ✅ Attempt to fetch users with retry
users = fetch_users_with_retry()
print(users)
