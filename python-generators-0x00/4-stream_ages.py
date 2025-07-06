import mysql.connector

def stream_user_ages():
    """Generator that yields user ages one by one from the database."""
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='PassCode@254!!',
        database='ALX_prodev'
    )
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT age FROM user_data")
        for (age,) in cursor:  # ✅ Loop 1
            yield age
    finally:
        cursor.close()
        connection.close()


def compute_average_age():
    """Computes the average age using the stream_user_ages generator."""
    total = 0
    count = 0
    for age in stream_user_ages():  # ✅ Loop 2
        total += float(age)
        count += 1

    if count == 0:
        print("No users found.")
    else:
        average = total / count
        print(f"Average age of users: {average:.2f}")

if __name__ == "__main__":
    compute_average_age()
