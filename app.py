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

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    email = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(30), nullable = False)
    name = db.Column(db.String(30), nullable = False)
    grades = db.relationship('Grade', backref='author', lazy = True) # Student has grades
    feedback = db.relationship('Feedback', backref='author', lazy = True) # Instructor has feedback

    def __repr__(self):
        return f"User('{self.username}')"

class Assessment(db.Model):
    __tablename__ = 'Assessment'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), unique = True, nullable = False)
    type = db.Column(db.String(30), nullable = False)
    weight = db.Column(db.Integer, nullable = False)

    def __repr__(self):
        return f"Assessment('{self.name}', '{self.type}', '{self.weight}%')"

class Grade(db.Model):
    __tablename__ = 'Grade'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)
    ass_id = db.Column(db.Integer, db.ForeignKey('Assessment.id'), nullable = False)
    score = db.Column(db.Integer)

    def __repr__(self):
        return f"Grade('{self.score}%')"

class Feedback(db.Model):
    __tablename__ = 'Feedback'
    id = db.Column(db.Integer, primary_key = True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)
    response_1 = db.Column(db.Text())
    response_2 = db.Column(db.Text())
    response_3 = db.Column(db.Text())
    response_4 = db.Column(db.Text())



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