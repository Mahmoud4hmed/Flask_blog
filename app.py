from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from flask_ckeditor import CKEditor
from flask_wtf.csrf import CSRFProtect

# Create a Flask instance and configure
app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ArmBar/Glitch01X'
app.config['MYSQL_DB'] = 'blog'
app.config['SECRET_KEY'] = 'My.Super*Seceret/Key'
db = MySQL(app)
app.secret_key = b'ArmBar/Glitch01X'
csrf = CSRFProtect(app)
time = datetime.now()

# Index Page
@app.route('/')
def index():
    cur = db.connection.cursor()
    cur.execute("SELECT * FROM posts ORDER BY date DESC")
    posts = cur.fetchall()
    return render_template('index.html', posts=posts)

# Profile
@app.route('/profile', methods=['GET', 'POST'])
def name():
    if session.get('id'):
        name = session.get('first_name') + ' ' + session.get('second_name')
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (session['id'],))
        users = cur.fetchall()
        if request.method == 'POST':
            first_name = request.form.get('first_name')
            second_name = request.form.get('second_name')
            username = request.form.get('username')
            username = username.lower()
            email = request.form.get('email')
            old_pass = request.form.get('old_password')
            new_pass = request.form.get('password')
            confirm_pass = request.form.get('confirm_password')
            
            if not username or not email or not first_name or not second_name:
                flash('Fill All Fields')
                return redirect(url_for('profile'))
            else:
                cur.execute("UPDATE users SET first_name = %s, second_name = %s, username = %s, email = %s WHERE id = %s", (first_name, second_name, username, email, session['id']))
                db.connection.commit()
                
            if new_pass or confirm_pass or old_pass:
                password = check_password_hash(users[0][5], old_pass)
                if not password:
                    flash('Incorrect Password')
                    return render_template('profile.html', name=name, users=users)
                elif new_pass != confirm_pass:
                    flash('Passwords do not match')
                    return render_template('profile.html', name=name, users=users)
                
            new_pass = generate_password_hash(new_pass)
            cur.execute("UPDATE users SET password = %s WHERE id = %s", (new_pass, session['id']))
            flash('Profile Updated')
            db.connection.commit()
            cur.close()
                
        return render_template('profile.html', name=name, users=users)
    else:
        return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if session.get('privilege') == 'owner' or session.get('privilege') == 'admin':
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users ORDER BY first_name ASC")
        count = cur.rowcount
        users = []
        users = cur.fetchall()
        return render_template('dashboard.html', users=users, count=count)
    else:
        return render_template('404.html')
    
# Search User
@app.route("/search", methods=['GET', 'POST'])
def search():
    if session.get('privilege') == 'owner' or session.get('privilege') == 'admin':
        users = []
        if request.method == 'POST':
            search = request.form.get('search')
            cur = db.connection.cursor()
            cur.execute("SELECT * FROM users WHERE first_name LIKE %s OR second_name LIKE %s OR username LIKE %s OR email LIKE %s OR privilege LIKE %s", ('%' + search + '%', '%' + search + '%', '%' + search + '%', '%' + search + '%', '%' + search + '%'))
            users = cur.fetchall()
            cur.close()
            return render_template('search.html', users=users)
    else:
        return render_template('404.html')
    
# Search Post
@app.route("/search_post", methods=['GET', 'POST'])
def search_post():
    users = []
    if request.method == 'POST':
        search = request.form.get('search')
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM posts WHERE title LIKE %s OR content LIKE %s", ('%' + search + '%', '%' + search + '%'))
        posts = cur.fetchall()
        cur.close()
        if posts == None:
            flash('No Posts Found')
            return render_template('index.html')
        return render_template('search_post.html', posts=posts)

# Add User
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    cur = db.connection.cursor()
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        second_name = request.form.get('second_name')
        usernameU = request.form.get('username')
        username = usernameU.lower()
        email = request.form.get('email')
        plain_pass = request.form.get('password')
        plain_confirm = request.form.get('confirm_password')
        if session.get('privilege') == 'owner' or session.get('privilege') == 'admin':
            privilege = request.form.get('btnn')
            
        if not username or not plain_pass:
            if session.get('id'):
                flash('Fill All Fields')
                return redirect(url_for('dashboard'))
            else:
                flash('Fill All Fields')
                return redirect(url_for('add_user'))
        elif plain_pass != plain_confirm:
            if session.get('id'):
                flash('Passwords do not match')
                return redirect(url_for('dashboard'))
            else:
                flash('Passwords do not match')
                return redirect(url_for('login'))
        
        exist = cur.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, username))
        if exist:
            flash("Email already exist")
            return render_template('add_user.html')
        
        password = generate_password_hash(plain_pass)
        if session.get('id') is None:
            privilege = "user"
        cur.execute("INSERT INTO users (first_name, second_name, username, email, password, date, privilege) VALUES (%s, %s, %s, %s, %s, %s, %s)", (first_name, second_name, username, email, password, time, privilege))
        db.connection.commit()
        cur.close()        
        if session.get('id'):
            flash('Account has been created')
            return redirect(url_for('dashboard'))
        else:
            flash('Account has been created')
            return redirect(url_for('login'))
    
    if session.get('id'):
        return render_template('dashboard.html')
    else:
        return render_template('add_user.html')
    
# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('id'):
        return redirect(url_for('index')) 
    
    session.clear()
    if request.method == 'POST':
        email = request.form.get('email')
        plain_pass = request.form.get('password')
        
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, email))
        users = cur.fetchall()
        if users and len(users) > 0:
            password = check_password_hash(users[0][5], plain_pass)
            if password: 
                session['id'] = users[0][0]
                session['username'] = users[0][3]
                session['first_name'] = users[0][1]
                session['second_name'] = users[0][2]
                session['email'] = users[0][4]
                session['privilege'] = users[0][7]
                return redirect(url_for('index'))
        else:
            flash('Invalid Credentials')
        
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Add Post
@app.route("/add-post", methods=['GET', 'POST'])
def add_post():
    if session.get('privilege') == 'owner' or session.get('privilege') == 'admin':
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('ckeditor')
            author = session['first_name'] + ' ' + session['second_name']
            author_id = session['id']
            slug = title.lower().replace(' ', '-')        
            cur = db.connection.cursor()
            cur.execute("INSERT INTO posts (title, content, author, slug, date, users_id) VALUES (%s, %s, %s, %s, %s, %s)", (title, content, author, slug, time, author_id))
            db.connection.commit()
            cur.close()
            flash('Post Added successfully!')
            return redirect(url_for('add_post'))
        
    
        return render_template('add_post.html')
    else:
        return render_template('404.html')

# View Post
@app.route("/posts/<int:id>")
def post(id):
    type = session.get('privilege')
    posts = 0
    cur = db.connection.cursor()
    cur.execute("SELECT * FROM posts WHERE id = %s", (id,))
    posts = cur.fetchone()
    cur.close()
    if posts is None:
        return render_template('404.html')
    return render_template('post.html', posts=posts, type=type) 

# Edit Users
@app.route("/update/<int:id>", methods=['GET', 'POST'])
def update(id):
    if session.get('privilege') == 'owner' or session.get('privilege') == 'admin': 
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (id,))
        users = cur.fetchall()
        if session['id'] != users[0][0] and users[0][7] != "user" and session['privilege'] != "owner":
            return render_template('404.html')
        option = users[0][7]

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            second_name = request.form.get('second_name')
            usernameU = request.form.get('username')
            username = usernameU.lower()
            option = request.form.get('btnn')
            email = request.form.get('email')
            plain_pass = request.form.get('password')
            if plain_pass == "":
                password = users[0][5]
            else:
                plain_pass = plain_pass
                password = generate_password_hash(plain_pass)
            if not username or not email or not first_name or not second_name:
                flash('Fill All Fields')
                return redirect(url_for('update', id=id))
            cur.execute("UPDATE users SET first_name = %s, second_name = %s, username = %s, email = %s, password = %s, privilege = %s WHERE id = %s", (first_name, second_name, username, email, password, option, id))
            db.connection.commit()
            cur.close()
            flash('User Was Updated!')
            return redirect(url_for('dashboard'))
        
        return render_template('update.html', users=users, option=option)
    else:
        return render_template('404.html')
    
# Delete Users
@app.route("/delete/<int:id>")
def delete(id):
    if session.get('privilege') == 'owner' or session.get('privilege') == 'admin':
        cur = db.connection.cursor() 
        cur.execute("DELETE from users WHERE id = %s", (id,))
        cur.connection.commit()
        cur.close()
        flash('Account has been deleted')
        return redirect(url_for('dashboard'))
    else:
        return render_template('404.html')

# Edit Post
@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit(id):
    if session.get('privilege') == 'owner' or session.get('privilege') == 'admin':
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM posts WHERE id = %s", (id,))
        posts = cur.fetchone()
        Author_id = posts[6]
        if session['id'] == Author_id or session['privilege'] == 'owner':
            if request.method == "POST":
                    title = request.form.get("title")
                    content = request.form.get("content")
                    cur.execute("UPDATE posts SET title = %s, content = %s WHERE id = %s", (title, content, id))
                    db.connection.commit()
                    cur.close()
                    flash('Post has been updated')
                    return redirect(url_for('index'))
            
            return render_template('edit.html', posts=posts)
        else:
            return render_template('404.html')
    else:
        return render_template('404.html')

# Delete Post
@app.route("/delete_post/<int:id>")
def delete_post(id):
    if session.get('privilege') == 'owner' or session.get('privilege') == 'admin':
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM posts WHERE id = %s", (id,))
        posts = cur.fetchone()
        Author_id = posts[6]
        if session['id'] == Author_id or session['privilege'] == 'owner':
            cur.execute("DELETE from posts WHERE id = %s", (id,))
            cur.connection.commit()
            cur.close()
            flash('Post has been deleted')
            return redirect(url_for('/'))
        else:
            return render_template('404.html')
    else:
        return render_template('404.html')

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
    
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)