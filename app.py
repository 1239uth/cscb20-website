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
    password = db.Column(db.String(100), nullable = False)
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
    score = db.Column(db.Integer)
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
    response = db.Column(db.Text())
    date_posted = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)


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
        password = request.form['loginPassword']

        # Check auth
        if check_auth(username, password):
            print("User/Passwd Matched: Logging the user in")
            session['username'] = username
            session['is_student'] = is_student(username)
            session.permanent = True
            return redirect(url_for('root'))
        else:
            flash("Please check your login credentials and try again!", "error")
            page_name = "login"
            return render_template('login.html', page_name = page_name)

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

        print(request.form['regPassword'])

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
        name = get_name(session['username']).capitalize()
        return render_template('home.html',
                               page_name = page_name,
                               name = name )


"""
    View Grades
"""
@app.route('/view/grades')
def view_grades():
    if 'username' not in session:
        return redirect(url_for('login'))

    if not session['is_student']:
        return redirect(url_for('add_grades'))

    page_name = 'view_grades'
    return render_template('view_grades.html', page_name = page_name)

"""
    Add Grades
"""
@app.route('/add/grades')
def add_grades():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['is_student']:
        return redirect(url_for('view_grades'))

    return ''

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
    Anonymous Feedback (Students)
"""
@app.route('/add/feedback', methods = ['GET', 'POST'])
def add_feedback():
    if 'username' not in session:
        return redirect(url_for('login'))

    if not session['is_student']:
        return redirect(url_for('view_feedback'))


    if request.method == 'GET':
        instructors = get_instructors()
        print(instructors)

        for instructor in instructors:
            print(instructor.name)

        page_name = "add_feedback"
        return render_template("add_feedback.html",
                               page_name = page_name,
                               questions = questions,
                               instructors = instructors)

    if request.method == 'POST':

        instructor_id = int(request.form['feedbackInstructor'])

        response = ""
        for i in range(4): # assumption: 4 questions in total
            response += "<h4>" + questions[i + 1] + "</h4>"
            response += "<p>" + request.form["feedbackQuestion" + str(i + 1)] + "</p>"

        # add response as feedback
        create_feedback(instructor_id, response)

        flash("Your feedback was successfully sent! Thank you", "success")

        return redirect(url_for('add_feedback'))

"""
    Anonymous Feedback (Instructors)
"""
@app.route('/view/feedback')
def view_feedback():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['is_student']:
        return redirect(url_for('add_feedback'))

    page_name = 'view_feedback'
    feedbacks = get_all_feedback(session['username'])
    return render_template("view_feedback.html", page_name = page_name, feedbacks = feedbacks)


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

"""
    Precondition: <password> is not hashed.
"""
def check_auth(username, password):
    user = User.query.filter_by(username = username).first()
    return user and bcrypt.check_password_hash(user.password, password)

# Edge case? bugs when no user in system
def get_name(username):
    if User.query.filter_by(username = username).first():
        return User.query.filter_by(username = username).first().name
    else:
        return "ERROR: No user found by that name"

def is_student(username):
    return User.query.filter_by(username = username).first().type == 'student'

def create_feedback(instructor_id, response):
    feedback = Feedback(instructor_id = instructor_id, response = response)
    db.session.add(feedback)
    db.session.commit()


"""
    Return all instructors
"""
def get_instructors():
    return User.query.filter_by(type = "instructor").all()


def get_all_feedback(username):
    return Feedback.query.filter_by(
        instructor_id = User.query.filter_by(username=username).first().id).all()


"""
Constants & Other variables
"""
# Can easily make this dynamic, but not a requirement.
# Using dictionary because it plays nicely with Jinja template
questions = {1: "What do you like about the instructor teaching?",
             2: "What do you recommend the instructor to do to improve their teaching?",
             3: "What do you like about the labs?",
             4: "What do you recommend the lab instructors to do to improve their lab teaching?"}


"""
Run
"""
if __name__ == '__main__': 
    app.run(debug=True)