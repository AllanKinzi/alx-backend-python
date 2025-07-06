import mysql.connector

def stream_users_in_batches(batch_size):
    """Generator that yields rows from user_data in batches."""
    connection = mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        password='Kenya@254!!',
        database='ALX_prodev'
    )
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM user_data")
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break
            yield batch  # ✅ Yield the batch
    finally:
        cursor.close()
        connection.close()


def batch_processing(batch_size):
    """Generator that yields users over age 25, batch by batch."""
    for batch in stream_users_in_batches(batch_size):  # ✅ Loop 1
        for user in batch:  # ✅ Loop 2
            if user['age'] > 25:
                yield user  # ✅ Yield filtered user
    return

if __name__ == "__main__":
    for user in batch_processing(3):  # ✅ Loop 3
        print(user)
