from datetime import datetime, timedelta
from flask import Flask, render_template, url_for, flash, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


app = Flask(__name__)


"""
    Session Config
"""
app.config['SECRET_KEY'] = 'secret_key' # TODO: use encryption!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assignment3.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours = 2)


"""
    Encryption Config
"""
bcrypt = Bcrypt(app)

"""
    Database Config
"""
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key = True)
    type = db.Column(db.String(30), nullable = False, default='student')
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
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('root'))

    if request.method == 'GET':
        page_name = "login"
        return render_template("login.html", page_name = page_name)

    if request.method == 'POST':
        username = request.form['loginUsername']
        password = bcrypt.generate_password_hash(
                            request.form['loginPassword']).decode('utf-8')

        # Check auth
        if check_auth(username, password):
            session['username'] = username
            session.permanent = True
            return redirect(url_for('root'))
        else:
            flash("Please check your login credentials and try again!", "error")
            return render_template('login.html')

"""
Logout
"""
@app.route('/logout')
def logout():
    session.pop('username', default = None)
    return redirect(url_for('login'))

"""
Register
"""
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('root'))

    if request.method == 'GET':
        page_name = "register"
        return render_template("register.html", page_name = page_name)

    if request.method == 'POST':
        username = request.form['regUsername']
        name = request.form['regName']
        email = request.form['regEmail']
        password = bcrypt.generate_password_hash(
                            request.form['regPassword']).decode('utf-8')
        type = 'student'
        if 'regType' in request.form:
            type = 'instructor'


        # TODO: validate each field

        # Add to database
        create_user(username, name, email, password, type)

        # Flash & Render
        flash("You were successfully registered! Please log in.", "success")
        return redirect(url_for('login'))

# Can users see this page without being logged in? -
# I think they should, but we can ask on piazza
""" 
    Home
"""
@app.route('/')
@app.route('/home')
def root():
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        page_name = "home"
        return render_template('home.html', page_name = page_name)


"""
    Announcements
"""
@app.route('/announcements')
def announcements():
    if 'username' not in session:
        return redirect(url_for('login'))

    page_name = "announcements"
    return render_template("announcements.html", page_name = page_name)


"""
    Anon Feedback
"""
@app.route('/anonFeedback')
def anonFeedback():
    if 'username' not in session:
        return redirect(url_for('login'))

    page_name = "anonFeedback"
    return render_template("anonFeedback.html", page_name = page_name)

"""
    Assignments
"""
@app.route('/assignments')
def assignments():
    if 'username' not in session:
        return redirect(url_for('login'))

    page_name = "assignments"
    return render_template("assignments.html", page_name = page_name)


"""
    Instructors
"""
@app.route('/instructors')
def instructors():
    if 'username' not in session:
        return redirect(url_for('login'))

    page_name = "instructors"
    return render_template("instructors.html", page_name = page_name)

"""
    Labs
"""
@app.route('/labs')
def labs():
    if 'username' not in session:
        return redirect(url_for('login'))

    page_name = "labs"
    return render_template("labs.html", page_name = page_name)

"""
    Midterms
"""
@app.route('/midterms')
def midterms():
    if 'username' not in session:
        return redirect(url_for('login'))

    page_name = "midterms"
    return render_template("midterms.html", page_name = page_name)


"""
    Weekly content
"""
@app.route('/weeklyContent')
def weeklyContent():
    if 'username' not in session:
        return redirect(url_for('login'))

    page_name = "weeklyContent"
    return render_template("weeklyContent.html", page_name = page_name)

"""
Helper methods
"""

"""
    Precondition: all parameters are validated
"""
def create_user(username, name, email, password, type):
    user = User(username=username,
                name=name,
                email=email,
                password=password,
                type=type)
    db.session.add(user)
    db.session.commit()

def check_auth(username, password):

    user = User.query.filter_by(username = username).first()
    return not user or not bcrypt.check_password_hash(user.password, password)


"""
Run
"""
if __name__ == '__main__': 
    app.run(debug=True)