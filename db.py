import threading
import sqlite3

connection = sqlite3.connect("users.db")


def build_db():
    print("111", threading.get_native_id())
    connection.execute("""CREATE TABLE IF NOT EXISTS users(username TEXT NOT NULL, firstname TEXT NOT NULL, 
    lastname TEXT NOT NULL, password TEXT NOT NULL, score INT NOT NULL) """)


def check_password(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Check if the username exists in the database
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()

    if result is None:
        print("Username not found.")
        conn.close()
        return False

    # Check if the password matches
    if result[0] == password:
        print("Password correct!")
        conn.close()
        return True
    else:
        print("Incorrect password.")
        conn.close()
        return False


def clear_database():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Loop over all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        # Delete all rows from the table
        cursor.execute("DELETE FROM {table[0]}")

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()


def user_exists(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    print(username)
    # Select all rows from the "users" table where the "username" column matches the input
    cursor.execute('SELECT * FROM users WHERE username=?', (username,))
    result = cursor.fetchone()

    # If the result is not None, a user with that username exists in the database
    print(result)
    if result is not None:
        print("true")
        conn.close()
        return True
    else:
        print("false")
        conn.close()
        return False


def add_user(username, firstname, lastname, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, firstname, lastname, password, score) VALUES (?, ?, ?, ?, 0)",
                   (username, firstname, lastname, password))
    conn.commit()
    conn.close()


def add_score_to_user(username, score):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET score = score + ? WHERE username = ?", (score, username))
    conn.commit()
    conn.close()


def get_score(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Check if the username exists in the database
    c.execute("SELECT score FROM users WHERE username = ?", (username,))
    return c.fetchone()

