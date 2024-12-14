import sqlite3
import bcrypt

connection = sqlite3.connect("mixmuse_users.db")
cursor = connection.cursor()

try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accepted_applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            job_id TEXT NOT NULL
        )
    ''')
    print("Table added successfully.")
except sqlite3.Error as e:
    print(f"An error occurred: {e}")
finally:
    # Commit the changes and close the connection
    connection.commit()
    connection.close()



# cursor.execute("""
#         CREATE TABLE IF NOT EXISTS new_users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             fullname TEXT NOT NULL UNIQUE,
#             username TEXT NOT NULL UNIQUE,
#             email TEXT NOT NULL,
#             phoneno TEXT NOT NULL,
#             gender TEXT NOT NULL,
#             address TEXT,
#             skills TEXT,
#             experience TEXT,
#             password TEXT NOT NULL
#         )
#     """)
# cursor.execute("SELECT username, password FROM users")
# users = cursor.fetchall()

# for user in users:
#     username = user[0]
#     password = user[1]
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
#     cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))

    

