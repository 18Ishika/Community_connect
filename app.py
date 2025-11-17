from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz
import os

# Import db and models first
from models import db, User, Artisan, Product, Wishlist, Chat, Message, Rating

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kalamitra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize db with app
db.init_app(app)

# Timezone
IST = pytz.timezone('Asia/Kolkata')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'artisans'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)

# Create tables
with app.app_context():
    db.create_all()

# Helper function for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp','jfif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    artisans = Artisan.query.all()
    return render_template('index.html', artisans=artisans)

# User Authentication Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_type'] = 'user'
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Artisan Authentication Routes
@app.route('/artisan/signup', methods=['GET', 'POST'])
def new_artisan():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        craft_type = request.form.get('craft_type')
        location = request.form.get('location')
        bio = request.form.get('bio')
        contact = request.form.get('contact')
        
        if Artisan.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('new_artisan'))
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{email}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'artisans', filename)
                file.save(filepath)
                image_url = f'/static/uploads/artisans/{filename}'
        
        hashed_password = generate_password_hash(password)
        new_artisan = Artisan(
            name=name,
            email=email,
            password=hashed_password,
            craft_type=craft_type,
            location=location,
            bio=bio,
            contact=contact,
            image_url=image_url
        )
        db.session.add(new_artisan)
        db.session.commit()
        
        flash('Artisan account created successfully! Please login.', 'success')
        return redirect(url_for('artisan_login'))
    
    return render_template('new_artisan.html')

