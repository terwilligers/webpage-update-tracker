from flask import render_template, flash, redirect, url_for, request
from app import app
from app import db
from app.forms import RegistrationForm
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Website
from werkzeug.urls import url_parse

import flask
import sys
import json
import requests
import hashlib
import lxml
import time
import datetime
from lxml.html.clean import Cleaner
from datetime import datetime

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()   
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


def remove_script_tags(file):
    '''
    Input: string to remove script tags from
    Return: string with script tags removed
    '''
    cleaner = Cleaner(kill_tags = ['script'])
    result = cleaner.clean_html(file)
    return result

def get_date():
    ts = time.time()
    timestamp = datetime.datetime
    return timestamp

def add_url_to_database(new_hash, url):
    '''
    Creates an entry in the site_hashes table, containing the url and hash
    '''
    website = Website(url=url, url_hash=new_hash, user_id=current_user.id)
    db.session.add(website)
    db.session.commit()
    return True

def remove_url_from_database(url):
    '''
    Removes the row corresonding to the url from the database
    '''

    website = Website.query.filter_by(url=url, user_id=current_user.id).delete()
    db.session.commit()
    return True

def is_url_in_database(url):
    '''
    Checks if a url is contained in the database
    '''    
    website = Website.query.filter_by(user_id=current_user.id, url=url).first()
    if website:
        return True
    return False

def get_old_hash(url):
    website = Website.query.filter_by(url=url, user_id=current_user.id).first()
    return website.url_hash
 
def get_new_hash(url):
    '''
    Calcultes the md5 hash of the html file, located at the specified url
    '''
    try:
        new_file = requests.get(url).text
        new_file = remove_script_tags(new_file)
        new_hash = hashlib.md5(new_file.encode("utf-8")).hexdigest()
    except Exception as e:
        return False
    return new_hash

def update_hash(new_hash, url):
    '''
    Updates the hash of the url in the table
    '''
    website = Website.query.filter_by(url=url, user_id=current_user.id).first()
    website.url_hash = new_hash
    website.last_update = datetime.utcnow()
    db.session.commit()

def html_has_changed(url):
    '''
    Input: url- a string containing a url
    Return: a boolean stating whether the website's html has changed
            True if website was never seen before
    '''
    
    #Otherwise check hashes
    new_hash = get_new_hash(url)
    
    #add url and hash to the database if no entry
    in_database = is_url_in_database(url)
    if not in_database:
        add_url_to_database(new_hash, url)
        return True
    
    #otherwise we check whether hash has changed
    old_hash = get_old_hash(url)
    if old_hash == new_hash:
        has_changed = False
    else:
        has_changed = True
        # update entry in database
        update_hash(new_hash, url)
    return has_changed

@app.route("/add_url/<path:url>")
def add_url(url):
    results = {"message":False}
    if url == "null":
        return json.dumps(results)
    if is_url_in_database(url):
        results[message] = "You are already tracking this website"
        return json.dumps(results)
    
    new_hash = get_new_hash(url)
    if not new_hash:
        results[message] = "Sorry, you entered an invaled url"
        return json.dumps(results)
    
    #Returns the newly added entry in table
    add_url_to_database(new_hash, url)
    website = Website.query.filter_by(user_id=current_user.id, url=url).first()
    url = website.url
    updated = True
    timestamp = website.last_update.fromtimestamp(time.time()).strftime('%m/%d/%Y')
    results[url] = (updated, timestamp)
    return json.dumps(results)

@app.route("/remove_url/<path:url>")
def remove_url(url):
    message = ""
    if is_url_in_database(url):
        result = remove_url_from_database(url)
        if not result:
            message = "Oops, there was an error with your request"
    return json.dumps(message)

@app.route("/update_values")
def get_update_values():
    if not current_user.is_authenticated:
        return json.dumps({})
    websites = Website.query.filter_by(user_id=current_user.id)
    results = {}
    for site in websites:
        url = site.url
        updated = html_has_changed(url)
        timestamp = site.last_update.fromtimestamp(time.time()).strftime('%m/%d/%Y')
        results[url] = (updated, timestamp)
    return json.dumps(results)
        


