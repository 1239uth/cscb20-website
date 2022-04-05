from datetime import datetime, timedelta
from urllib.request import Request
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


class Grade(db.Model):
    __tablename__ = 'Grade'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)
    ass_name = db.Column(db.String(30), nullable = False)
    score = db.Column(db.Float, nullable = False)
    weight = db.Column(db.Float, nullable = False)

    def __repr__(self):
        return f"Grade('{self.score}%')"

class RemarkRequest(db.Model):
    __tablename__ = 'RemarkRequest'
    id = db.Column(db.Integer, primary_key = True)
    grade_id = db.Column(db.Integer, db.ForeignKey('Grade.id'), nullable = False)
    details = db.Column(db.Text())
    closed = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"RemarkRequest('{self.details}')"

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
        name = request.form['regName'].capitalize()
        email = request.form['regEmail']
        password = bcrypt.generate_password_hash(
                            request.form['regPassword']).decode('utf-8')
        type = 'student'
        if 'regType' in request.form:
            type = 'instructor'

        # Prevents integrity error
        if user_exists(username, email):
            flash("A user with that username or email aleady exists.", "error")
            return redirect(url_for('register'))
        else:
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
    Student view only
"""
@app.route('/view/grades')
def view_grades():
    if 'username' not in session:
        return redirect(url_for('login'))

    if not session['is_student']:
        return redirect(url_for('root'))

    page_name = 'view_grades'
    grades = get_grades(session['username'])
    requests = []
    for grade in grades:
        remark_request = RemarkRequest.query.filter_by(grade_id = grade.id).first()

        if remark_request is None:
            requests.append("none")
        else:
            if remark_request.closed == 0:
                requests.append("ongoing")
            else:
                requests.append("closed")


    return render_template('view_grades.html', page_name = page_name, grades = grades, requests=requests)


@app.route('/remark_request/<grade_id>', methods=['POST'])
def submit_remark_request(grade_id):

    details = request.form['remarkContent']
    remark_request = RemarkRequest(grade_id = grade_id, details = details)
    db.session.add(remark_request)
    db.session.commit()

    flash("Your remark request was submitted", "success")
    return redirect(url_for('view_grades'))



"""
    View all students
    Instructor view only
"""
@app.route('/view/students')
def view_students():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['is_student']:
        return redirect(url_for('view_grades'))

    if request.method == 'GET':
        page_name = 'view_students'
        students = get_all_students()
        return render_template('view_students.html', page_name=page_name, students=students)





"""
    View and add student grades
    Instructor view only
"""
@app.route('/view/student/<username>', methods = ['GET', 'POST'])
def view_student(username):
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['is_student']:
        return redirect(url_for('view_grades'))

    student = User.query.filter_by(username = username).first()
    grades = Grade.query.filter_by(user_id = student.id).all()


    if request.method == 'POST':
        ass_name = request.form['gradeAssName']
        weight = request.form['gradeWeight']
        score = request.form['gradeScore']
        create_grade(ass_name, weight, score, student.id)

        flash("Grade added", "success")
        return redirect(url_for('view_student', username=username)) # do not remove

    page_name = "view_student"
    return render_template('view_student.html', page_name=page_name, student=student, grades=grades)



@app.route('/view/remark_requests')
def view_remark_requests():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['is_student']:
        return redirect(url_for('view_grades'))

    requests = RemarkRequest.query.all()

    # Paralel array
    grades = []
    students = []
    for request in requests:
        grade = Grade.query.filter_by(id = request.grade_id).first()
        grades.append(grade)

        student = User.query.filter_by(id = grade.user_id).first()
        students.append(student)


    page_name = 'view_remark_requests'
    return render_template('view_remark_requests.html',
                           page_name=page_name,
                           requests=requests,
                           grades=grades,
                           students=students)


@app.route('/close_request/<id>', methods = ['POST'])
def close_request(id):
    db.session.query(RemarkRequest).filter(RemarkRequest.id == id).update({'closed': 1})
    db.session.commit()
    return redirect(url_for('view_remark_requests'))

@app.route('/edit/student/<username>/grade/<grade_id>', methods = ['GET', 'POST'])
def edit_grade(username, grade_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['is_student']:
        return redirect(url_for('home'))

    if request.method == 'GET':
        page_name='edit_grade'
        grade=Grade.query.filter_by(id=grade_id).first()
        return render_template('edit_grade.html', page_name=page_name, username=username, grade_id=grade_id, grade=grade)

    if request.method == 'POST':
        new_name = request.form['newAssName']
        new_weight = request.form['newWeight']
        new_score = request.form['newScore']

        db.session.query(Grade).filter(Grade.id == grade_id).update({
            'ass_name': new_name,
            'weight': new_weight,
            'score': new_score
        })

        db.session.commit()

        return redirect(url_for('view_student', username=username))


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

def user_exists(username, email):
    username_match = User.query.filter_by(username = username).first()
    email_match = User.query.filter_by(email = email).first()

    return email_match is not None or username_match is not None

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

def get_all_students():
    return User.query.filter_by(type = 'student').all()


def create_grade(ass_name, weight, score, student_id):
    grade = Grade(ass_name=ass_name, weight=weight, score=score, user_id=student_id)
    db.session.add(grade)
    db.session.commit()

def get_grades(username):
    user = User.query.filter_by(username = username).first()
    return Grade.query.filter_by(user_id=user.id).all()


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