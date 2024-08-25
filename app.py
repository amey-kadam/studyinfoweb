from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 

app.config['UPLOAD_FOLDER'] = 'files'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  
    is_admin = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))

with app.app_context():
    db.create_all() 

    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password=generate_password_hash('admin_password'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

@app.route('/')
@login_required
def index():
    return render_template('index.html', current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html', current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('register.html', current_user=current_user)

@app.route('/<category>')
@login_required
def category_page(category):
    if category not in ['FE', 'SE', 'TE', 'BE']:
        abort(404)

    # Define the subfolders
    subfolders = ['QUESTION PAPERS', 'DECODE', 'BOOKS']

    # Define the sub-subfolders
    sem_subfolders = ['sem1', 'sem2']

    # Get the path to the category's directory
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], category)
    
    # Create subfolders and sub-subfolders if they don't exist
    for folder in subfolders:
        folder_path = os.path.join(full_path, folder)
        for sem_folder in sem_subfolders:
            sem_folder_path = os.path.join(folder_path, sem_folder)
            os.makedirs(sem_folder_path, exist_ok=True)

    # List the subfolders
    contents = os.listdir(full_path)

    return render_template(f'{category.lower()}.html', category=category, contents=contents, is_admin=current_user.is_admin)

@app.route('/<category>/files/<path:subpath>')
@login_required
def browse_files(category, subpath):
    if category not in ['FE', 'SE', 'TE', 'BE']:
        abort(404)

    full_path = os.path.join(app.config['UPLOAD_FOLDER'], category, subpath)

    if not os.path.exists(full_path):
        abort(404)

    if os.path.isfile(full_path):
        return send_file(full_path, as_attachment=True)

    if os.path.isdir(full_path):
        contents = os.listdir(full_path)
        return render_template('browse.html',
                               contents=contents,
                               current_path=f'{category}/files/{subpath}',
                               category=category,
                               subpath=subpath,  # Add this line
                               is_admin=current_user.is_admin)
        
@app.route('/<category>/<path:subpath>/upload', methods=['POST'])
@login_required
def upload_file_to_subfolder(category, subpath):
    if not current_user.is_admin:
        abort(403)  # Forbidden

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
        
    if file:
        filename = secure_filename(file.filename)  
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], category, subpath, filename)
        
        # Create subfolder if it doesn't exist
        if not os.path.isdir(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
            
        file.save(file_path)
        flash('File uploaded successfully')
        
    return redirect(url_for('browse_files', category=category, subpath=subpath))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

if __name__ == '__main__':
    app.run(debug=True)
