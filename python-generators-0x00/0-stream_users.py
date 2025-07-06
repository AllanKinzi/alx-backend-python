import mysql.connector

def stream_users():
    """Generator function that yields rows from user_data table one by one."""
    connection = mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='Passcode@254!!',
        database='ALX_prodev'
    )
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM user_data")

        for row in cursor:
            yield row

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    for user in stream_users():
        print(user)