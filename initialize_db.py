import os
import sys
import pymysql
pymysql.install_as_MySQLdb()

# Required environment variables
required_vars = {
    'MYSQL_USER': 'Database username',
    'MYSQL_PASSWORD': 'Database password',
    'MYSQL_HOST': 'Database host',
    'MYSQL_DATABASE': 'Database name'
}

# Check for missing environment variables
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print("Error: Missing required environment variables:")
    for var in missing_vars:
        print(f"  - {var}: {required_vars[var]}")
    print("\nPlease set these environment variables before running the script.")
    print("Example (PowerShell):")
    print("$env:MYSQL_USER = 'your_username'")
    print("$env:MYSQL_PASSWORD = 'your_password'")
    print("$env:MYSQL_HOST = 'your_host'")
    print("$env:MYSQL_DATABASE = 'your_database'")
    sys.exit(1)

# Get database credentials from environment
db_user = os.getenv('MYSQL_USER')
db_pass = os.getenv('MYSQL_PASSWORD')
db_host = os.getenv('MYSQL_HOST')
db_name = os.getenv('MYSQL_DATABASE')

print(f"Connecting to database {db_name} on {db_host} as {db_user}")

# Set environment variable for database URL
os.environ['DATABASE_URL'] = f"mysql://{db_user}:{db_pass}@{db_host}/{db_name}"

# Now import the app after setting the environment variable
from app import app, db, User, init_cryptocurrencies
from werkzeug.security import generate_password_hash

def initialize_database():
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