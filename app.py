import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import requests
import logging
from logging.handlers import RotatingFileHandler

# Flask app configuration
app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your-secure-secret-key-here')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database configuration for Namecheap
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql://root:@localhost/crypto_portfolio')

# Production settings
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Site configuration
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Investment Tracker')

# Set up logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

# Log configuration (excluding sensitive data)
app.logger.info(f"SITE_URL: {SITE_URL}")
app.logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Add context processor for footer variables
@app.context_processor
def inject_site_config():
    """Inject site configuration into all templates"""
    return {
        'site_url': SITE_URL,
        'company_name': COMPANY_NAME,
        'current_year': datetime.now().year,
        'app_version': os.getenv('APP_VERSION', '1.0.0')
    }

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Cryptocurrency(db.Model):
    __tablename__ = 'cryptocurrencies'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    price_24h_ago = db.Column(db.Float, nullable=True)
    price_change_24h = db.Column(db.Float, nullable=True)
    price_change_percentage_24h = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='cryptocurrency', lazy=True)

    def update_price(self):
        try:
            # Using CoinGecko API to get current price and 24h change
            response = requests.get(
                f'https://api.coingecko.com/api/v3/simple/price?ids={self.name.lower()}&vs_currencies=usd&include_24hr_change=true',
                headers={'accept': 'application/json'}
            )
            
            # Handle rate limiting
            if response.status_code == 429:  # Too Many Requests
                print(f"Rate limited when updating {self.symbol}. Waiting before retry...")
                return False
                
            if response.status_code == 200:
                data = response.json()
                coin_data = data[self.name.lower()]
                new_price = coin_data['usd']
                
                # Store the current price as price_24h_ago before updating
                if self.current_price != new_price:
                    self.price_24h_ago = self.current_price
                    self.current_price = new_price
                    self.price_change_24h = new_price - (self.price_24h_ago or new_price)
                    self.price_change_percentage_24h = coin_data.get('usd_24h_change', 0)
                    self.last_updated = datetime.utcnow()
                    db.session.commit()
                    print(f"Updated {self.symbol} price to ${new_price} (24h change: {self.price_change_percentage_24h:.2f}%)")
                return True
            else:
                print(f"Error updating {self.symbol}: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"Error updating price for {self.symbol}: {str(e)}")
            return False

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    crypto_id = db.Column(db.Integer, db.ForeignKey('cryptocurrencies.id'), nullable=False)
    investment_amount = db.Column(db.Float, nullable=False)  # Amount in USD
    price_at_time = db.Column(db.Float, nullable=False)  # Price of crypto at transaction time
    units = db.Column(db.Float, nullable=False)  # Calculated based on investment_amount and price
    transaction_type = db.Column(db.String(4), nullable=False)  # 'buy' or 'sell'
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def calculate_units(self):
        self.units = self.investment_amount / self.price_at_time

# Function to initialize cryptocurrencies
def init_cryptocurrencies():
    print("Initializing cryptocurrencies...")
    cryptocurrencies = [
        {'symbol': 'BTC', 'name': 'bitcoin'},
        {'symbol': 'ETH', 'name': 'ethereum'},
        {'symbol': 'BNB', 'name': 'binancecoin'},
        {'symbol': 'SOL', 'name': 'solana'},
        {'symbol': 'XRP', 'name': 'ripple'},
        {'symbol': 'ADA', 'name': 'cardano'},
        {'symbol': 'DOGE', 'name': 'dogecoin'},
        {'symbol': 'AVAX', 'name': 'avalanche-2'},
        {'symbol': 'DOT', 'name': 'polkadot'},
        {'symbol': 'MATIC', 'name': 'matic-network'}
    ]
    
    for crypto in cryptocurrencies:
        print(f"Checking {crypto['symbol']}...")
        existing = Cryptocurrency.query.filter_by(symbol=crypto['symbol']).first()
        if not existing:
            print(f"Adding {crypto['symbol']}...")
            new_crypto = Cryptocurrency(
                symbol=crypto['symbol'],
                name=crypto['name'],
                current_price=0.0
            )
            db.session.add(new_crypto)
            new_crypto.update_price()
            print(f"Added {crypto['symbol']} with price ${new_crypto.current_price}")
        else:
            print(f"{crypto['symbol']} already exists")
    
    db.session.commit()
    print("Cryptocurrency initialization complete")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Update the error handler
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error('Server Error: %s', str(error), exc_info=True)
    return render_template('error.html', error=error), 500

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error('Not Found: %s', str(error))
    return render_template('error.html', error=error), 404

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                flash('Please enter both email and password')
                return render_template('login.html')
            
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            
            flash('Invalid email or password')
            app.logger.warning(f'Failed login attempt for email: {email}')
            
        return render_template('login.html')
        
    except Exception as e:
        app.logger.error('Login error: %s', str(e), exc_info=True)
        db.session.rollback()
        flash('An error occurred during login. Please try again.')
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Ensure we have a fresh session
        db.session.rollback()
        
        # Log user role
        app.logger.info(f'User accessing dashboard: {current_user.username} (Admin: {current_user.is_admin})')
        
        # Get transactions based on user role
        if current_user.is_admin:
            app.logger.info('Admin user detected - fetching all transactions')
            transactions = Transaction.query.options(
                db.joinedload(Transaction.user),
                db.joinedload(Transaction.cryptocurrency)
            ).order_by(Transaction.timestamp.desc()).all()
            
            app.logger.info(f'Admin dashboard: Found {len(transactions)} total transactions')
            
            # Empty portfolio for admin users
            portfolio = []
            app.logger.info('Admin user - setting empty portfolio')
        else:
            app.logger.info('Regular user detected - fetching user transactions')
            transactions = Transaction.query.filter_by(user_id=current_user.id).options(
                db.joinedload(Transaction.cryptocurrency)
            ).order_by(Transaction.timestamp.desc()).all()
            
            app.logger.info(f'User dashboard: Found {len(transactions)} transactions for user {current_user.username}')
            
            # Calculate portfolio holdings for regular users
            portfolio = []
            holdings = {}
            
            for transaction in transactions:
                crypto = transaction.cryptocurrency
                if crypto.symbol not in holdings:
                    holdings[crypto.symbol] = {
                        'symbol': crypto.symbol,
                        'name': crypto.name,
                        'total_units': 0,
                        'total_investment': 0
                    }
                
                if transaction.transaction_type == 'buy':
                    holdings[crypto.symbol]['total_units'] += transaction.units
                    holdings[crypto.symbol]['total_investment'] += transaction.investment_amount
                else:  # sell
                    holdings[crypto.symbol]['total_units'] -= transaction.units
                    holdings[crypto.symbol]['total_investment'] -= transaction.investment_amount

            # Update crypto prices and calculate current values
            for symbol, holding in holdings.items():
                if holding['total_units'] > 0:  # Only show active holdings
                    crypto = Cryptocurrency.query.filter_by(symbol=symbol).first()
                    # Update price before calculating values
                    crypto.update_price()
                    
                    current_value = holding['total_units'] * crypto.current_price
                    avg_purchase_price = holding['total_investment'] / holding['total_units']
                    price_change_since_purchase = crypto.current_price - avg_purchase_price
                    
                    holding.update({
                        'current_price': crypto.current_price,
                        'current_value': current_value,
                        'profit_loss': current_value - holding['total_investment'],
                        'profit_loss_percentage': ((current_value - holding['total_investment']) / holding['total_investment']) * 100,
                        'price_change_percentage_24h': crypto.price_change_percentage_24h,
                        'price_change_percentage_since_purchase': (price_change_since_purchase / avg_purchase_price) * 100
                    })
                    portfolio.append(holding)
            
            # Commit the price updates
            db.session.commit()

        return render_template('dashboard.html', transactions=transactions, portfolio=portfolio)
    except Exception as e:
        app.logger.error(f"Error in dashboard route: {str(e)}", exc_info=True)
        db.session.rollback()
        flash('An error occurred while loading the dashboard')
        return redirect(url_for('error_handler'))

@app.route('/admin')
@login_required
def admin():
    try:
        if not current_user.is_admin:
            app.logger.warning('Non-admin user attempted to access admin page: %s', current_user.username)
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('dashboard'))
        
        # Ensure we have a fresh database session
        db.session.rollback()
        
        app.logger.info('Fetching users for admin page')
        users = User.query.all()
        app.logger.info('Successfully fetched %d users', len(users))
        
        # Direct SQL query to check transactions
        from sqlalchemy import text
        result = db.session.execute(text('SELECT COUNT(*) FROM transactions'))
        count = result.scalar()
        app.logger.info('Direct SQL query shows %d transactions in database', count)
        
        # Fetch all transactions with eager loading of relationships
        app.logger.info('Fetching all transactions')
        transactions = Transaction.query.options(
            db.joinedload(Transaction.user),
            db.joinedload(Transaction.cryptocurrency)
        ).order_by(Transaction.timestamp.desc()).all()
        app.logger.info('Successfully fetched %d transactions', len(transactions))
        
        # Log transaction details for debugging
        if transactions:
            app.logger.info('Transaction details:')
            for transaction in transactions:
                try:
                    app.logger.info(
                        'Transaction: ID=%d, User=%s, Type=%s, Crypto=%s, Amount=%.2f, Units=%.4f, Timestamp=%s', 
                        transaction.id,
                        transaction.user.username,
                        transaction.transaction_type,
                        transaction.cryptocurrency.symbol,
                        transaction.investment_amount,
                        transaction.units,
                        transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    )
                except Exception as e:
                    app.logger.error('Error logging transaction details: %s', str(e))
        else:
            app.logger.warning('No transactions found in database')
            
        return render_template('admin.html', users=users, transactions=transactions)
        
    except Exception as e:
        app.logger.error('Admin page error: %s', str(e), exc_info=True)
        db.session.rollback()
        flash('An error occurred while loading the admin page')
        return redirect(url_for('dashboard'))

