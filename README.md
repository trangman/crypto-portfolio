# Crypto Portfolio Tracker

A Flask-based web application for tracking cryptocurrency portfolios with multiple client accounts and admin management.

## Features

- Multi-user support with separate client accounts
- Admin dashboard for managing transactions
- Secure authentication system
- Beautiful UI with TailwindCSS
- PostgreSQL database for reliable data storage

## Environment Configuration

The application uses environment variables for configuration. To set up:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure the following required variables:
   - `SITE_URL`: Your website URL (no trailing slash)
   - `COMPANY_NAME`: Your company or application name
   - `SECRET_KEY`: A secure random key for Flask sessions
   - `DATABASE_URL`: Your database connection URL

3. Optional variables:
   - `APP_VERSION`: Application version number
   - `COINGECKO_API_KEY`: If using CoinGecko Pro API

## Prerequisites

- Python 3.8+
- PostgreSQL
- pip (Python package manager)

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto-portfolio
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL:
- Create a new PostgreSQL database named `crypto_portfolio`
- Update the `DATABASE_URL` in `.env` file with your PostgreSQL credentials

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Default Admin Account

- Username: admin
- Password: admin123

**Important:** Change the admin password after first login!

## Usage

1. Admin users can:
   - Add new transactions for any client
   - View all client portfolios
   - Manage user accounts

2. Client users can:
   - View their own portfolio
   - Track their transaction history
   - Monitor their investment performance

## Security

- Passwords are securely hashed using Werkzeug's security functions
- Session management with Flask-Login
- Environment variables for sensitive configuration
- CSRF protection for forms

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 