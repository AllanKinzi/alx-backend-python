import sqlite3


class DatabaseConnection:
   def __init__(self, db_name):
       self.db_name = db_name
       self.connection = None


   def __enter__(self):
       self.connection = sqlite3.connect(self.db_name)
       return self.connection


   def __exit__(self, exc_type, exc_val, exc_tb):
       if self.connection:
           if exc_type:
               print("An error occurred:", exc_val)
           self.connection.close()


if __name__ == "__main__":
   with DatabaseConnection("users.db") as conn:
       cursor = conn.cursor()
       cursor.execute("SELECT * FROM users")
       results = cursor.fetchall()
       for row in results:
           print(row)
