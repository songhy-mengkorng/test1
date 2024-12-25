from flask import Flask, render_template, request, redirect, url_for, flash,session
from werkzeug.utils import secure_filename 
import os
from flask_mysqldb import MySQL
import pymysql
import uuid
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'securety' 
bcrypt = Bcrypt(app) 
# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dashboard_7_8'

# File upload configuration
UPLOAD_FOLDER = 'static/img' 
ALLOWED_EXTENSIONS = {'jpg', 'png', 'gif', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Initialize MySQL
mysql = MySQL(app)

# Function to check allowed file extensions
def allowed_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to get a database connection
def get_database():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        ssl={'disable': True}
    )

@app.route('/', methods=['GET', 'POST'])
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard(): 
    if 'email' not in session:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        img = request.files['img']

        if img and allowed_extension(img.filename):
            # filename = secure_filename(img.filename)
            filename = str(uuid.uuid4())+'.'+img.filename.rsplit('.',1)[1].lower()
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(file_path)
        else:
            filename = None

        connection = get_database()
        cur = connection.cursor()
        cur.execute('INSERT INTO data (name, email, photo) VALUES (%s, %s, %s)', [name, email, filename])
        connection.commit()
        cur.close()
        connection.close()

        return redirect(url_for('dashboard'))     
    connection = get_database()
    cur = connection.cursor()
    cur.execute('SELECT * FROM data')
    data = cur.fetchall()
   
    connection = get_database()
    cur.execute('SELECT * FROM admin')  # Get profile data
    profile = cur.fetchone()  # Assuming only one admin profile, otherwise modify to handle multiple
    cur.close()
    connection.close()

    return render_template('dashboard.html', data=data , profile = profile)
@app.route('/delete/<int:id>', methods =['GET','POST'])
def delete(id):
    if 'email' not in session:
        return redirect(url_for('admin'))
    connection = get_database()
    cur = connection.cursor()
    cur.execute('SELECT photo FROM data WHERE id = %s',(id,))
    file_path = cur.fetchone()
    all_file = None
    if file_path and file_path[0]:
        all_file = os.path.join(app.config['UPLOAD_FOLDER'],file_path[0])
    else:
        file_path = None
    if all_file and os.path.exists(all_file):
        os.remove(all_file)
    cur = connection.cursor()
    cur.execute('DELETE FROM data WHERE id = %s',(id,))
    connection.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:id>', methods = ['GET','POST'])
def edit(id):
    if 'email' not in session:
        return redirect(url_for('admin'))
    connection = get_database()
    cur = connection.cursor()
    cur.execute('SELECT name ,email, photo FROM data WHERE id = %s',(id,))
    file_path = cur.fetchone()
    if not file_path:
        return redirect(url_for('dashboard'))
    name, email, img = file_path
    old_file = os.path.join(app.config['UPLOAD_FOLDER'], img) if img else None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        photo = request.files['img']
        
        #remove old file
        if photo and old_file and os.path.exists(old_file):
            os.remove(old_file)

        #add new file
        filename = img
        if photo and photo.filename:
            if allowed_extension(photo.filename):
                filename = str(uuid.uuid4())+'.'+photo.filename.rsplit('.',1)[1].lower()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
                photo.save(file_path)
            else:
                flash ('Not allowedn extensions')
            cur = connection.cursor()
            cur.execute('UPDATE data SET name = %s, email =%s, photo = %s WHERE id =%s',[
                name, email, filename, id
            ])
            connection.commit()
            return redirect(url_for('dashboard'))
        return render_template('edit.html')
# ============== profile ================
@app.route('/profile/<int:id>', methods = ['GET','POST'])
def profile(id):
    if 'email' not in session:
        return redirect(url_for('admin'))
    connection = get_database()
    cur = connection.cursor()
    cur.execute('SELECT photo FROM admin WHERE id = %s',(id,))
    file_path = cur.fetchone()

    if not file_path or not file_path[0]:
        return redirect(url_for('dashboard'))
    img = file_path[0]
    old_file = os.path.join(app.config['UPLOAD_FOLDER'], img) if img else None

    show = None
    if request.method == 'POST':
        photo = request.files['img']
    # ========= remove old file============
        if photo and old_file and os.path.exists(old_file):
            os.remove(old_file)
        filename = img

    #============ add new file ============
        if photo and photo.filename:
            if allowed_extension(photo.filename):
                filename = str(uuid. uuid4()) + '.'+photo.filename.rsplit('.',1)[1].lower()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(file_path)
            else:
                flash ('Not allowed extensions')
        cur.execute('UPDATE admin SET photo = %s WHERE id = %s',[filename,id])
        connection.commit()
        cur.execute('SELECT * FROM admin WHERE id = %s',(id,))
        show = cur.fetchone()
        connection.commit()
        cur.close()
        connection.close()
        return redirect(url_for('dashboard'))
    cur.execute('SELECT * FROM admin WHERE id = %s',(id,))
    show = cur.fetchone()
    cur.close()
    connection.close()
    return render_template('add_profile.html', show = show)

# @app.route('/register',methods =['GET','POST'])
# def register():
#     if request.method == 'POST':
#         email = request.form['email'] 
#         password = request.form['password']

#         connection = get_database()
#         cur = connection.cursor()
#         cur.execute('SELECT * FROM login WHERE email = %s',[email])
#         store_data = cur.fetchone() 
#         if store_data:
#             return redirect(url_for('login'))
#         hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
#         if email and hash_password:
#             connection = get_database()
#             cur = connection.cursor()
#             cur.execute('INSERT INTO login(email,password) VALUES(%s,%s)',[email,hash_password])
#             connection.commit()
#             return "success"
#         session['email'] = email
#     return render_template('register.html')
@app.route('/admin', methods =['GET','POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = get_database()
        cur = connection.cursor()
        cur.execute('SELECT password FROM login WHERE email = %s',[email])
        data = cur.fetchone()
        if data and bcrypt.check_password_hash(data[0], password):
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/logout', methods = ['GET','POST'])
def logout():
    session.pop('email',None)
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)