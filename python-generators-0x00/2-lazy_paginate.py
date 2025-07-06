import mysql.connector

def paginate_users(page_size, offset):
    """Fetch a single page of users starting from the given offset."""
    connection = mysql.connector.connect(
          host='localhost',
        port=3306,
        user='root',
        password='Passcode@254!!',
        database='ALX_prodev'
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = "SELECT * FROM user_data LIMIT %s OFFSET %s"
        cursor.execute(query, (page_size, offset))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

def lazy_paginate(page_size):
    """Generator that yields one page of users at a time, lazily."""
    offset = 0
    while True:  # ✅ Only loop
        page = paginate_users(page_size, offset)
        if not page:
            break
        yield page  # ✅ Yield each page
        offset += page_size  # Move to next page

if __name__ == "__main__":
    for page in lazy_paginate(5):  # Only one loop
        for user in page:
            print(user)