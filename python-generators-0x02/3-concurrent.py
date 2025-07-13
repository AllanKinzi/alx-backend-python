import asyncio
import aiosqlite


# Async function to fetch all users
async def async_fetch_users():
   async with aiosqlite.connect("users.db") as db:
       async with db.execute("SELECT * FROM users") as cursor:
           rows = await cursor.fetchall()
           print("All Users:")
           for row in rows:
               print(row)


# Async function to fetch users older than 40
async def async_fetch_older_users():
   async with aiosqlite.connect("users.db") as db:
       async with db.execute("SELECT * FROM users WHERE age > 40") as cursor:
           rows = await cursor.fetchall()
           print("\nUsers older than 40:")
           for row in rows:
               print(row)


# Function to run both concurrently
async def fetch_concurrently():
   await asyncio.gather(
       async_fetch_users(),
       async_fetch_older_users()
   )


# Run the concurrent fetch
if __name__ == "__main__":
   asyncio.run(fetch_concurrently())
