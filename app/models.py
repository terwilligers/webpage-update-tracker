from app import login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    websites = db.relationship('Website', backref='tracker', lazy='dynamic')

    def __repr__(self):
        return '<User {},{}>'.format(self.username, self.id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_tracking_site(self, url):
        return self.websites.filter_by(user_id=self.id, url=url).count() > 0
    
    def add_site(self, url, new_hash):
        website = Website(url=url, url_hash=new_hash, user_id=self.id)
        db.session.add(website)
        db.session.commit()
    
    def remove_site(self, url):
        Website.query.filter_by(url=url, user_id=self.id).delete()
        db.session.commit()
        
    def get_old_hash(self, url):
        website = Website.query.filter_by(url=url, user_id=self.id).first()
        return website.url_hash
    
    def update_hash(self, url, new_hash):
        website = Website.query.filter_by(url=url, user_id=self.id).first()
        website.url_hash = new_hash
        website.last_update = datetime.utcnow()
        db.session.commit()
    
@login.user_loader
def load_user(id):
    return User.query.get(int(id))
    
class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(140))
    last_update = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    url_hash = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Website {},{}>'.format(self.url,self.user_id)