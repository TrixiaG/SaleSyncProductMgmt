#Routes
from flask import Blueprint, render_template

views = Blueprint('views', __name__)

@views.route('/login')
def loginPage():
    return render_template("login.html")

@views.route('/help')
def helpPage():
    return render_template("help.html")


@views.route('/aboutus')
def aboutUsPage():
    return render_template("aboutus.html")