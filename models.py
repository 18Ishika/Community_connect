from datetime import datetime
import pytz
from flask_sqlalchemy import SQLAlchemy

# Create db instance without app binding
db = SQLAlchemy()

# Set timezone to Asia/Kolkata
IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.now(IST)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=get_ist_time)
    
    # Relationships
    wishlists = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.name}>'


class Artisan(db.Model):
    __tablename__ = 'artisans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    craft_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    bio = db.Column(db.Text)
    contact = db.Column(db.String(50))
    image_url = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=get_ist_time)
    
    # Relationships
    products = db.relationship('Product', backref='artisan', lazy=True, cascade='all, delete-orphan')
    chats = db.relationship('Chat', backref='artisan', lazy=True, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='artisan', lazy=True, cascade='all, delete-orphan')
    
    def update_rating(self):
        """Calculate and update average rating"""
        if self.ratings:
            total = sum(r.rating for r in self.ratings)
            self.rating = round(total / len(self.ratings), 1)
            self.total_ratings = len(self.ratings)
        else:
            self.rating = 0.0
            self.total_ratings = 0
    
    def __repr__(self):
        return f'<Artisan {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=get_ist_time)
    
    # Foreign Keys
    artisan_id = db.Column(db.Integer, db.ForeignKey('artisans.id'), nullable=False)
    
    # Relationships
    wishlists = db.relationship('Wishlist', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'


class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=get_ist_time)
    
    def __repr__(self):
        return f'<Wishlist User:{self.user_id} Product:{self.product_id}>'


class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey('artisans.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    created_at = db.Column(db.DateTime, default=get_ist_time)
    updated_at = db.Column(db.DateTime, default=get_ist_time, onupdate=get_ist_time)
    
    # Ensure one rating per user per artisan
    __table_args__ = (db.UniqueConstraint('user_id', 'artisan_id', name='unique_user_artisan_rating'),)
    
    def __repr__(self):
        return f'<Rating User:{self.user_id} Artisan:{self.artisan_id} Stars:{self.rating}>'


class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey('artisans.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_ist_time)
    
    # Relationships
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Chat User:{self.user_id} Artisan:{self.artisan_id}>'


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'user' or 'artisan'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_ist_time)
    
    def __repr__(self):
        return f'<Message {self.sender_type}:{self.sender_id}>'