@app.route('/transaction', methods=['GET', 'POST'])
@login_required
def transaction():
    if not current_user.is_admin:
        flash('Only administrators can add transactions')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Start with a fresh session
            db.session.rollback()
            
            user_id = request.form.get('user_id')
            crypto_id = request.form.get('crypto_id')
            investment_amount = float(request.form.get('investment_amount'))
            transaction_type = request.form.get('transaction_type')
            
            app.logger.info(f'Creating new transaction: user_id={user_id}, crypto_id={crypto_id}, amount={investment_amount}, type={transaction_type}')
            
            # Get the cryptocurrency and its current price
            crypto = Cryptocurrency.query.get(crypto_id)
            if not crypto:
                app.logger.error(f'Invalid cryptocurrency ID: {crypto_id}')
                flash('Invalid cryptocurrency selected')
                return redirect(url_for('transaction'))
            
            # Update crypto price before creating transaction
            crypto.update_price()
            
            # Create new transaction
            new_transaction = Transaction(
                user_id=user_id,
                crypto_id=crypto_id,
                investment_amount=investment_amount,
                price_at_time=crypto.current_price,
                transaction_type=transaction_type
            )
            
            # Calculate the number of units
            new_transaction.calculate_units()
            
            app.logger.info(f'Transaction details: price={crypto.current_price}, units={new_transaction.units}')
            
            db.session.add(new_transaction)
            db.session.commit()
            app.logger.info('Transaction added successfully')
            flash('Transaction added successfully')
            
            return redirect(url_for('admin'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error adding transaction: {str(e)}', exc_info=True)
            flash('Error adding transaction')
            return redirect(url_for('transaction'))
    
    try:
        # Get clients and cryptocurrencies with a fresh session
        db.session.rollback()
        
        users = User.query.filter_by(is_admin=False).all()
        cryptocurrencies = Cryptocurrency.query.all()
        
        # Update crypto prices
        for crypto in cryptocurrencies:
            crypto.update_price()
        db.session.commit()
        
        app.logger.info(f'Transaction form: Found {len(users)} clients and {len(cryptocurrencies)} cryptocurrencies')
        return render_template('transaction.html', users=users, cryptocurrencies=cryptocurrencies)
        
    except Exception as e:
        app.logger.error(f'Error loading transaction form: {str(e)}', exc_info=True)
        flash('Error loading transaction form')
        return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user is not logged in and public registration is disabled, redirect to login
    if not current_user.is_authenticated:
        flash('Please login to access this page')
        return redirect(url_for('login'))
    
    # If user is logged in but not admin, redirect to dashboard
    if current_user.is_authenticated and not current_user.is_admin:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password or not confirm_password:
            flash('All fields are required')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
            
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Client name already exists')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        try:
            # Create new client
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=False
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Client created successfully!')
            return redirect(url_for('admin'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during client creation')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/cryptocurrency')
@login_required
def cryptocurrency_list():
    try:
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('dashboard'))
            
        cryptocurrencies = Cryptocurrency.query.all()
        return render_template('cryptocurrency.html', cryptocurrencies=cryptocurrencies)
        
    except Exception as e:
        app.logger.error('Cryptocurrency page error: %s', str(e), exc_info=True)
        db.session.rollback()
        flash('An error occurred while loading the cryptocurrency page')
        return redirect(url_for('admin'))

@app.route('/cryptocurrency/add', methods=['POST'])
@login_required
def cryptocurrency_add():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    try:
        symbol = request.form.get('symbol').upper()
        name = request.form.get('name').lower()
        
        # Check if cryptocurrency already exists
        if Cryptocurrency.query.filter_by(symbol=symbol).first():
            flash('Cryptocurrency with this symbol already exists')
            return redirect(url_for('cryptocurrency_list'))
        
        # Create new cryptocurrency
        new_crypto = Cryptocurrency(
            symbol=symbol,
            name=name,
            current_price=0.0
        )
        db.session.add(new_crypto)
        db.session.commit()
        
        # Update price
        new_crypto.update_price()
        
        flash('Cryptocurrency added successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error adding cryptocurrency')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('cryptocurrency_list'))

@app.route('/cryptocurrency/<int:id>/edit', methods=['POST'])
@login_required
def cryptocurrency_edit(id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    try:
        crypto = Cryptocurrency.query.get_or_404(id)
        symbol = request.form.get('symbol').upper()
        name = request.form.get('name').lower()
        
        # Check if another cryptocurrency has the same symbol
        existing = Cryptocurrency.query.filter_by(symbol=symbol).first()
        if existing and existing.id != id:
            flash('Cryptocurrency with this symbol already exists')
            return redirect(url_for('cryptocurrency_list'))
        
        crypto.symbol = symbol
        crypto.name = name
        db.session.commit()
        
        # Update price with new name
        crypto.update_price()
        
        flash('Cryptocurrency updated successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error updating cryptocurrency')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('cryptocurrency_list'))

@app.route('/cryptocurrency/<int:id>/delete', methods=['POST'])
@login_required
def cryptocurrency_delete(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        crypto = Cryptocurrency.query.get_or_404(id)
        
        # Check if cryptocurrency has any transactions
        if crypto.transactions:
            return jsonify({
                'success': False,
                'message': 'Cannot delete cryptocurrency with existing transactions'
            }), 400
        
        db.session.delete(crypto)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error deleting cryptocurrency'}), 500

@app.route('/cryptocurrency/<int:id>/update_price', methods=['POST'])
@login_required
def cryptocurrency_update_price(id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        crypto = Cryptocurrency.query.get_or_404(id)
        success = crypto.update_price()
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating price'}), 500

@app.route('/api/prices', methods=['GET'])
@login_required
def get_prices():
    try:
        # Get all cryptocurrencies
        cryptos = Cryptocurrency.query.all()
        prices = {}
        for crypto in cryptos:
            # Update price from CoinGecko
            crypto.update_price()
            prices[crypto.symbol] = {
                'price': crypto.current_price,
                'last_updated': crypto.last_updated.strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        db.session.commit()
        return jsonify({'success': True, 'prices': prices})
    except Exception as e:
        db.session.rollback()
        print(f"Error fetching prices: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching prices'}), 500

@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    try:
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('dashboard'))
            
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            is_admin = request.form.get('is_admin') == 'on'
            
            # Check if username is taken by another user
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user_id:
                flash('Username already exists')
                return render_template('edit_user.html', user=user)
                
            # Check if email is taken by another user
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user_id:
                flash('Email already exists')
                return render_template('edit_user.html', user=user)
            
            # Update user information
            user.username = username
            user.email = email
            user.is_admin = is_admin
            
            # Update password if provided
            if new_password:
                if new_password != confirm_password:
                    flash('Passwords do not match')
                    return render_template('edit_user.html', user=user)
                user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            flash('User updated successfully')
            return redirect(url_for('admin'))
            
        return render_template('edit_user.html', user=user)
        
    except Exception as e:
        app.logger.error('Error editing user: %s', str(e), exc_info=True)
        db.session.rollback()
        flash('An error occurred while editing the user')
        return redirect(url_for('admin'))

@app.route('/user/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
def reset_user_password(user_id):
    try:
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('dashboard'))
            
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not new_password or not confirm_password:
                flash('Please enter both password fields')
                return render_template('reset_password.html', user=user)
                
            if new_password != confirm_password:
                flash('Passwords do not match')
                return render_template('reset_password.html', user=user)
            
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            flash('Password reset successfully')
            return redirect(url_for('admin'))
            
        return render_template('reset_password.html', user=user)
        
    except Exception as e:
        app.logger.error('Error resetting password: %s', str(e), exc_info=True)
        db.session.rollback()
        flash('An error occurred while resetting the password')
        return redirect(url_for('admin'))

# Add this at the bottom of the file
if __name__ == '__main__':
    with app.app_context():
        try:
            # Test database connection
            app.logger.info('Testing database connection...')
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            app.logger.info('Database connection successful')
            
            # Ensure tables exist
            app.logger.info('Checking database tables...')
            db.create_all()
            app.logger.info('Database tables verified')
            
            # Initialize cryptocurrencies
            app.logger.info('Checking cryptocurrencies...')
            init_cryptocurrencies()
            app.logger.info('Cryptocurrency initialization complete')
            
        except Exception as e:
            app.logger.error('Database initialization error: %s', str(e), exc_info=True)
            raise
    
    if os.getenv('FLASK_ENV') == 'development':
        app.run(debug=True)
    else:
        app.run(host='127.0.0.1', port=8000) 