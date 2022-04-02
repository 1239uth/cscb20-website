from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


"""
    Session Config
"""
app.config['SECRET_KEY'] = 'secret_key' # TODO: use encryption!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignment3.db'


"""
    Database Config
"""
db = SQLAlchemy(app)



"""
    Routes & Rendering
"""


"""
Login
"""
@app.route('/login')
def login():
    page_name = "login"
    return render_template("login.html", page_name = page_name)

"""
Register
"""
@app.route('/register')
def register():
    page_name = "register"
    return render_template("register.html", page_name = page_name)


""" 
    Home
"""
@app.route('/')
@app.route('/home')
def root():
    page_name = "home"
    return render_template('home.html', page_name = page_name)


"""
    Announcements
"""
@app.route('/announcements')
def announcements():
    page_name = "announcements"
    return render_template("announcements.html", page_name = page_name)


"""
    Anon Feedback
"""
@app.route('/anonFeedback')
def anonFeedback():
    page_name = "anonFeedback"
    return render_template("anonFeedback.html", page_name = page_name)

"""
    Assignments
"""
@app.route('/assignments')
def assignments():
    page_name = "assignments"
    return render_template("assignments.html", page_name = page_name)


"""
    Instructors
"""
@app.route('/instructors')
def instructors():
    page_name = "instructors"
    return render_template("instructors.html", page_name = page_name)

"""
    Labs
"""
@app.route('/labs')
def labs():
    page_name = "labs"
    return render_template("labs.html", page_name = page_name)

"""
    Midterms
"""
@app.route('/midterms')
def midterms():
    page_name = "midterms"
    return render_template("midterms.html", page_name = page_name)


"""
    Weekly content
"""
@app.route('/weeklyContent')
def weeklyContent():
    page_name = "weeklyContent"
    return render_template("weeklyContent.html", page_name = page_name)



if __name__ == '__main__': 
    app.run(debug=True)