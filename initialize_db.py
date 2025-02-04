import os
import pymysql
pymysql.install_as_MySQLdb()

from app import app, db, User, init_cryptocurrencies
from werkzeug.security import generate_password_hash

def initialize_database():
    # Get database credentials from environment
    db_user = os.getenv('MYSQL_USER')
    db_pass = os.getenv('MYSQL_PASSWORD')
    db_host = os.getenv('MYSQL_HOST')
    db_name = os.getenv('MYSQL_DATABASE')

    print(f"Connecting to database {db_name} on {db_host} as {db_user}")

    # Update the database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{db_user}:{db_pass}@{db_host}/{db_name}"

    with app.app_context():
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")

            # Create admin user if it doesn't exist
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("Creating admin user...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
                print("Username: admin")
                print("Password: admin123")
            else:
                print("Admin user already exists!")

            # Initialize cryptocurrencies
            print("\nInitializing cryptocurrencies...")
            init_cryptocurrencies()
            print("Database initialization complete!")

        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    initialize_database() 