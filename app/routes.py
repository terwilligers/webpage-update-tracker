from flask import render_template, flash, redirect, url_for, request
from app import app
from app import db
from app.forms import RegistrationForm
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Website
from werkzeug.urls import url_parse
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.forms import ResetPasswordForm

import flask
import sys
import json
import requests
import hashlib
import lxml
import time
from lxml.html.clean import Cleaner
from datetime import datetime

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

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

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route("/add_url/<path:url>")
@login_required
def add_url(url):
    #message will be False unless there is an error with the request
    results = {"message":False}
    if url == "null":
        return json.dumps(results)
    if current_user.is_tracking_site(url):
        results["message"] = "You are already tracking this website"
        return json.dumps(results)
    
    new_hash = get_new_hash(url)
    if not new_hash:
        results["message"] = "Sorry, you entered an invaled url"
        return json.dumps(results)
    
    #Returns the newly added entry in table
    current_user.add_site(url, new_hash)
    website = Website.query.filter_by(user_id=current_user.id, url=url).first()
    url = website.url
    updated = True
    timestamp = website.get_readable_time()
    results[url] = (updated, timestamp)
    return json.dumps(results)

@app.route("/remove_url/<path:url>")
@login_required
def remove_url(url):
    message = ""
    if current_user.is_tracking_site(url):
        current_user.remove_site(url)
    return json.dumps(message)

@app.route("/update_values")
@login_required
def get_update_values():
    if not current_user.is_authenticated:
        return json.dumps({})
    websites = Website.query.filter_by(user_id=current_user.id)
    results = {}
    for site in websites:
        url = site.url
        updated = html_has_changed(url)
        timestamp = site.get_readable_time()
        results[url] = (updated, timestamp)
    return json.dumps(results)

def html_has_changed(url):
    '''
    Input: url- a string containing a url
    Return: a boolean stating whether the website's html has changed
            True if website was never seen before
    '''
    new_hash = get_new_hash(url)
    
    #add url and hash to the database if no entry
    if not current_user.is_tracking_site(url):
        current_user.add_site(url, new_hash)
        return True
    
    #otherwise we check whether hash has changed
    old_hash = current_user.get_old_hash(url)
    if old_hash == new_hash:
        has_changed = False
    else:
        has_changed = True
        current_user.update_hash(url, new_hash)
    return has_changed

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

def remove_script_tags(file):
    '''
    Input: string to remove script tags from
    Return: string with script tags removed
    '''
    cleaner = Cleaner(kill_tags = ['script'])
    result = cleaner.clean_html(file)
    return result
 

        


