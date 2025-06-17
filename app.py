from flask import Flask, render_template, redirect, url_for, flash, session, request, current_app
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re 
import os 
from functools import wraps 
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename 
from datetime import datetime


UPLOAD_FOLDER_IMAGES = 'static/course_images'
UPLOAD_FOLDER_VIDEOS = 'static/course_videos'

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

def allowed_file(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

app = Flask(__name__)

app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
app.config['UPLOAD_FOLDER_VIDEOS'] = UPLOAD_FOLDER_VIDEOS

os.makedirs(app.config['UPLOAD_FOLDER_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_VIDEOS'], exist_ok=True)

app.config['SESSION_TYPE'] = 'filesystem'  # เลือกวิธีการเก็บ session ใน filesystem

Session(app)
app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'creditbank'

mysql = MySQL(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, role, first_name, last_name, username, email, profile_image=None):
        self.id = id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.profile_image = profile_image if profile_image else "default.png"
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
class Admin(UserMixin):
    def __init__(self, id, role, first_name, last_name, username, email, tel=None, gender=None, profile_image=None):
        self.id = id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.tel = tel
        self.gender = gender
        self.profile_image = profile_image if profile_image else "default.png"
# ---------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------
class Instructor(UserMixin):
    def __init__(self, id, role, first_name, last_name, username, email, tel=None, gender=None, profile_image=None):
        self.id = id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.tel = tel
        self.gender = gender
        self.profile_image = profile_image if profile_image else "default.png"
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Query the 'user' table for a regular user
    cursor.execute('SELECT * FROM user WHERE id = %s', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(id=user_data['id'], role=user_data['role'],
                    first_name=user_data['first_name'], last_name=user_data['last_name'],
                    username=user_data['username'], email=user_data['email'])

    # Query the 'admin' table for an admin user
    cursor.execute('SELECT * FROM admin WHERE id = %s', (user_id,))
    admin_data = cursor.fetchone()
    if admin_data:
        return Admin(id=admin_data['id'], role=admin_data['role'],
        first_name=admin_data['first_name'], last_name=admin_data['last_name'],
        username=admin_data['username'], email=admin_data['email'],
        gender=admin_data['gender'])

    # Query the 'instructor' table for an instructor user
    cursor.execute('SELECT * FROM instructor WHERE id = %s', (user_id,))
    instructor_data = cursor.fetchone()
    if instructor_data:
        return Instructor(id=instructor_data['id'], role=instructor_data['role'],
                           first_name=instructor_data['first_name'], last_name=instructor_data['last_name'],
                           username=instructor_data['username'], email=instructor_data['email'], tel=instructor_data['tel'])

    cursor.close()
    return None

# ---------------------------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("กรุณาเข้าสู่ระบบเพื่อเข้าสู่หน้านี้", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
# ---------------------------------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("กรุณาเข้าสู่ระบบเพื่อเข้าสู่หน้านี้", "warning")
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash("คุณไม่ได้รับอนุญาตให้เข้าถึงหน้านี้", "error")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------

def instructor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("กรุณาเข้าสู่ระบบเพื่อเข้าสู่หน้านี้", "warning")
            return redirect(url_for('login'))
        if current_user.role != 'instructor':
            flash("คุณไม่ได้รับอนุญาตให้เข้าถึงหน้านี้", "error")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function



# ---------------------------------------------------------------------------------------------

# Routes ต่าง ๆ
@app.route('/')
def home():
    return render_template('main/home.html')

@app.route('/about')
def about():
    return render_template('main/about.html')

@app.route('/course')
def course():
    return render_template('main/course.html')

@app.route('/contact')
def contact():
    return render_template('main/contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form.get('email_or_username')
        password = request.form.get('password')

        if not email_or_username or not password:
            flash('กรุณากรอกอีเมล / รหัสผ่าน', 'danger')
            return redirect(url_for('login'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # ตรวจสอบใน user
        cursor.execute('SELECT * FROM user WHERE username = %s OR email = %s', (email_or_username, email_or_username))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            user_obj = User(
                id=user['id'], role=user['role'],
                first_name=user['first_name'], last_name=user['last_name'],
                username=user['username'], email=user['email'],
            )
            login_user(user_obj)
            session.update({
                'loggedin': True,
                'id': user['id'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'username': user['username'],
                'email': user['email'],
                'profile_image': user.get('profile_image', 'default.jpg'),
            })
            flash('เข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('home'))

        # ตรวจสอบใน admin
        cursor.execute('SELECT * FROM admin WHERE username = %s OR email = %s', (email_or_username, email_or_username))
        admin = cursor.fetchone()
        if admin and check_password_hash(admin['password'], password):
            profile_image = admin.get('profile_image') or 'default.jpg'
            admin_obj = Admin(
                id=admin['id'], role=admin['role'],
                first_name=admin['first_name'], last_name=admin['last_name'],
                username=admin['username'], email=admin['email'], tel=admin['tel'],
                gender=admin.get('gender'),
                profile_image=profile_image
            )
            login_user(admin_obj)
            session.update({
                'loggedin': True,
                'id': admin['id'],
                'first_name': admin['first_name'],
                'last_name': admin['last_name'],
                'username': admin['username'],
                'email': admin['email'],
                'tel': admin['tel'],
                'profile_image': profile_image,
            })
            flash('ผู้ดูแลระบบเข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('admin_dashboard'))

        # ตรวจสอบใน instructor
        cursor.execute('SELECT * FROM instructor WHERE username = %s OR email = %s', (email_or_username, email_or_username))
        instructor = cursor.fetchone()
        if instructor and check_password_hash(instructor['password'], password):
            profile_image = instructor.get('profile_image') or 'default.jpg'
            instructor_obj = Instructor(
                id=instructor['id'], role='instructor',
                first_name=instructor['first_name'], last_name=instructor['last_name'],
                username=instructor['username'], email=instructor['email'], tel=instructor['tel'],
                profile_image=profile_image
            )
            login_user(instructor_obj)
            session.update({
                'loggedin': True,
                'id': instructor['id'],
                'first_name': instructor['first_name'],
                'last_name': instructor['last_name'],
                'username': instructor['username'],
                'email': instructor['email'],
                'tel': instructor['tel'],
                'profile_image': profile_image,
            })
            flash('ผู้สอนเข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('instructor_dashboard'))

        flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger')
        return redirect(url_for('login'))

    return render_template('main/login.html')




# # @app.route('/register', methods=['GET', 'POST'])
# # def register():
#     if request.method == 'POST':
#         # รับข้อมูลจากฟอร์ม
#         first_name = request.form.get('first_name')
#         last_name = request.form.get('last_name')
#         username = request.form.get('username').strip()
#         email = request.form.get('email').strip()
#         id_card = request.form.get('id_card').strip()
#         gender = request.form.get('gender')
#         password = request.form.get('password')
#         confirm_password = request.form.get('confirm_password')

#         # ตรวจสอบรหัสผ่าน
#         if password != confirm_password:
#             flash('Password และ Confirm Password ไม่ตรงกัน', 'danger')
#             return redirect(url_for('register'))

#         # ตรวจสอบข้อมูลซ้ำแบบแยก
#         if User.query.filter_by(email=email).first():
#             flash('Email นี้ถูกใช้ไปแล้ว', 'danger')
#             return redirect(url_for('register'))

#         if User.query.filter_by(username=username).first():
#             flash('Username นี้ถูกใช้ไปแล้ว', 'danger')
#             return redirect(url_for('register'))

#         if User.query.filter_by(id_card=id_card).first():
#             flash('รหัสบัตรประชาชนนี้ถูกใช้ไปแล้ว', 'danger')
#             return redirect(url_for('register'))

#         # เข้ารหัสรหัสผ่าน
#         hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

#         # สร้าง user ใหม่
#         new_user = User(
#             first_name=first_name,
#             last_name=last_name,
#             username=username,
#             email=email,
#             id_card=id_card,
#             gender=gender,
#             password=hashed_password,
#             role='user',
#             profile_image='default.jpg'
#         )

#         db.session.add(new_user)
#         try:
#             db.session.commit()
#             flash('สมัครสมาชิกสำเร็จ กรุณาล็อกอิน', 'success')
#             return redirect(url_for('register'))
#         except IntegrityError as e:
#             db.session.rollback()
#             flash('เกิดข้อผิดพลาดในการสมัครสมาชิก', 'danger')
#             print(f"IntegrityError: {e}")
#             return redirect(url_for('register'))

#     return render_template('main/register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        required_fields = ['username', 'password', 'confirm_password', 'email', 'first_name', 'last_name', 'gender', 'id_card']
        if all(field in request.form and request.form[field].strip() != '' for field in required_fields):
            first_name = request.form.get('first_name').strip()
            last_name = request.form.get('last_name').strip()
            username = request.form.get('username').strip()
            email = request.form.get('email').strip()
            id_card = request.form.get('id_card').strip()
            gender = request.form.get('gender')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
            user = cursor.fetchone()

            if user:
                flash('บัญชีมีอยู่แล้ว!', 'error')
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash('ที่อยู่อีเมลไม่ถูกต้อง!', 'error')
            elif not re.match(r'[A-Za-z0-9]+', username):
                flash('ชื่อผู้ใช้ต้องประกอบด้วยตัวอักษรและตัวเลขเท่านั้น!', 'error')
            elif password != confirm_password:
                flash('รหัสผ่านไม่ตรงกัน!', 'error')
            elif len(password) < 8:
                flash("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร", 'error')
            elif not any(c.isupper() for c in password):
                flash("รหัสผ่านต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว", 'error')
            elif not any(c.islower() for c in password):
                flash("รหัสผ่านต้องมีตัวอักษรพิมพ์เล็กอย่างน้อย 1 ตัว", 'error')
            elif not any(c.isdigit() for c in password):
                flash("รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 หลัก", 'error')
            elif gender not in ['Male', 'Female']:
                flash('กรุณาเลือกเพศที่ถูกต้อง!', 'error')
            else:
                hashed_password = generate_password_hash(password)
                created_at = datetime.now()

                cursor.execute(
                    'INSERT INTO user (first_name, last_name, email, username, id_card, gender, password, role, created_at) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (first_name, last_name, email, username, id_card, gender, hashed_password, 'user', created_at)
                )
                mysql.connection.commit()
                flash('คุณลงทะเบียนสำเร็จแล้ว!', 'success')
                return redirect(url_for('register'))
        else:
            flash('กรุณากรอกแบบฟอร์มให้ครบถ้วน!', 'error')
    
    return render_template('main/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/admin_dashboard.html')

@app.route('/admin/manage/admin', methods=['GET', 'POST'])
def manage_admins():
    if request.method == 'POST':
        # รับข้อมูลจากฟอร์ม
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        tel = request.form['tel']
        gender = request.form['gender']
        password = request.form['password']
        profile_image = request.files.get('profile_image')

        # แปลงรหัสผ่านเป็น hash
        hashed_password = generate_password_hash(password)

        filename = None
        if profile_image:
            filename = profile_image.filename
            upload_path = os.path.join(app.root_path, 'static/profile_images')
            os.makedirs(upload_path, exist_ok=True)
            profile_image.save(os.path.join(upload_path, filename))

        # บันทึกลงฐานข้อมูล
        cursor = mysql.connection.cursor()
        sql = """INSERT INTO admin (first_name, last_name, email, username, tel, gender, password, profile_image)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (first_name, last_name, email, username, tel, gender, hashed_password, filename))
        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มผู้ดูแลระบบสำเร็จ!', 'success')
        return redirect(url_for('manage_admins'))

    # ดึงข้อมูล admin
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM admin")
    admins = cursor.fetchall()
    cursor.close()

    return render_template('admin/manage_admins.html', admins=admins)

@app.route('/admin/edit/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM admin WHERE id = %s", (admin_id,))
    admin = cursor.fetchone()

    if not admin:
        flash('ไม่พบผู้ดูแลระบบนี้', 'danger')
        return redirect(url_for('manage_admins'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        tel = request.form['tel']
        gender = request.form['gender']
        password = request.form['password']

        # ถ้ามีการเปลี่ยนรหัสผ่าน ก็แปลง hash ใหม่
        if password:
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                UPDATE admin SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s, password=%s
                WHERE id=%s
            """, (first_name, last_name, email, username, tel, gender, hashed_password, admin_id))
        else:
            cursor.execute("""
                UPDATE admin SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s
                WHERE id=%s
            """, (first_name, last_name, email, username, tel, gender, admin_id))

        mysql.connection.commit()
        cursor.close()
        flash('แก้ไขข้อมูลผู้ดูแลระบบเรียบร้อยแล้ว', 'success')
        return redirect(url_for('manage_admins'))

    cursor.close()
    return render_template('admin/edit_admin.html', admin=admin)


@app.route('/admin/manage/admin/delete/<int:admin_id>', methods=['POST'])
def delete_admin(admin_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM admin WHERE id = %s", (admin_id,))
    mysql.connection.commit()
    cursor.close()
    flash('ลบผู้ดูแลระบบสำเร็จ!', 'success')
    return redirect(url_for('manage_admins'))



@app.route('/admin/manage/instructor', methods=['GET', 'POST'])
def manage_instructors():
    if request.method == 'POST':
        # รับข้อมูลจากฟอร์ม
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        tel = request.form['tel']
        gender = request.form['gender']
        password = request.form['password']
        profile_image = request.files.get('profile_image')

        # แปลงรหัสผ่านเป็น hash
        hashed_password = generate_password_hash(password)

        filename = None
        if profile_image:
            filename = profile_image.filename
            upload_path = os.path.join(app.root_path, 'static/profile_images')
            os.makedirs(upload_path, exist_ok=True)
            profile_image.save(os.path.join(upload_path, filename))

        # บันทึกลงฐานข้อมูลโดยใช้ cursor ของ flask_mysqldb
        cursor = mysql.connection.cursor()
        sql = """INSERT INTO instructor (first_name, last_name, email, username, tel, gender, password, profile_image)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (first_name, last_name, email, username, tel, gender, hashed_password, filename))
        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มผู้สอนสำเร็จ!', 'success')
        return redirect(url_for('manage_instructors'))

    # ดึงข้อมูลผู้สอนจากฐานข้อมูลเพื่อแสดงหน้าเว็บ (GET)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM instructor")
    instructors = cursor.fetchall()
    cursor.close()

    return render_template('admin/manage_instructors.html', instructors=instructors)

@app.route('/instructor/edit/<int:instructor_id>', methods=['GET', 'POST'])
def edit_instructor(instructor_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM instructor WHERE id = %s", (instructor_id,))
    instructor = cursor.fetchone()

    if not instructor:
        flash('ไม่พบผู้สอนนี้', 'danger')
        return redirect(url_for('manage_instructors'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        tel = request.form['tel']
        gender = request.form['gender']
        password = request.form['password']

        if password:
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                UPDATE instructor SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s, password=%s
                WHERE id=%s
            """, (first_name, last_name, email, username, tel, gender, hashed_password, instructor_id))
        else:
            cursor.execute("""
                UPDATE instructor SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s
                WHERE id=%s
            """, (first_name, last_name, email, username, tel, gender, instructor_id))

        mysql.connection.commit()
        cursor.close()
        flash('แก้ไขข้อมูลผู้สอนเรียบร้อยแล้ว', 'success')
        return redirect(url_for('manage_instructors'))

    cursor.close()
    return render_template('admin/edit_instructor.html', instructor=instructor)


@app.route('/admin/manage/instructor/delete/<int:instructor_id>', methods=['POST'])
def delete_instructor(instructor_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM instructor WHERE id = %s", (instructor_id,))
    mysql.connection.commit()
    cursor.close()
    flash('ลบผู้สอนสำเร็จ!', 'success')
    return redirect(url_for('manage_instructors'))



@app.route('/admin/manage/users', methods=['GET', 'POST'])
def manage_users():
    if request.method == 'POST':
        # รับข้อมูลจากฟอร์มเพิ่มผู้ใช้ใหม่
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        tel = request.form['tel']
        gender = request.form['gender']
        id_card = request.form['id_card']  # เพิ่มตรงนี้
        password = request.form['password']
        profile_image = request.files.get('profile_image')

        # แปลงรหัสผ่านเป็น hash
        hashed_password = generate_password_hash(password)

        filename = None
        if profile_image:
            filename = profile_image.filename
            upload_path = os.path.join(app.root_path, 'static/profile_images')
            os.makedirs(upload_path, exist_ok=True)
            profile_image.save(os.path.join(upload_path, filename))

        # บันทึกลงฐานข้อมูล user
        cursor = mysql.connection.cursor()
        sql = """INSERT INTO user (first_name, last_name, email, username, tel, gender, id_card, password, profile_image)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (first_name, last_name, email, username, tel, gender, id_card, hashed_password, filename))
        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มผู้ใช้สำเร็จ!', 'success')
        return redirect(url_for('manage_users'))

    # ดึงข้อมูลผู้ใช้จากฐานข้อมูล (GET)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    cursor.close()

    return render_template('admin/manage_users.html', users=users)

@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        flash('ไม่พบผู้ใช้คนนี้', 'danger')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        id_card = request.form['id_card']            # รับ id_card เพิ่ม
        email = request.form['email']
        username = request.form['username']
        tel = request.form['tel']
        gender = request.form['gender']
        password = request.form['password']

        if password:
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                UPDATE user SET first_name=%s, last_name=%s, id_card=%s, email=%s, username=%s, tel=%s, gender=%s, password=%s
                WHERE id=%s
            """, (first_name, last_name, id_card, email, username, tel, gender, hashed_password, user_id))
        else:
            cursor.execute("""
                UPDATE user SET first_name=%s, last_name=%s, id_card=%s, email=%s, username=%s, tel=%s, gender=%s
                WHERE id=%s
            """, (first_name, last_name, id_card, email, username, tel, gender, user_id))

        mysql.connection.commit()
        cursor.close()
        flash('แก้ไขข้อมูลผู้ใช้เรียบร้อยแล้ว', 'success')
        return redirect(url_for('manage_users'))

    cursor.close()
    return render_template('admin/edit_user.html', user=user)



@app.route('/admin/manage/user/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cursor.close()
    flash('ลบผู้ใช้สำเร็จ!', 'success')
    return redirect(url_for('manage_users'))


@app.route('/admin/attendance/students')
def attendance_students():
    # ดึงข้อมูล หรือแค่แสดงหน้าเปล่าก่อนได้
    return render_template('admin/attendance_students.html')

@app.route('/admin/attendance/exams')
def attendance_exams():
    # ดึงข้อมูล หรือแค่แสดงหน้าเปล่าก่อนได้
    return render_template('admin/attendance_exams.html')

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def category_list():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        category_name = request.form['category_name'].strip()

        # ตรวจสอบว่ามีชื่อนี้อยู่แล้วหรือยัง
        cursor.execute("SELECT * FROM categories WHERE name = %s", (category_name,))
        existing = cursor.fetchone()
        if existing:
            flash('หมวดหมู่นี้มีอยู่แล้ว', 'warning')
        else:
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
            mysql.connection.commit()
            flash('เพิ่มหมวดหมู่เรียบร้อยแล้ว', 'success')

    # ดึงข้อมูลจากตาราง categories
    cursor.execute("SELECT * FROM categories ORDER BY id DESC")
    categories = cursor.fetchall()
    cursor.close()

    return render_template('admin/category_list.html', categories=categories)

# แก้ไขหมวดหมู่
@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
    category = cursor.fetchone()

    if not category:
        flash('ไม่พบหมวดหมู่', 'danger')
        return redirect(url_for('category_list'))

    if request.method == 'POST':
        new_name = request.form['category_name'].strip()

        # ตรวจสอบชื่อซ้ำ (ยกเว้นตัวเอง)
        cursor.execute("SELECT * FROM categories WHERE name = %s AND id != %s", (new_name, category_id))
        existing = cursor.fetchone()
        if existing:
            flash('ชื่อหมวดหมู่นี้ถูกใช้ไปแล้ว', 'warning')
        else:
            cursor.execute("UPDATE categories SET name = %s WHERE id = %s", (new_name, category_id))
            mysql.connection.commit()
            flash('แก้ไขหมวดหมู่เรียบร้อยแล้ว', 'success')
            return redirect(url_for('category_list'))

    cursor.close()
    return render_template('admin/edit_category.html', category=category)


# ลบหมวดหมู่
@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    mysql.connection.commit()
    cursor.close()

    flash('ลบหมวดหมู่เรียบร้อยแล้ว', 'success')
    return redirect(url_for('category_list'))


@app.route('/admin/courses')
@login_required
def course_list():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = """
    SELECT
      c.id,
      c.title AS course_name,
      c.featured_image AS image,
      cat.id AS category_id,
      cat.name AS category_name,
      i.id AS instructor_id,
      i.first_name,
      i.last_name
    FROM courses c
    LEFT JOIN categories cat ON c.categories_id = cat.id
    LEFT JOIN instructor i ON c.instructor_id = i.id
    ORDER BY c.id DESC
    """
    
    cursor.execute(query)
    courses_raw = cursor.fetchall()
    cursor.close()
    
    courses = []
    for row in courses_raw:
        courses.append({
            'id': row['id'],
            'course_name': row['course_name'],
            'image': row['image'],
            'category': {
                'id': row['category_id'],
                'name': row['category_name']
            },
            'instructor': {
                'id': row['instructor_id'],
                'first_name': row['first_name'],
                'last_name': row['last_name']
            }
        })
    
    return render_template('admin/course_list.html', courses=courses)

# 🔸 แก้ไขหลักสูตร
@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        course_name = request.form['course_name']
        description = request.form['description']
        instructor_id = request.form['instructor_id']
        category_id = request.form['category_id']
        status = request.form['status']

        cur.execute("""
            UPDATE courses SET
                course_name = %s,
                description = %s,
                instructor_id = %s,
                category_id = %s,
                status = %s
            WHERE id = %s
        """, (course_name, description, instructor_id, category_id, status, course_id))

        mysql.connection.commit()
        flash('แก้ไขข้อมูลหลักสูตรเรียบร้อยแล้ว', 'success')
        return redirect(url_for('course_list'))

    # ดึงข้อมูลหลักสูตรเดิม
    cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cur.fetchone()

    # ดึง instructor จาก user ที่มี role เป็น instructor
    cur.execute("SELECT id, first_name, last_name FROM user WHERE role = 'instructor'")
    instructors = cur.fetchall()

    # ดึงหมวดหมู่จากตาราง categories
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    return render_template('admin/edit_course.html', course=course, instructors=instructors, categories=categories)


# 🔸 ลบหลักสูตร
@app.route('/delete_course/<int:course_id>', methods=['POST', 'GET'])
def delete_course(course_id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    mysql.connection.commit()

    flash('ลบหลักสูตรเรียบร้อยแล้ว', 'success')
    return redirect(url_for('course_list'))


@app.route('/admin/lesson/<int:course_id>')
@admin_required
def lesson(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
    SELECT lesson.*, courses.title AS course_name
    FROM lesson
    JOIN courses ON lesson.course_id = courses.id
    WHERE courses.id = %s
    ORDER BY lesson.lesson_date DESC
    """, (course_id,))

    lesson_data = cursor.fetchall()

    lessons = []
    for row in lesson_data:
        # แปลงวันที่ให้เป็น datetime object ถ้ายังไม่ใช่
        lesson_date = row['lesson_date']
        if isinstance(lesson_date, str):
            lesson_date = datetime.strptime(lesson_date, '%Y-%m-%d %H:%M:%S')

        lessons.append({
            'id': row['lesson_id'],
            'title': row['lesson_name'],
            'lesson_date': lesson_date,
            'course': {
                'course_name': row['course_name']
            }
        })

    cursor.close()
    return render_template('admin/lesson.html', lessons=lessons, course_id=course_id)


@app.route('/admin/add_lesson', methods=['GET', 'POST'])
@admin_required
def add_lesson():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        lesson_name = request.form.get('lesson_name')
        course_id = request.form.get('course_id')
        instructor_id = request.form.get('instructor_id')

        if not lesson_name or not course_id or not instructor_id:
            flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'danger')
            return redirect(url_for('add_lesson'))

        cursor.execute(
            'INSERT INTO lesson (lesson_name, course_id, instructor_id, lesson_date) VALUES (%s, %s, %s, NOW())',
            (lesson_name, course_id, instructor_id)
        )
        mysql.connection.commit()
        flash('เพิ่มบทเรียนสำเร็จ', 'success')
        return redirect(url_for('lesson', course_id=course_id))

    cursor.execute('SELECT id, title FROM courses WHERE status = "publish"')
    courses = cursor.fetchall()

    cursor.execute('SELECT id, first_name, last_name FROM instructor')
    instructors = cursor.fetchall()

    return render_template('admin/add_lesson.html', courses=courses, instructors=instructors)

@app.route('/admin/lesson/edit')
@admin_required
def edit_lesson():
    return render_template('admin/edit_lesson.html')

@app.route('/admin/lesson/delete/<int:lesson_id>', methods=['POST'])
@admin_required
def delete_lesson(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ ดึง course_id ก่อนลบ
    cursor.execute("SELECT course_id FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash("ไม่พบบทเรียนนี้", "danger")
        return redirect(url_for('dashboard'))

    course_id = lesson['course_id']

    try:
        # ✅ ลบโดยใช้ lesson_id
        cursor.execute("DELETE FROM lesson WHERE lesson_id = %s", (lesson_id,))
        mysql.connection.commit()
        flash("ลบบทเรียนเรียบร้อยแล้ว", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"เกิดข้อผิดพลาด: {str(e)}", "danger")

    # ✅ ส่งกลับไปยังหน้า lesson
    return redirect(url_for('lesson', course_id=course_id))





@app.route('/admin/lesson/<int:lesson_id>/quiz_and_video')
@admin_required
def quiz_and_video(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลบทเรียนหลัก
    cursor.execute("SELECT * FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        return redirect(url_for('admin_dashboard'))

    # 1. ดึงข้อมูลแบบทดสอบ (Quizzes) ที่ผูกกับบทเรียนนี้
    #    ต้อง JOIN ตาราง quiz_video กับตาราง quiz เพื่อดึงรายละเอียด quiz_name, quiz_type
    #    ***และ JOIN กับตาราง 'lesson' เพื่อดึง lesson_name***
    cursor.execute("""
        SELECT
            qv.video_id AS qv_id,
            qv.lesson_id,
            q.quiz_id,
            q.quiz_name,
            q.quiz_type,
            q.quiz_date,
            l.lesson_name -- <-- เพิ่มบรรทัดนี้เพื่อดึง lesson_name
        FROM quiz_video qv
        INNER JOIN quiz q ON qv.quiz_id = q.quiz_id
        INNER JOIN lesson l ON q.lesson_id = l.lesson_id -- <-- เพิ่ม INNER JOIN กับตาราง lesson
        WHERE qv.lesson_id = %s AND qv.quiz_id IS NOT NULL -- กรองเฉพาะรายการที่เป็นแบบทดสอบ
        ORDER BY qv.video_id ASC
    """, (lesson_id,))
    quizzes_for_lesson = cursor.fetchall()

    # 2. ดึงข้อมูลวิดีโอ (Videos) ที่ผูกกับบทเรียนนี้
    #    (ส่วนนี้ไม่จำเป็นต้องเปลี่ยนแปลงเพราะแสดง video.title ซึ่งอยู่ใน quiz_video อยู่แล้ว)
    cursor.execute("""
        SELECT
            qv.video_id AS video_id,
            qv.lesson_id,
            qv.title,
            qv.youtube_link,
            qv.description,
            qv.time_duration,
            qv.preview,
            qv.video_image
        FROM quiz_video qv
        WHERE qv.lesson_id = %s AND qv.quiz_id IS NULL -- กรองเฉพาะรายการที่เป็นวิดีโอ
        ORDER BY qv.video_id ASC
    """, (lesson_id,))
    videos_for_lesson = cursor.fetchall()

    cursor.close()

    return render_template('admin/quiz_and_video.html',
                           lesson=lesson,
                           quizzes=quizzes_for_lesson,
                           videos=videos_for_lesson)


@app.route('/admin/lesson/<int:lesson_id>/quiz/add', methods=['GET', 'POST'])
@admin_required
def add_quiz_to_lesson(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลบทเรียนที่กำลังจะเพิ่มแบบทดสอบให้
    cursor.execute("SELECT * FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    # --- ส่วนนี้ที่ต้องมีเพื่อให้ all_quizzes_data ถูกกำหนดค่า ---
    # ดึงข้อมูลแบบทดสอบทั้งหมดจากตาราง 'quiz'
    # เพื่อให้ได้ quiz_name และ quiz_type ไปแสดงใน dropdown และใช้ใน INSERT
    cursor.execute("""
        SELECT q.quiz_id, q.quiz_name, q.quiz_type, q.quiz_date, l.lesson_name
        FROM quiz q
        LEFT JOIN lesson l ON q.lesson_id = l.lesson_id
    """)
    all_quizzes_data = cursor.fetchall() # <-- บรรทัดนี้ที่ต้องอยู่ตรงนี้

    if request.method == 'POST':
        selected_quiz_id = request.form['quiz_id']

        selected_quiz_name = None
        # ลูปนี้จะทำงานได้เพราะ all_quizzes_data ถูกกำหนดค่าแล้ว
        for q_item in all_quizzes_data:
            if q_item['quiz_id'] == int(selected_quiz_id):
                selected_quiz_name = q_item['quiz_name']
                break

        if selected_quiz_name is None:
            flash('ไม่พบแบบทดสอบที่เลือก กรุณาลองใหม่อีกครั้ง', 'danger')
            cursor.close()
            return redirect(url_for('add_quiz_to_lesson', lesson_id=lesson_id))

        # --- ส่วน INSERT statement ที่ปรับปรุงล่าสุด ---
        cursor.execute("""
            INSERT INTO quiz_video (
                lesson_id,
                quiz_id,
                title,
                youtube_link,
                description,
                time_duration,
                preview,
                video_image
            ) VALUES (%s, %s, %s, '', '', '', '', '')
        """, (lesson_id, selected_quiz_id, selected_quiz_name))

        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มแบบทดสอบเรียบร้อยแล้ว', 'success')
        return redirect(url_for('quiz_and_video', lesson_id=lesson_id))

    cursor.close()
    return render_template('admin/add_quiz_to_lesson.html', lesson=lesson, available_quizzes=all_quizzes_data)




@app.route('/admin/lesson/<int:lesson_id>/add_video', methods=['GET', 'POST'])
@admin_required
def add_video(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงชื่อบทเรียนมาแสดง
    cursor.execute("SELECT * FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    # ดึงแบบทดสอบทั้งหมด
    cursor.execute("SELECT * FROM quiz")
    all_quizzes = cursor.fetchall()

    if request.method == 'POST':
        title = request.form['title']
        youtube_link = request.form['youtube_link']
        description = request.form.get('description')
        time_duration = request.form.get('time_duration')
        video_image = None

        # อัปโหลดรูปภาพ (ถ้ามี)
        if 'video_image' in request.files:
            file = request.files['video_image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.root_path, 'static/video_images', filename))
                video_image = filename

        # บันทึกข้อมูลลงฐานข้อมูล
        cursor.execute("""
            INSERT INTO quiz_video (title, youtube_link, description, time_duration, video_image, lesson_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, youtube_link, description, time_duration, video_image, lesson_id))
        mysql.connection.commit()
        cursor.close()
        flash('เพิ่มวิดีโอสำเร็จ', 'success')
        return redirect(url_for('quiz_and_video', lesson_id=lesson_id))

    cursor.close()
    return render_template('admin/add_video.html', lesson=lesson, all_quizzes=all_quizzes)


@app.route('/admin/video/<int:video_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_video(video_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM quiz_video WHERE video_id = %s", (video_id,))
    video = cursor.fetchone()

    if request.method == 'POST':
        title = request.form['title']
        youtube_link = request.form['youtube_link']
        description = request.form.get('description')
        time_duration = request.form.get('time_duration')

        # อัปเดตรายการวิดีโอ
        cursor.execute("""
            UPDATE quiz_video
            SET title=%s, youtube_link=%s, description=%s, time_duration=%s
            WHERE video_id=%s
        """, (title, youtube_link, description, time_duration, video_id))
        mysql.connection.commit()
        cursor.close()
        flash('แก้ไขวิดีโอเรียบร้อยแล้ว', 'success')
        return redirect(url_for('quiz_and_video', lesson_id=video['lesson_id']))

    cursor.close()
    return render_template('admin/edit_video.html', video=video)


@app.route('/admin/lesson_content/remove/<int:qv_entry_id>', methods=['POST'])
@admin_required
def remove_lesson_content(qv_entry_id):
    # --- แก้ไขตรงนี้: เพิ่ม MySQLdb.cursors.DictCursor ---
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    lesson_id_to_redirect = None

    print(f"\n--- DEBUG: Entering remove_lesson_content for qv_entry_id: {qv_entry_id} ---")

    try:
        cursor.execute("SELECT lesson_id FROM quiz_video WHERE video_id = %s", (qv_entry_id,))
        result = cursor.fetchone()
        print(f"DEBUG: SELECT result for qv_entry_id {qv_entry_id}: {result}")

        if result:
            # ตรงนี้จะใช้งานได้ถูกต้องแล้วเพราะ cursor เป็น DictCursor
            lesson_id_to_redirect = result['lesson_id']
            print(f"DEBUG: Found lesson_id: {lesson_id_to_redirect}. Attempting DELETE.")
            cursor.execute("DELETE FROM quiz_video WHERE video_id = %s", (qv_entry_id,))
            mysql.connection.commit()
            print("DEBUG: DELETE successful, commit done.")
            flash('ลบเนื้อหาออกจากบทเรียนเรียบร้อยแล้ว', 'success')
        else:
            print(f"DEBUG: No entry found for qv_entry_id {qv_entry_id}. Flashing 'danger' and redirecting to dashboard.")
            flash('ไม่พบรายการเนื้อหาที่ระบุเพื่อลบ', 'danger')
            return redirect(url_for('admin_dashboard'))

    except Exception as e:
        mysql.connection.rollback()
        print(f"ERROR: Exception during deletion: {e}")
        flash(f'เกิดข้อผิดพลาดในการลบเนื้อหา: {e}', 'danger')
    finally:
        cursor.close()
        print("DEBUG: Cursor closed.")

    if lesson_id_to_redirect:
        print(f"DEBUG: Redirecting to quiz_and_video for lesson_id: {lesson_id_to_redirect}")
        return redirect(url_for('quiz_and_video', lesson_id=lesson_id_to_redirect))
    else:
        print("DEBUG: Fallback redirect to admin_dashboard (lesson_id_to_redirect was None).")
        return redirect(url_for('admin_dashboard'))




@app.route('/admin/quiz/<int:lesson_id>')
@admin_required
def quiz_list(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT q.quiz_id, q.quiz_name, q.passing_percentage, q.quiz_date, q.quiz_type,
               l.lesson_name,
               (SELECT COUNT(*) FROM questions WHERE questions.quiz_id = q.quiz_id) AS question_count
        FROM quiz q
        JOIN lesson l ON q.lesson_id = l.lesson_id
        WHERE q.lesson_id = %s
        ORDER BY q.quiz_date DESC
    """, (lesson_id,))
    quizzes = cursor.fetchall()
    cursor.close()
    return render_template('admin/quiz_list.html', quizzes=quizzes, lesson_id=lesson_id)

# ฟอร์มเพิ่มแบบทดสอบ
@app.route('/admin/quiz/add', methods=['GET', 'POST'])
@admin_required
def add_quiz():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # ดึงบทเรียนทั้งหมดมาแสดงใน dropdown
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson")
    lessons = cursor.fetchall()

    if request.method == 'POST':
        quiz_name = request.form['quiz_name']
        quiz_type = request.form['quiz_type']
        passing_percentage = request.form['passing_percentage']
        lesson_id = request.form['lesson_id']  # รับค่าจาก dropdown

        cursor.execute("""
            INSERT INTO quiz (quiz_name, lesson_id, passing_percentage, quiz_date, quiz_type)
            VALUES (%s, %s, %s, NOW(), %s)
        """, (quiz_name, lesson_id, passing_percentage, quiz_type))
        mysql.connection.commit()
        cursor.close()
        flash('เพิ่มแบบทดสอบเรียบร้อยแล้ว', 'success')
        return redirect(url_for('quiz_list', lesson_id=lesson_id))

    cursor.close()
    return render_template('admin/add_quiz.html', lessons=lessons)



# ตัวอย่างหน้า edit และ delete (คุณสามารถเพิ่มเองได้ตามโครงสร้างนี้)
@app.route('/admin/quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
def edit_quiz(quiz_id):
    # ใส่โค้ดแก้ไขแบบทดสอบ
    pass

@app.route('/admin/quiz/delete/<int:quiz_id>', methods=['POST'])
@admin_required
def delete_quiz(quiz_id):
    cursor = mysql.connection.cursor()
    # เช็คว่ามี quiz นี้อยู่ไหม พร้อมดึง lesson_id
    cursor.execute("SELECT lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        flash('ไม่พบแบบทดสอบนี้', 'danger')
        cursor.close()
        return redirect(request.referrer or url_for('dashboard'))

    lesson_id = quiz[0]

    try:
        cursor.execute("DELETE FROM quiz WHERE quiz_id = %s", (quiz_id,))
        mysql.connection.commit()
        flash('ลบแบบทดสอบเรียบร้อยแล้ว', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('quiz_list', lesson_id=lesson_id))


@app.route('/admin/quiz/<int:quiz_id>/questions')
@admin_required
def quiz_questions(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT quiz_id, quiz_name, lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    cursor.execute("SELECT * FROM questions WHERE quiz_id = %s", (quiz_id,))
    questions = cursor.fetchall()
    cursor.close()

    return render_template('admin/quiz_questions.html', quiz=quiz, questions=questions, lesson_id=quiz['lesson_id'])


@app.route('/admin/quiz/<int:quiz_id>/questions/add', methods=['GET', 'POST'])
@admin_required
def add_question(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT quiz_id, quiz_name, lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    if request.method == 'POST':
        question_name = request.form['question_name']
        choice_a = request.form['choice_a']
        choice_b = request.form['choice_b']
        choice_c = request.form['choice_c']
        choice_d = request.form['choice_d']
        correct_answer = request.form['correct_answer'].lower()
        score = int(request.form['score'])

        def save_image(file_key):
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, 'static/question_images')
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    return filename
            return ''  # แก้ไขที่นี่

        question_image = save_image('question_image')
        choice_a_image = save_image('choice_a_image')
        choice_b_image = save_image('choice_b_image')
        choice_c_image = save_image('choice_c_image')
        choice_d_image = save_image('choice_d_image')

        cursor.execute("""
            INSERT INTO questions (
                quiz_id, question_name, choice_a, choice_b, choice_c, choice_d,
                correct_answer, score,
                question_image, choice_a_image, choice_b_image, choice_c_image, choice_d_image
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            quiz_id, question_name, choice_a, choice_b, choice_c, choice_d,
            correct_answer, score,
            question_image, choice_a_image, choice_b_image, choice_c_image, choice_d_image
        ))

        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มคำถามเรียบร้อยแล้ว', 'success')
        return redirect(url_for('quiz_questions', quiz_id=quiz_id))

    cursor.close()
    return render_template('admin/add_question.html', quiz=quiz, lesson_id=quiz['lesson_id'])






@app.route('/admin/question/<int:question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลคำถามจากฐานข้อมูล (เปลี่ยน question -> questions)
    cursor.execute("SELECT * FROM questions WHERE question_id = %s", (question_id,))
    question = cursor.fetchone()

    if not question:
        flash('ไม่พบคำถามนี้', 'danger')
        return redirect(url_for('quiz_list'))  # เปลี่ยนเป็นหน้า list quiz หรือหน้าอื่นตามต้องการ

    if request.method == 'POST':
        question_name = request.form['question_name']
        choice_a = request.form['choice_a']
        choice_b = request.form['choice_b']
        choice_c = request.form['choice_c']
        choice_d = request.form['choice_d']
        correct_answer = request.form['correct_answer']
        score = request.form['score']

        # อัปเดตข้อมูลในฐานข้อมูล (เปลี่ยน question -> questions)
        cursor.execute("""
            UPDATE questions SET question_name=%s, choice_a=%s, choice_b=%s, choice_c=%s,
            choice_d=%s, correct_answer=%s, score=%s WHERE question_id=%s
        """, (question_name, choice_a, choice_b, choice_c, choice_d, correct_answer, score, question_id))

        mysql.connection.commit()
        cursor.close()

        flash('แก้ไขคำถามเรียบร้อยแล้ว', 'success')
        return redirect(url_for('quiz_questions', quiz_id=question['quiz_id']))

    cursor.close()
    return render_template('admin/edit_question.html', question=question)

@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
def delete_question(question_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึง quiz_id ก่อนลบ เพื่อ redirect กลับหน้า quiz_questions
    cursor.execute("SELECT quiz_id FROM questions WHERE question_id = %s", (question_id,))
    result = cursor.fetchone()

    if not result:
        flash('ไม่พบคำถามนี้', 'danger')
        return redirect(url_for('quiz_list'))

    quiz_id = result['quiz_id']

    # ลบคำถาม
    cursor.execute("DELETE FROM questions WHERE question_id = %s", (question_id,))
    mysql.connection.commit()
    cursor.close()

    flash('ลบคำถามเรียบร้อยแล้ว', 'success')
    return redirect(url_for('quiz_questions', quiz_id=quiz_id))




@app.route('/admin/course/add', methods=['GET', 'POST'])
@login_required
def add_course():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึง instructor (รวมชื่อ + นามสกุล)
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS name FROM instructor")
    instructors = cursor.fetchall()

    # ดึง categories
    cursor.execute("SELECT id, name AS name FROM categories")
    categories = cursor.fetchall()

    if request.method == 'POST':
        course_name = request.form['course_name']
        instructor_id = request.form['instructor_id']
        category_id = request.form['category_id']
        description = request.form['description']
        status = request.form['status']


        # รูปภาพหลักสูตร
        course_image = request.files.get('course_image')
        image_filename = None
        if course_image and allowed_file(course_image.filename, ALLOWED_IMAGE_EXTENSIONS):
            image_filename = secure_filename(course_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_filename)
            course_image.save(image_path)

        # วิดีโอแนะนำ (ใช้ชื่อ 'featured_video' ให้ตรงกับฐานข้อมูล)
        featured_video = request.files.get('featured_video')
        video_filename = None
        if featured_video and allowed_file(featured_video.filename, ALLOWED_VIDEO_EXTENSIONS):
            video_filename = secure_filename(featured_video.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], video_filename)
            featured_video.save(video_path)

        # บันทึกลงฐานข้อมูล (เปลี่ยน intro_video => featured_video)
        cursor.execute("""
            INSERT INTO courses (title, instructor_id, categories_id, description, featured_image, featured_video, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (course_name, instructor_id, category_id, description, image_filename, video_filename, status))

        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มหลักสูตรเรียบร้อยแล้ว', 'success')
        return redirect(url_for('course_list'))

    cursor.close()
    return render_template('admin/add_course.html', instructors=instructors, categories=categories)



@app.route('/edit_profile')
@login_required
def edit_profile():
    if current_user.role == 'admin':
        return render_template('admin/edit_profile.html', user=current_user)
    elif current_user.role == 'instructor':
        return render_template('instructor/edit_profile.html', user=current_user)
    elif current_user.role == 'user':
        return render_template('user/edit_profile.html', user=current_user)
    else:
        flash("ไม่มีสิทธิ์เข้าถึง", "danger")
        return redirect(url_for('login'))

@app.route('/instructor/dashboard')
@instructor_required
def instructor_dashboard():
    return render_template('instructor/instructor_dashboard.html')

@app.route('/registered_courses')
def registered_courses():
    return render_template('instructor/registered_courses.html')

@app.route('/instructor/attendance/exams')
def instructor_attendance_exams():
    return render_template('instructor/attendance_exams.html')

@app.route('/instructor/categories')
def instructor_category():
    return render_template('instructor/category_list')

@app.route('/instructor/courses')
def instructor_courses():
    return render_template('instructor/course_list')

@app.route('/user/dashboard')
def user_dashboard():
    return render_template('user/user_dashboard.html')




if __name__ == '__main__':
    app.run(debug=True)
