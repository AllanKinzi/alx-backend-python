import sqlite3
import functools


def log_queries():
   def decorator_log_queries(func):
       @functools.wraps(func)
       def wrapper(*args, **kwargs):
           query = kwargs.get('query') or (args[0] if args else None)
           if query:
               print(f"[LOG] Executing SQL Query: {query}")
           return func(*args, **kwargs)
       return wrapper
   return decorator_log_queries


@log_queries()
def fetch_all_users(query):
   conn = sqlite3.connect('users.db')
   cursor = conn.cursor()
   cursor.execute(query)
   results = cursor.fetchall()
   conn.close()
   return results


users = fetch_all_users(query="SELECT * FROM users")
print(users)
