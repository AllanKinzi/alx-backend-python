import sqlite3


class ExecuteQuery:
   def __init__(self, db_name, query, params=()):
       self.db_name = db_name
       self.query = query
       self.params = params
       self.connection = None
       self.cursor = None
       self.results = None


   def __enter__(self):
       self.connection = sqlite3.connect(self.db_name)
       self.cursor = self.connection.cursor()
       self.cursor.execute(self.query, self.params)
       self.results = self.cursor.fetchall()
       return self.results


   def __exit__(self, exc_type, exc_val, exc_tb):
       if self.cursor:
           self.cursor.close()
       if self.connection:
           self.connection.close()
       if exc_type:
           print("An error occurred:", exc_val)


if __name__ == "__main__":
   query = "SELECT * FROM users WHERE age > ?"
   params = (25,)
   with ExecuteQuery("users.db", query, params) as results:
       for row in results:
           print(row)