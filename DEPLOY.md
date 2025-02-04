# Deployment Guide for Namecheap Shared Hosting

## 1. Initial Setup in cPanel

1. Log in to your Namecheap cPanel
2. Create a Python application:
   - Go to `Setup Python App` in cPanel
   - Choose Python 3.9 or later
   - Set application path to your domain or subdomain
   - Set application URL to your domain
   - Enable `passenger_wsgi.py`

## 2. Database Setup

1. Create MySQL Database:
   - Go to `MySQL Databases` in cPanel
   - Create a new database
   - Create a new user
   - Add user to database with all privileges

2. Note down these credentials:
   ```
   Database Name: your_cpanel_username_dbname
   Database User: your_cpanel_username_dbuser
   Database Password: your_password
   ```

## 3. Application Deployment

1. Connect to your hosting via SSH or File Manager

2. Navigate to your application directory:
   ```bash
   cd public_html   # or your application directory
   ```

3. Clone the repository:
   ```bash
   git clone https://github.com/trangman/crypto-portfolio.git .
   ```

4. Create and configure virtual environment:
   ```bash
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. Create and configure `.env` file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your database credentials:
   ```
   DATABASE_URL=mysql://dbuser:dbpassword@localhost/dbname
   SECRET_KEY=your-secure-secret-key
   SITE_URL=https://your-domain.com
   COMPANY_NAME=Your Company Name
   ```

6. Initialize the database:
   ```bash
   python init_db.py
   ```

## 4. Configure Passenger

1. Update `passenger_wsgi.py` with your Python path:
   ```python
   INTERP = "/home/username/public_html/venv/bin/python"
   ```

2. Set file permissions:
   ```bash
   chmod 755 passenger_wsgi.py
   chmod -R 755 venv
   chmod 644 .env
   ```

## 5. Application Access

1. Default admin credentials:
   - Username: `admin`
   - Password: `admin123`

2. **IMPORTANT**: Change the admin password after first login!

## 6. Troubleshooting

1. Check error logs in cPanel:
   - Go to `Error Log` in cPanel
   - Look for Python or application-specific errors

2. Common issues:
   - Database connection errors: Check credentials in `.env`
   - 500 errors: Check Python path in `passenger_wsgi.py`
   - Permission issues: Verify file permissions

## 7. Updates and Maintenance

To update the application:
```bash
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
touch tmp/restart.txt  # Restart the application
``` 