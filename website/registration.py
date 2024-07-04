from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime
import random
import string


registration = Blueprint('registration', __name__)

def validateEmail(email):
    regex = re.compile(r'^[a-zA-Z0-9!#$%&\'*+\-/=?^_`{|}~.@]+$')
    return regex.match(email) is not None

def validateEID(EID):
    regex = re.compile(r'^[a-zA-Z][0-9]{7}$')
    return regex.match(EID) is not None

def validateName(name):
    trimmed_name = name.strip()
    return all(char.isalpha() or char.isspace() for char in trimmed_name)

def validatePW(pw1):
    uppercase = re.search(r'[A-Z]', pw1)
    lowercase = re.search(r'[a-z]', pw1)
    number = re.search(r'\d', pw1)
    specialChar = re.search(r'[!@#$%^&*()-+=_?{}|~]', pw1)
    return uppercase and lowercase and number and specialChar and len(pw1) > 7

def validate2PW(pw1, pw2):
    return pw1 == pw2

@registration.route('/sign-up', methods=['GET', 'POST'])
def userRegistration():

    def generate_eid():
        first_letter = random.choice(string.ascii_lowercase)
        random_digits = ''.join(random.choices(string.digits, k=7))
        return f"{first_letter}{random_digits}"

    generated_eid = generate_eid()

    if request.method == 'POST':
        email = request.form.get('emailAddress')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        pw1 = request.form.get('pw1')
        pw2 = request.form.get('pw2')
        bdaystr = request.form.get('bday')

        try:
            bday = datetime.strptime(bdaystr, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', category='error')
            return render_template("signup.html")
        
        #Check for Duplicate EID
        existing_userEID = User.query.filter_by(eid=generated_eid).first()
        if existing_userEID:
            flash('EID is already is already in use.', category='error')
            return render_template("signup.html")

        #Check for Duplicate Email
        existing_userEmail = User.query.filter_by(email=email).first()
        if existing_userEmail:
            flash('Email address is already in use.', category='error')
            return render_template("signup.html")
        

        if not validateEmail(email):
            flash('Email address is not valid.', category='error')
        elif not first_name:
            flash('First Name is required.', category='error')
        elif len(first_name) < 3:
            flash('First Name must be greater than 2 characters.', category='error')
        elif not validateName(first_name):
            flash('First Name must contain only alphabetic characters.', category='error')
        elif not last_name:
            flash('Last Name is required.', category='error')
        elif len(last_name) < 3:
            flash('Last Name must be greater than 2 characters.', category='error')
        elif not validateName(last_name):
            flash('Last Name must contain only alphabetic characters.', category='error')
        elif not pw1:
            flash('Password is required.', category='error')
        elif len(pw1) <= 7:
            flash('Password must be greater than 7 characters.', category='error')
        elif not validatePW(pw1):
            flash('Password must contain at least one special character, one number, one lowercase letter, and one uppercase letter.', category='error')
        elif not pw2:
            flash('Please confirm your password.', category='error')
        elif not validate2PW(pw1, pw2):
            flash('Passwords do not match.', category='error')
        elif not bdaystr:
            flash('Please select birthday.', category='error')
        else:
            new_user = User(eid=generated_eid, email=email, first_name=first_name, last_name=last_name, password=generate_password_hash(pw1, method='pbkdf2:sha256'), bday=bday, access='Pending')
            db.session.add(new_user)
            db.session.commit()        
            
            flash('Account creation request has been submitted. Please wait for admin&apos;s approval.', category='success')
            return render_template("login.html")

    return render_template('signup.html', generated_eid=generate_eid())