from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class SystemConfig(db.Model):
    """System configuration table to store admin credentials and other settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255))
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_value(cls, key, default=None):
        config = cls.query.filter_by(key=key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, key, value, description=None):
        config = cls.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.description = description or config.description
        else:
            config = cls(key=key, value=value, description=description)
            db.session.add(config)
        db.session.commit()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    can_upload = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def init_admin():
        """Initialize admin user if not exists using credentials from database"""
        # Get admin credentials from system config
        admin_username = SystemConfig.get_value('ADMIN_USERNAME', 'admin')
        admin_password = SystemConfig.get_value('ADMIN_PASSWORD')
        admin_email = SystemConfig.get_value('ADMIN_EMAIL', 'admin@example.com')

        # Check if admin password is configured
        if not admin_password:
            print("Warning: Admin password not found in database configuration!")
            return

        # Create admin user if not exists
        admin = User.query.filter_by(username=admin_username).first()
        if not admin:
            admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created successfully with username: {admin_username}") 