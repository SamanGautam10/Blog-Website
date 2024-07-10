from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename


local_server = True

'''reading json configuration files'''
with open('config.json', 'r') as configuration:
    params = json.load(configuration) ["params"]

app = Flask(__name__)
app.secret_key = 'Codingfreak'

'''configuring smtp to send mail'''
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = 'True',
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)

app.config['UPLOAD_FOLDER'] = params['upload_location']

mail = Mail(app)    #creating instance of Mail(app)

#Getting URI for the database
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

'''Table for contacts in database'''
class contacts(db.Model):
    SN = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)  
    message = db.Column(db.String(300), nullable=False)  # Corrected column name
    date = db.Column(db.String(20), nullable=True)


'''Table for post in database'''
class posts(db.Model):
    sn = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    title = db.Column(db.String(100), nullable = False)
    sub_title = db.Column(db.String(100), nullable = False)
    slug = db.Column(db.String(25), nullable = False)
    content = db.Column(db.String(1200), nullable = False)
    date = db.Column(db.String(20), nullable = True)
    img_file = db.Column(db.String(255), nullable = False)

@app.route("/")
def home():
    post = posts.query.filter_by().all() [0:params['no_of_post']]
    return render_template('index.html', param = params, posts = post)


@app.route("/about")
def about():
    return render_template('about.html', param = params)


@app.route("/contact", methods=['GET', 'POST'])
def contact_route():
    if request.method == 'POST':
        '''Add entry to the database'''
        namedb = request.form.get('nameform')
        phone = request.form.get('phone')  
        emaildb = request.form.get('email')
        message = request.form.get('message')

        '''Entries goes to the database'''
        entry = contacts(name=namedb, phone_num=phone, email=emaildb, message=message, date=datetime.now())  # Changed 'msg' to 'message'

        '''Updating the database entries'''
        db.session.add(entry)
        db.session.commit()

        '''Sending message to own mail'''
        mail.send_message("New Message From " + namedb, 
                          sender = emaildb, 
                          recipients = [params['gmail_user']],
                          body = message + "\n" + phone + "\n" + emaildb)
        
    return render_template('contact.html', param = params)

@app.route('/post/<string:post_slug>', methods=["GET"])
def post_route(post_slug):
    post = posts.query.filter_by(slug=post_slug).first()  #Slug for the url
    return render_template('post.html', param = params, post_passed = post)

@app.route('/post')
def sample_post():
    return render_template('sample.html', param = params, post_passed = posts)

'''Route for login page'''
@app.route('/dashboard', methods = ["GET", "POST"])
def dashboard():
    '''checking if user is already logged into the session'''
    if ('user' in session and session['user'] == params['admin_user']):
        post = posts.query.all()
        return render_template('dashboard.html', param = params, post_passed = post)


    if request.method == 'POST':
        username = request.form.get('adminemail')
        password = request.form.get('adminpassword')

        '''Checking username and password for admin panel'''
        if (username == params['admin_user'] and password == params['admin_password']):
            session['user'] = username
            post = posts.query.all()
            return render_template('dashboard.html', param = params, post_passed = post)

    else:
        return render_template('login.html', param = params)


'''Function to edit posts'''
@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):  #checks if user logged in is an admin
        if request.method=='POST':
            box_name = request.form.get('name')
            box_title = request.form.get('title')       #Fetching title from post db
            box_subtitle = request.form.get('subtitle')     
            box_slug = request.form.get('slug')         #slug of the post
            box_content = request.form.get('content')
            box_image = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = posts(name = box_name, title = box_title, sub_title = box_subtitle, slug = box_slug, content = box_content, img_file = box_image, date = date)
                db.session.add(post)
                db.session.commit()
            
            else:
                post = posts.query.filter_by(sn = sno).first()
                post.name = box_name
                post.title = box_title
                post.sub_title = box_subtitle
                post.slug = box_slug
                post.content = box_content
                post.img_file = box_image
                date = datetime.now()
                db.session.commit()
                return redirect('/edit/' + sno)
    
    post = posts.query.filter_by(sn = sno).first()
    return render_template('edit.html', param = params, post = post, sno=sno)


#File uploader end point
@app.route('/uploader', methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"

#Logout end point
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

#Deletion end point
@app.route('/delete/<string:sn>', methods=['GET', 'POST'])
def delete(sn):
    if ('user' in session and session['user'] == params['admin_user']):
        post = posts.query.filter_by(sn = sn).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


app.run(debug=True)
