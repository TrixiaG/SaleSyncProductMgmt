from .models import User
from . import db
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, current_user, logout_user
import sqlite3, smtplib, datetime, secrets
from datetime import datetime, timedelta, timezone 
import re

login = Blueprint('login', __name__)

def validatePW(pw1):
    uppercase = re.search(r'[A-Z]', pw1)
    lowercase = re.search(r'[a-z]', pw1)
    number = re.search(r'\d', pw1)
    specialChar = re.search(r'[!@#$%^&*()-+=_?{}|~]', pw1)
    return uppercase and lowercase and number and specialChar and len(pw1) > 7

def validate2PW(pw1, pw2):
    return pw1 == pw2


def fetch_email(eid):
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM user WHERE eid = ?', (eid,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

def send_otp(email, otp):
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('qtdgregorio@tip.edu.ph', 'cdkojtaxskzksghf')
        message = f'Subject: TCFM SaleSync One-Time PIN\n\nYour OTP is {otp}.'
        server.sendmail('your_email@example.com', email, message)

@login.route('/', methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        eid = request.form.get('eid')
        password = request.form.get('password')
        
        user = User.query.filter_by(eid=eid).first()

        if user and check_password_hash(user.password, password):
            if user.access == 'Pending':
                flash('Your account still for approval.')
                return render_template("login.html", boolean=True)
            else:
                session['user_eid'] = user.eid 

                otp = str(secrets.randbelow(10000)).zfill(4)
                user_email = fetch_email(eid)
                send_otp(user_email, otp)
                
                session['otp'] = otp
                session['otp_time'] = datetime.now(timezone.utc)

                return render_template("otp.html", boolean=True)
        if not user or not check_password_hash(user.password, password):
            flash('Employee ID and/or Password invalid.', category='error')
            return render_template("login.html", boolean=True)

    else:
        return render_template("login.html", boolean=True)

#OTP
@login.route('/verify_otp', methods=['POST'])
def verify_otp():
    otp_entered = request.form.get('otp')
    if 'otp' in session and 'otp_time' in session:
        stored_otp = session['otp']
        otp_time = session['otp_time']
        current_time = datetime.now(timezone.utc)

        if otp_entered == stored_otp and (current_time - otp_time).seconds <= 300:
            session.pop('otp', None)
            session.pop('otp_time', None)
            
            user = User.query.filter_by(eid=session['user_eid']).first()
            if user:
                login_user(user, remember=True)
                return redirect(url_for('cashierops.user_cashier'))  
            else:
                flash('User not found.', category='error')
                return redirect(url_for('login.userLogin'))
        else:
            flash('Invalid OTP or OTP expired.', category='error')
    else:
        flash('Session expired. Please login again.', category='error')

    return redirect(url_for('login.userLogin'))


# FORGOT PASSWORD 
@login.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        
        eid = request.form.get('eid')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        user = User.query.filter_by(eid=eid).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password updated successfully.', category='success')
            return redirect(url_for('login.userLogin'))
        if not user:
            flash('EID not found.', category='error')
            return redirect(url_for('login.userLogin'))
        if not validatePW(new_password):
            flash('Please enter a valid password. Password must contain at least 1 lowercase and uppercase letter, 1 number, and 1 special character.', category='error')
            return redirect(url_for('login.userLogin'))

        if not validate2PW(new_password, confirm_password):
            flash('Passwords do not match.', category='error')
            return redirect(url_for('login.userLogin'))
        else:
            return redirect(url_for('login.userLogin'))

        return render_template('forgetpw.html', boolean=True)

@login.route('/logout')
@login_required
def userLogout():
    logout_user()
    return redirect(url_for('login.userLogin'))
