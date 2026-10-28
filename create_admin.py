import getpass

from werkzeug.security import generate_password_hash
from app import create_database, connect_database


def main():
    # Create tables if they do not exist yet.
    create_database()

    db = connect_database()

    try:
        existing = db.execute(
            "SELECT COUNT(*) FROM admins"
        ).fetchone()[0]

        if existing > 0:
            print("An administrator account already exists.")
            print("No new account was created.")
            return

        username = input("Choose administrator username: ").strip()

        if not username or len(username) > 80:
            print("Username must contain 1 to 80 characters.")
            return

        password = getpass.getpass(
            "Choose a strong administrator password: "
        )
        confirm = getpass.getpass("Confirm password: ")

        if len(password) < 12:
            print("Use a password with at least 12 characters.")
            return

        if password != confirm:
            print("Passwords do not match.")
            return

        password_hash = generate_password_hash(password)

        db.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        db.commit()

        print("Administrator account created successfully.")

    except Exception as error:
        db.rollback()
        print("Could not create the administrator account.")
        print("Error:", error)

    finally:
        db.close()


if __name__ == "__main__":
    main()