@app.route('/artisan/login', methods=['GET', 'POST'])
def artisan_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        artisan = Artisan.query.filter_by(email=email).first()
        
        if artisan and check_password_hash(artisan.password, password):
            session['user_id'] = artisan.id
            session['user_type'] = 'artisan'
            flash('Logged in successfully!', 'success')
            return redirect(url_for('artisan_dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('artisan_login.html')

# Artisan Dashboard
@app.route('/artisan/dashboard')
def artisan_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'artisan':
        flash('Please login as artisan first!', 'error')
        return redirect(url_for('artisan_login'))
    
    artisan = Artisan.query.get(session['user_id'])
    products = Product.query.filter_by(artisan_id=artisan.id).all()
    return render_template('artisan_dashboard.html', artisan=artisan, products=products)

# User Dashboard
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    wishlists = Wishlist.query.filter_by(user_id=user.id).all()
    wishlist_products = [Product.query.get(w.product_id) for w in wishlists]
    
    return render_template('user_dashboard.html', user=user, wishlist_products=wishlist_products)

# Product Management
@app.route('/artisan/product/add', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session.get('user_type') != 'artisan':
        flash('Please login as artisan first!', 'error')
        return redirect(url_for('artisan_login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        category = request.form.get('category')
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{session['user_id']}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'products', filename)
                file.save(filepath)
                image_url = f'/static/uploads/products/{filename}'
        
        new_product = Product(
            name=name,
            description=description,
            price=float(price),
            category=category,
            image_url=image_url,
            artisan_id=session['user_id']
        )
        db.session.add(new_product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('artisan_dashboard'))
    
    return render_template('add_product.html')

@app.route('/artisan/product/delete/<int:product_id>')
def delete_product(product_id):
    if 'user_id' not in session or session.get('user_type') != 'artisan':
        flash('Unauthorized!', 'error')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    if product.artisan_id != session['user_id']:
        flash('Unauthorized!', 'error')
        return redirect(url_for('artisan_dashboard'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('artisan_dashboard'))

# View Artisan Profile and Products
@app.route('/artisan/<int:artisan_id>')
def view_artisan_profile(artisan_id):
    artisan = Artisan.query.get_or_404(artisan_id)
    products = Product.query.filter_by(artisan_id=artisan_id).all()
    
    # Get wishlist product IDs for logged-in user
    wishlist_product_ids = []
    if 'user_id' in session and session.get('user_type') == 'user':
        wishlists = Wishlist.query.filter_by(user_id=session['user_id']).all()
        wishlist_product_ids = [w.product_id for w in wishlists]
    
    # Get user's rating for this artisan if exists
    user_rating = None
    if 'user_id' in session and session.get('user_type') == 'user':
        user_rating = Rating.query.filter_by(
            user_id=session['user_id'], 
            artisan_id=artisan_id
        ).first()
    
    return render_template('artisan_profile.html', 
                         artisan=artisan, 
                         products=products,
                         wishlist_product_ids=wishlist_product_ids,
                         user_rating=user_rating)

# Rating Routes
@app.route('/artisan/<int:artisan_id>/rate', methods=['POST'])
def rate_artisan(artisan_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    rating_value = request.form.get('rating')
    if not rating_value or not rating_value.isdigit() or int(rating_value) < 1 or int(rating_value) > 5:
        flash('Invalid rating value!', 'error')
        return redirect(url_for('view_artisan_profile', artisan_id=artisan_id))
    
    artisan = Artisan.query.get_or_404(artisan_id)
    
    # Check if user already rated this artisan
    existing_rating = Rating.query.filter_by(
        user_id=session['user_id'], 
        artisan_id=artisan_id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = int(rating_value)
        existing_rating.updated_at = datetime.now(IST)
        flash('Rating updated successfully!', 'success')
    else:
        # Create new rating
        new_rating = Rating(
            user_id=session['user_id'],
            artisan_id=artisan_id,
            rating=int(rating_value)
        )
        db.session.add(new_rating)
        flash('Rating added successfully!', 'success')
    
    # Update artisan's average rating
    artisan.update_rating()
    db.session.commit()
    
    return redirect(url_for('view_artisan_profile', artisan_id=artisan_id))

@app.route('/artisan/<int:artisan_id>/rating/delete')
def delete_rating(artisan_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Unauthorized!', 'error')
        return redirect(url_for('login'))
    
    rating = Rating.query.filter_by(
        user_id=session['user_id'],
        artisan_id=artisan_id
    ).first()
    
    if rating:
        db.session.delete(rating)
        artisan = Artisan.query.get(artisan_id)
        artisan.update_rating()
        db.session.commit()
        flash('Rating deleted successfully!', 'success')
    
    return redirect(url_for('view_artisan_profile', artisan_id=artisan_id))

# Wishlist Management
@app.route('/wishlist/add/<int:product_id>')
def add_to_wishlist(product_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    existing = Wishlist.query.filter_by(user_id=session['user_id'], product_id=product_id).first()
    if existing:
        flash('Product already in wishlist!', 'info')
    else:
        new_wishlist = Wishlist(user_id=session['user_id'], product_id=product_id)
        db.session.add(new_wishlist)
        db.session.commit()
        flash('Added to wishlist!', 'success')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/wishlist/remove/<int:product_id>')
def remove_from_wishlist(product_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    wishlist_item = Wishlist.query.filter_by(user_id=session['user_id'], product_id=product_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Removed from wishlist!', 'success')
    
    return redirect(request.referrer or url_for('user_dashboard'))

# Chat Routes
@app.route('/chat')
def chat_list():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if session.get('user_type') == 'user':
        chats = Chat.query.filter_by(user_id=session['user_id']).all()
    else:
        chats = Chat.query.filter_by(artisan_id=session['user_id']).all()
    
    return render_template('chat_list.html', chats=chats)

@app.route('/chat/<int:chat_id>')
def chat_view(chat_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    chat = Chat.query.get_or_404(chat_id)
    
    # Verify user has access to this chat
    if session.get('user_type') == 'user' and chat.user_id != session['user_id']:
        flash('Unauthorized!', 'error')
        return redirect(url_for('chat_list'))
    elif session.get('user_type') == 'artisan' and chat.artisan_id != session['user_id']:
        flash('Unauthorized!', 'error')
        return redirect(url_for('chat_list'))
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    return render_template('chat_view.html', chat=chat, messages=messages)

@app.route('/chat/start/<int:artisan_id>')
def start_chat(artisan_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Please login as user first!', 'error')
        return redirect(url_for('login'))
    
    # Check if chat already exists
    existing_chat = Chat.query.filter_by(user_id=session['user_id'], artisan_id=artisan_id).first()
    if existing_chat:
        return redirect(url_for('chat_view', chat_id=existing_chat.id))
    
    # Create new chat
    new_chat = Chat(user_id=session['user_id'], artisan_id=artisan_id)
    db.session.add(new_chat)
    db.session.commit()
    
    return redirect(url_for('chat_view', chat_id=new_chat.id))

@app.route('/chat/<int:chat_id>/send', methods=['POST'])
def send_message(chat_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    chat = Chat.query.get_or_404(chat_id)
    content = request.form.get('message')
    
    if not content:
        flash('Message cannot be empty!', 'error')
        return redirect(url_for('chat_view', chat_id=chat_id))
    
    new_message = Message(
        chat_id=chat_id,
        sender_id=session['user_id'],
        sender_type=session.get('user_type'),
        content=content
    )
    db.session.add(new_message)
    db.session.commit()
    
    return redirect(url_for('chat_view', chat_id=chat_id))
@app.route('/admin/dashboard')
def admin_dashboard():
    secret = request.args.get("key")
    if secret != "KEY_123":
        return "Unauthorized", 401

    users = User.query.all()
    artisans = Artisan.query.all()
    return render_template('admin_dashboard.html', users=users, artisans=artisans)

if __name__ == '__main__':
    app.run(debug=True)