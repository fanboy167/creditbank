from flask import Flask, render_template, redirect, url_for, flash, session, request,  make_response, current_app, jsonify, send_file 
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
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, IntegerField
from wtforms.validators import DataRequired, URL, Optional, Length, NumberRange
import random
from fpdf import FPDF
import io
from PIL import Image, ImageDraw, ImageFont
import locale
import time


UPLOAD_FOLDER_COURSE_IMAGES = 'static/course_images'
UPLOAD_FOLDER_COURSE_VIDEOS = 'static/course_videos'
UPLOAD_FOLDER_PROFILE_IMAGES = 'static/profile_images'
UPLOAD_FOLDER_QUESTION_IMAGES = 'static/question_images'
UPLOAD_FOLDER_VIDEO_IMAGES = 'static/video_images'

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

def allowed_file(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

app = Flask(__name__) # ✅ app = Flask(__name__) ต้องอยู่ตรงนี้

locale.setlocale(locale.LC_TIME, 'th_TH.UTF-8')

# ✅ กำหนดค่าเข้า app.config หลัง app = Flask(__name__)
app.config['UPLOAD_FOLDER_COURSE_IMAGES'] = UPLOAD_FOLDER_COURSE_IMAGES
app.config['UPLOAD_FOLDER_COURSE_VIDEOS'] = UPLOAD_FOLDER_COURSE_VIDEOS
app.config['UPLOAD_FOLDER_PROFILE_IMAGES'] = UPLOAD_FOLDER_PROFILE_IMAGES
app.config['UPLOAD_FOLDER_QUESTION_IMAGES'] = UPLOAD_FOLDER_QUESTION_IMAGES
app.config['UPLOAD_FOLDER_VIDEO_IMAGES'] = UPLOAD_FOLDER_VIDEO_IMAGES

# ✅ สร้างโฟลเดอร์หลังกำหนดใน app.config
os.makedirs(app.config['UPLOAD_FOLDER_COURSE_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_PROFILE_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_QUESTION_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_VIDEO_IMAGES'], exist_ok=True)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
app.secret_key = 'your_strong_secret_key_here'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'creditbank'

mysql = MySQL(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class CourseForTemplate: # คลาสย่อยสำหรับข้อมูลคอร์ส
    def __init__(self, id, name):
        self.id = id
        self.course_name = name

class LessonForTemplate: # คลาสสำหรับข้อมูลบทเรียน
    def __init__(self, lesson_id, lesson_name, course_id, course_name):
        self.id = lesson_id # ให้มี .id สำหรับ url_for และการอ้างอิงทั่วไป
        self.lesson_id = lesson_id # เก็บ original lesson_id ไว้ด้วย
        self.title = lesson_name # แมป lesson_name จาก DB ไปยัง .title เพื่อให้เทมเพลตเข้าถึงได้
        self.course = CourseForTemplate(course_id, course_name) # มี .course.course_name

# ---------------------------------------------------------------------------------------------

class QuizForm(FlaskForm): # ✅ QuizForm สำหรับแก้ไขแบบทดสอบจริง
    quiz_name = StringField('ชื่อแบบทดสอบ', validators=[DataRequired(message="กรุณาระบุชื่อแบบทดสอบ"), Length(max=255)])
    quiz_type = SelectField('ประเภทแบบทดสอบ', coerce=str, validators=[DataRequired(message="กรุณาเลือกประเภท")])
    passing_percentage = IntegerField('เปอร์เซ็นต์ผ่าน', validators=[DataRequired(message="กรุณาระบุเปอร์เซ็นต์ผ่าน"), NumberRange(min=0, max=100, message="ต้องอยู่ระหว่าง 0-100")])
    lesson_id = SelectField('บทเรียนที่เกี่ยวข้อง', coerce=int, validators=[DataRequired(message="กรุณาเลือกบทเรียน")])
    # ✅ ลบ select_quiz_id ออกจาก QuizForm นี้แล้ว
    
class QuizSelectionForm(FlaskForm): # ✅ QuizSelectionForm สำหรับเลือกแบบทดสอบ
    select_quiz_id = SelectField('เลือกแบบทดสอบที่ต้องการแก้ไข', coerce=int, validators=[DataRequired(message="กรุณาเลือกแบบทดสอบ")])
# ---------------------------------------------------------------------------------------------

class LessonForm(FlaskForm):
    course_id = SelectField('หลักสูตร', coerce=int, validators=[DataRequired(message="กรุณาเลือกหลักสูตร")])
    instructor_id = SelectField('ผู้สอน', coerce=int, validators=[DataRequired(message="กรุณาเลือกผู้สอน")])
    title = StringField('ชื่อบทเรียน', validators=[DataRequired(message="กรุณาระบุชื่อบทเรียน")])
    description = TextAreaField('รายละเอียดบทเรียน', validators=[Optional()])
    lesson_date = DateField('วันที่สร้างบทเรียน', format='%Y-%m-%d', validators=[Optional()])
    
# ---------------------------------------------------------------------------------------------


class User(UserMixin):
    # แก้ไขโดยการเพิ่ม id_card=None และ gender=None เข้าไปในพารามิเตอร์
    def __init__(self, id, role, first_name, last_name, username, email, profile_image=None, id_card=None, gender=None):
        self.id = id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.profile_image = profile_image if profile_image else "default.png"
        
        # เพิ่ม 2 บรรทัดนี้เพื่อเก็บค่าที่รับมา
        self.id_card = id_card
        self.gender = gender

        # เพิ่มเวอร์ชันสำหรับบังคับให้เบราว์เซอร์โหลดรูปใหม่
        self.profile_image_version = datetime.now().timestamp()
        
    def get_id(self):
        return str(self.id)
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
        self.profile_image_version = datetime.now().timestamp() # ✅ เพิ่ม version สำหรับ cache busting
    def get_id(self):
        return str(self.id)
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
        self.profile_image_version = datetime.now().timestamp() # ✅ เพิ่ม version สำหรับ cache busting
    def get_id(self):
        return str(self.id)
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    print(f"\n--- DEBUG: กำลังโหลดผู้ใช้สำหรับ user_id: {user_id} ---")

    # 1. ตรวจสอบในตาราง Admin ก่อน
    cursor.execute('SELECT id, username, email, role, first_name, last_name, tel, gender, profile_image FROM admin WHERE id = %s', (user_id,))
    admin_data = cursor.fetchone()
    if admin_data:
        db_role = str(admin_data.get('role', 'admin')).strip()
        print(f"DEBUG: พบผู้ใช้ในตาราง 'admin'. Role: '{db_role}'")
        admin_obj = Admin(
            id=admin_data['id'], role=db_role,
            first_name=admin_data['first_name'], last_name=admin_data['last_name'],
            username=admin_data['username'], email=admin_data['email'],
            tel=admin_data.get('tel'), gender=admin_data.get('gender'),
            profile_image=admin_data.get('profile_image')
        )
        return admin_obj

    # 2. ตรวจสอบในตาราง Instructor
    cursor.execute('SELECT id, username, email, role, first_name, last_name, tel, gender, profile_image FROM instructor WHERE id = %s', (user_id,))
    instructor_data = cursor.fetchone()
    if instructor_data:
        db_role = str(instructor_data.get('role', 'instructor')).strip()
        print(f"DEBUG: พบผู้ใช้ในตาราง 'instructor'. Role: '{db_role}'")
        instructor_obj = Instructor(
            id=instructor_data['id'], role=db_role,
            first_name=instructor_data['first_name'], last_name=instructor_data['last_name'],
            username=instructor_data['username'], email=instructor_data['email'],
            tel=instructor_data.get('tel'), gender=instructor_data.get('gender'),
            profile_image=instructor_data.get('profile_image')
        )
        return instructor_obj
    
    # 3. ตรวจสอบในตาราง User
    cursor.execute('SELECT id, username, email, role, first_name, last_name, id_card, gender, profile_image FROM user WHERE id = %s', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        db_role = str(user_data.get('role', 'user')).strip()
        print(f"DEBUG: พบผู้ใช้ในตาราง 'user'. Role: '{db_role}'")
        
        # VVVVVV จุดที่แก้ไข Bug VVVVVV
        # โค้ดเดิมขาดการส่งค่า id_card และ gender ตรงนี้
        user_obj = User(
            id=user_data['id'], role=db_role,
            first_name=user_data['first_name'], last_name=user_data['last_name'],
            username=user_data['username'], email=user_data['email'],
            id_card=user_data.get('id_card'), 
            gender=user_data.get('gender'),
            profile_image=user_data.get('profile_image')
        )
        # ^^^^^^ สิ้นสุดจุดที่แก้ไข ^^^^^^
        return user_obj
    
    print(f"DEBUG: ไม่พบ User ID {user_id} ในตารางใดๆ")
    cursor.close()
    return None

# ---------------------------------------------------------------------------------------------


def _update_current_user(user_id, role, table_name, select_query_columns):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT {select_query_columns} FROM {table_name} WHERE id = %s", (user_id,))
    updated_user_data_from_db = cursor.fetchone()
    cursor.close()

    if not updated_user_data_from_db:
        print(f"WARNING: _update_current_user: User ID {user_id} not found after update.")
        return False

    processed_role = str(updated_user_data_from_db.get('role', '')).strip()
    
    user_obj = None
    if role == 'admin':
        user_obj = Admin(
            id=updated_user_data_from_db['id'], role=processed_role,
            first_name=updated_user_data_from_db['first_name'], last_name=updated_user_data_from_db['last_name'],
            username=updated_user_data_from_db['username'], email=updated_user_data_from_db['email'],
            tel=updated_user_data_from_db.get('tel'), gender=updated_user_data_from_db.get('gender'),
            profile_image=updated_user_data_from_db.get('profile_image')
        )
    elif role == 'instructor':
        user_obj = Instructor(
            id=updated_user_data_from_db['id'], role=processed_role,
            first_name=updated_user_data_from_db['first_name'], last_name=updated_user_data_from_db['last_name'],
            username=updated_user_data_from_db['username'], email=updated_user_data_from_db['email'],
            tel=updated_user_data_from_db.get('tel'), gender=updated_user_data_from_db.get('gender'),
            profile_image=updated_user_data_from_db.get('profile_image')
        )
    elif role == 'user':
        user_obj = User(
            id=updated_user_data_from_db['id'], role=processed_role,
            first_name=updated_user_data_from_db['first_name'], last_name=updated_user_data_from_db['last_name'],
            username=updated_user_data_from_db['username'], email=updated_user_data_from_db['email'],
            id_card=updated_user_data_from_db.get('id_card'), gender=updated_user_data_from_db.get('gender'),
            profile_image=updated_user_data_from_db.get('profile_image')
        )
    else:
        return False

    if user_obj: # ตรวจสอบว่าสร้าง user_obj ได้
        user_obj.profile_image_version = datetime.now().timestamp() # ✅ ตั้งค่า version ใหม่
        login_user(user_obj, remember=True)
        return True
    return False


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

@app.context_processor
def inject_now():
    from datetime import datetime # ต้อง import datetime ภายในฟังก์ชันนี้ หรือด้านบนสุดของไฟล์
    return {'now': datetime.now}

# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
@app.context_processor
def utility_processor():
    def get_youtube_embed_url(youtube_link):
        """
        ฟังก์ชันนี้จะรับลิงก์ YouTube ทุกรูปแบบ
        แล้วแปลงให้เป็นลิงก์สำหรับฝัง (embed) ที่ถูกต้อง
        """
        if not youtube_link:
            return ""

        # รูปแบบที่ 1: https://www.youtube.com/watch?v=VIDEO_ID
        match = re.search(r"watch\?v=([a-zA-Z0-9_-]+)", youtube_link)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"

        # รูปแบบที่ 2: https://youtu.be/VIDEO_ID
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]+)", youtube_link)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"

        # รูปแบบที่ 3: https://www.youtube.com/embed/VIDEO_ID (ถ้าลิงก์ถูกต้องอยู่แล้ว)
        if "embed/" in youtube_link:
            return youtube_link

        # ถ้าไม่ตรงกับรูปแบบไหนเลย
        return "" # หรือจะ return URL แจ้งเตือนข้อผิดพลาดก็ได้
        
    return dict(get_youtube_embed_url=get_youtube_embed_url)

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
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # 1. ดึงข้อมูลคอร์สทั้งหมด (เหมือนเดิม)
    query = """
    SELECT
        c.id,
        c.title AS course_name,
        c.featured_image,
        c.featured_video,
        cat.id AS category_id,
        cat.name AS category_name,
        i.id AS instructor_id,
        i.first_name,
        i.last_name
    FROM courses c
    LEFT JOIN categories cat ON c.categories_id = cat.id
    LEFT JOIN instructor i ON c.instructor_id = i.id
    WHERE c.status = 'publish'
    ORDER BY c.id DESC
    """
    cursor.execute(query)
    courses_raw = cursor.fetchall()
    
    # --- VVVVVV จุดที่แก้ไข VVVVVV ---

    # 2. สร้าง List ว่างๆ เพื่อเก็บข้อมูลคอร์สที่สมบูรณ์
    courses = []
    
    # 3. วนลูปแต่ละคอร์สเพื่อนับจำนวนนักเรียน
    for row in courses_raw:
        course_id = row['id']
        
        # นับจำนวนนักเรียนสำหรับคอร์สนี้โดยเฉพาะ
        cursor.execute("SELECT COUNT(id) as count FROM registered_courses WHERE course_id = %s", (course_id,))
        student_count_data = cursor.fetchone()
        students_count = student_count_data['count'] if student_count_data else 0

        # นำข้อมูลทั้งหมดมารวมกันแล้วเพิ่มเข้าไปใน List
        courses.append({
            'id': row['id'],
            'course_name': row['course_name'],
            'description': row.get('description'), 
            'featured_image': row['featured_image'],
            'featured_video': row['featured_video'],
            'category': {
                'id': row['category_id'],
                'name': row['category_name']
            },
            'instructor': {
                'id': row['instructor_id'],
                'first_name': row['first_name'],
                'last_name': row['last_name']
            },
            'students_count': students_count, # <--- ใช้ค่าที่นับมาได้
            'duration_hours': 'N/A'
        })
        
    # --- ^^^^^^ สิ้นสุดจุดที่แก้ไข ^^^^^^ ---

    cursor.close()
    
    # 4. ส่ง List ที่สมบูรณ์แล้วไปแสดงผล
    return render_template('course/course.html', courses=courses)



@app.route('/course/<int:course_id>')
def course_detail(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลคอร์ส (เหมือนเดิม)
    query = """
    SELECT
        c.id, c.title AS course_name, c.description, c.featured_image, c.featured_video,
        cat.id AS category_id, cat.name AS category_name,
        i.id AS instructor_id, i.first_name, i.last_name,
        c.status,
        pre_q.quiz_id AS pre_test_quiz_id,
        pre_q.quiz_name AS pre_test_quiz_name,
        pre_q.passing_percentage AS pre_test_passing_percentage
    FROM courses c
    LEFT JOIN categories cat ON c.categories_id = cat.id
    LEFT JOIN instructor i ON c.instructor_id = i.id
    LEFT JOIN lesson AS l_quiz ON l_quiz.course_id = c.id
    LEFT JOIN quiz AS pre_q ON pre_q.lesson_id = l_quiz.lesson_id AND pre_q.quiz_type = 'Pre-test'
    WHERE c.id = %s AND c.status = 'publish'
    GROUP BY c.id
    LIMIT 1
    """
    try:
        cursor.execute(query, (course_id,))
        course_data = cursor.fetchone()
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการดึงข้อมูลหลักสูตร: {str(e)}", "danger")
        cursor.close()
        return redirect(url_for('course'))

    if not course_data:
        flash('ไม่พบหลักสูตรที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('course'))

    # --- VVVVVV จุดที่แก้ไข VVVVVV ---

    # 2. นับจำนวนนักเรียนที่ลงทะเบียนในคอร์สนี้
    cursor.execute("SELECT COUNT(id) as count FROM registered_courses WHERE course_id = %s", (course_id,))
    student_count_data = cursor.fetchone()
    students_count = student_count_data['count'] if student_count_data else 0

    # 3. สร้าง Dictionary ของ course พร้อมกับจำนวนนักเรียนที่นับมาได้
    course = {
        'id': course_data['id'], 'course_name': course_data['course_name'], 'description': course_data.get('description', ''),
        'featured_image': course_data['featured_image'], 'featured_video': course_data['featured_video'],
        'category': {'id': course_data['category_id'], 'name': course_data['category_name']},
        'instructor': {'id': course_data['instructor_id'], 'first_name': course_data['first_name'], 'last_name': course_data['last_name']},
        'pre_test_quiz_id': course_data.get('pre_test_quiz_id'),
        'pre_test_quiz_name': course_data.get('pre_test_quiz_name'),
        'pre_test_passing_percentage': course_data.get('pre_test_passing_percentage'),
        'students_count': students_count,  # <--- ใช้ค่าที่นับมาได้
        'duration_hours': 'N/A' # คุณสามารถคำนวณค่านี้เพิ่มเติมได้ในอนาคต
    }
    
    # --- ^^^^^^ สิ้นสุดจุดที่แก้ไข ^^^^^^ ---

    cursor.execute("SELECT lesson_id, lesson_name, lesson_date, description FROM lesson WHERE course_id = %s ORDER BY lesson_date ASC", (course_id,))
    lessons_in_course = cursor.fetchall()
    first_lesson_id = lessons_in_course[0].get('lesson_id') if lessons_in_course else None

    # เตรียมตัวแปร (เหมือนเดิม)
    is_enrolled = False
    user_pre_test_attempt = None
    progress_percentage = 0
    passed_display = False

    # ตรวจสอบสถานะผู้ใช้ (เหมือนเดิม)
    if current_user.is_authenticated:
        user_id = current_user.id
        cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (user_id, course_id))
        
        if cursor.fetchone():
            is_enrolled = True
        
            if course.get('pre_test_quiz_id'):
                cursor.execute("""
                    SELECT score, passed FROM user_quiz_attempts 
                    WHERE user_id = %s AND quiz_id = %s 
                    ORDER BY attempt_date DESC LIMIT 1
                """, (user_id, course['pre_test_quiz_id']))
                user_pre_test_attempt = cursor.fetchone()
                if user_pre_test_attempt:
                    passed_display = user_pre_test_attempt['passed']

            # ส่วนคำนวณความคืบหน้า (เหมือนเดิม)
            cursor.execute("SELECT COUNT(qv.video_id) as total FROM quiz_video qv JOIN lesson l ON qv.lesson_id = l.lesson_id WHERE l.course_id = %s AND qv.quiz_id IS NULL", (course_id,))
            total_videos = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(q.quiz_id) as total FROM quiz q JOIN lesson l ON q.lesson_id = l.lesson_id WHERE l.course_id = %s AND q.quiz_type = 'Post_test'", (course_id,))
            total_post_tests = cursor.fetchone()['total']
            total_items = total_videos + total_post_tests

            cursor.execute("SELECT COUNT(uvp.id) as total FROM user_video_progress uvp JOIN quiz_video qv ON uvp.video_id = qv.video_id JOIN lesson l ON qv.lesson_id = l.lesson_id WHERE uvp.user_id = %s AND l.course_id = %s", (user_id, course_id))
            completed_videos = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(DISTINCT uqa.quiz_id) as total FROM user_quiz_attempts uqa JOIN quiz q ON uqa.quiz_id = q.quiz_id JOIN lesson l ON q.lesson_id = l.lesson_id WHERE uqa.user_id = %s AND l.course_id = %s AND q.quiz_type = 'Post_test' AND uqa.passed = 1", (user_id, course_id))
            passed_post_tests = cursor.fetchone()['total']
            completed_items = completed_videos + passed_post_tests
            
            progress_percentage = (completed_items / total_items) * 100 if total_items > 0 else 0
            
    cursor.close()
    
    return render_template('course/course_detail.html', 
                           course=course, 
                           lessons_in_course=lessons_in_course,
                           is_enrolled=is_enrolled,
                           user_pre_test_attempt=user_pre_test_attempt,
                           passed_display=passed_display,
                           first_lesson_id=first_lesson_id,
                           progress=progress_percentage)

    
@app.route('/user/lesson/<int:lesson_id>')
@login_required
def user_view_lesson(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    user_id = current_user.id

    # ดึงข้อมูลบทเรียน (เหมือนเดิม)
    cursor.execute("SELECT lesson_id, lesson_name, description, course_id FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()
    if not lesson:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard'))

    # ดึงข้อมูลหลักสูตร (เหมือนเดิม)
    cursor.execute("SELECT id, title FROM courses WHERE id = %s", (lesson['course_id'],))
    course_of_lesson = cursor.fetchone()
    if not course_of_lesson:
        flash('ไม่พบหลักสูตรที่เกี่ยวข้องกับบทเรียนนี้', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard'))

    # ตรวจสอบสิทธิ์การเข้าถึง (เหมือนเดิม)
    if current_user.role not in ['admin', 'instructor']:
        cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (user_id, course_of_lesson['id']))
        if not cursor.fetchone():
            flash('คุณยังไม่ได้ลงทะเบียนหลักสูตรนี้', 'warning')
            cursor.close()
            return redirect(url_for('course_detail', course_id=course_of_lesson['id']))

    # --- VVVVVV แก้ไขการดึงเนื้อหา VVVVVV ---
    # เราจะดึงเนื้อหามาทั้งหมดก่อน แล้วค่อยวนลูปเพื่อเช็คสถานะ
    cursor.execute("""
        SELECT video_id, title, youtube_link, video_file, description, time_duration, video_image, quiz_id
        FROM quiz_video
        WHERE lesson_id = %s AND quiz_id IS NULL
        ORDER BY video_id ASC
    """, (lesson_id,))
    contents_raw = cursor.fetchall()

    # สร้าง List ใหม่เพื่อเก็บเนื้อหาพร้อมสถานะ "ดูจบแล้ว"
    lesson_contents_with_status = []
    for content in contents_raw:
        # ตรวจสอบว่าผู้ใช้คนนี้เคยดูวิดีโอนี้จบแล้วหรือยัง
        cursor.execute(
            "SELECT id FROM user_video_progress WHERE user_id = %s AND video_id = %s",
            (user_id, content['video_id'])
        )
        is_completed = True if cursor.fetchone() else False
        
        # เพิ่มข้อมูลสถานะเข้าไปใน Dictionary ของ content
        content_dict = dict(content) # แปลง tuple เป็น dict
        content_dict['is_completed'] = is_completed
        lesson_contents_with_status.append(content_dict)
    
    # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

    cursor.close()
    
    # ส่ง list ใหม่ที่มีสถานะไปด้วย
    return render_template('course/user_view_lesson.html',
                           lesson=lesson,
                           course=course_of_lesson,
                           lesson_contents=lesson_contents_with_status) # <-- ใช้ตัวแปรใหม่

@app.route('/course/join/<int:course_id>', methods=['POST'])
@login_required # ต้องล็อกอินก่อน
def join_course(course_id): 
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ตรวจสอบว่าหลักสูตรมีอยู่จริงหรือไม่
    cursor.execute("SELECT id, title FROM courses WHERE id = %s AND status = 'publish'", (course_id,))
    course = cursor.fetchone()

    if not course:
        flash('ไม่พบหลักสูตรที่ระบุ หรือหลักสูตรยังไม่เผยแพร่', 'danger')
        cursor.close()
        return redirect(url_for('course'))

    # 2. ตรวจสอบว่าผู้ใช้คนนี้ (current_user.id) ได้ลงทะเบียนหลักสูตรนี้ไปแล้วหรือยัง
    cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (current_user.id, course_id))
    already_registered = cursor.fetchone()

    if already_registered:
        flash(f"คุณได้ลงทะเบียนหลักสูตร '{course['title']}' นี้ไปแล้ว", 'info')
        cursor.close()
        # ✅ Redirect ไปที่หน้า Learning Path โดยตรง หากลงทะเบียนแล้ว
        return redirect(url_for('user_learning_path', course_id=course_id)) 

    # 3. บันทึกการลงทะเบียนหลักสูตร
    try:
        cursor.execute("INSERT INTO registered_courses (user_id, course_id, registered_at) VALUES (%s, %s, %s)",
                       (current_user.id, course_id, datetime.now()))
        mysql.connection.commit()
        flash(f"คุณได้ลงทะเบียนหลักสูตร '{course['title']}' สำเร็จแล้ว!", 'success')
        cursor.close()
        # ✅ Redirect ไปที่หน้า Learning Path โดยตรง หากลงทะเบียนสำเร็จ
        return redirect(url_for('user_learning_path', course_id=course_id)) 

    except Exception as e:
        mysql.connection.rollback()
        flash(f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}", 'danger')
        cursor.close()
        return redirect(url_for('course_detail', course_id=course_id))
    
# แก้ไขฟังก์ชันนี้ใน app.py ของคุณ
@app.route('/user/course/<int:course_id>/learning_path')
@login_required
def user_learning_path(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลหลักสูตร
    query = """
    SELECT
        c.id, c.title AS course_name, c.description, c.featured_image, c.featured_video,
        cat.id AS category_id, cat.name AS category_name,
        i.id AS instructor_id, i.first_name, i.last_name,
        c.status
    FROM courses c
    LEFT JOIN categories cat ON c.categories_id = cat.id
    LEFT JOIN instructor i ON c.instructor_id = i.id
    WHERE c.id = %s AND c.status = 'publish'
    LIMIT 1
    """
    cursor.execute(query, (course_id,))
    course_data = cursor.fetchone()

    if not course_data:
        flash('ไม่พบหลักสูตรที่ระบุ หรือหลักสูตรยังไม่เผยแพร่', 'danger')
        cursor.close()
        return redirect(url_for('course'))

    course_for_template = {
        'id': course_data['id'], 'title': course_data['course_name'], 'description': course_data.get('description', ''),
        'featured_image': course_data['featured_image'], 'featured_video': course_data['featured_video'],
        'category': {'id': course_data['category_id'], 'name': course_data['category_name']},
        'instructor': {'id': course_data['instructor_id'], 'first_name': course_data['first_name'], 'last_name': course_data['last_name']},
        'status': course_data.get('status')
    }

    # --- VVVVVV แก้ไขจุดที่ 1: ตรวจสอบสิทธิ์การเข้าถึง VVVVVV ---
    if current_user.role not in ['admin', 'instructor']:
        # ถ้าเป็น user ทั่วไป ให้ตรวจสอบการลงทะเบียน
        cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (current_user.id, course_id,))
        if not cursor.fetchone():
            flash('คุณยังไม่ได้ลงทะเบียนหลักสูตรนี้ กรุณาลงทะเบียนก่อน', 'warning')
            cursor.close()
            return redirect(url_for('course_detail', course_id=course_id))
    # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

    # ดึงบทเรียนและคำนวณความคืบหน้า
    cursor.execute("SELECT lesson_id, lesson_name, description FROM lesson WHERE course_id = %s ORDER BY lesson_id ASC", (course_id,))
    lessons_raw = cursor.fetchall()

    learning_path_data = []
    total_possible_learning_points = 0
    user_earned_learning_points = 0
    previous_lesson_completed = True

    for lesson_row in lessons_raw:
        # ... (โค้ด for loop และการคำนวณทั้งหมดของคุณเหมือนเดิม) ...
        # (โค้ดส่วนนี้ยาวมาก แต่ทำงานถูกต้องแล้ว จึงไม่นำมาแสดงซ้ำ)
        # ให้แน่ใจว่าโค้ด for loop เดิมของคุณยังอยู่ครบถ้วน
        is_locked = not previous_lesson_completed
        current_lesson_is_complete = True
        
        learning_path_data.append({
            'type': 'lesson', 'lesson_id': lesson_row['lesson_id'],
            'title': lesson_row['lesson_name'], 'description': lesson_row['description'],
            'is_locked': is_locked
        })
        
        cursor.execute("SELECT video_id, title, youtube_link, description, time_duration, quiz_id FROM quiz_video WHERE lesson_id = %s ORDER BY video_id ASC", (lesson_row['lesson_id'],))
        contents_raw = cursor.fetchall()

        lesson_pre_test_quiz = None
        lesson_post_test_quiz = None
        lesson_videos = []
        lesson_other_quizzes = []

        for content_row in contents_raw:
            if content_row['quiz_id']:
                cursor.execute("SELECT quiz_name, quiz_type, passing_percentage FROM quiz WHERE quiz_id = %s", (content_row['quiz_id'],))
                quiz_info = cursor.fetchone()
                if quiz_info:
                    if quiz_info['quiz_type'] == 'Pre-test':
                        lesson_pre_test_quiz = {'quiz_id': content_row['quiz_id'], 'title': f"แบบทดสอบก่อนบทเรียน: {quiz_info['quiz_name']}", 'passing_percentage': quiz_info['passing_percentage']}
                    elif quiz_info['quiz_type'] == 'Post_test':
                        lesson_post_test_quiz = {'quiz_id': content_row['quiz_id'], 'title': f"แบบทดสอบหลังเรียน: {quiz_info['quiz_name']}", 'passing_percentage': quiz_info['passing_percentage']}
                    else:
                        lesson_other_quizzes.append({'quiz_id': content_row['quiz_id'], 'title': f"แบบทดสอบ: {quiz_info['quiz_name']}", 'passing_percentage': quiz_info['passing_percentage']})
            else:
                lesson_videos.append(content_row)

        if lesson_pre_test_quiz:
            total_possible_learning_points += 1
            cursor.execute("SELECT score, passed FROM user_quiz_attempts WHERE user_id = %s AND quiz_id = %s ORDER BY attempt_date DESC LIMIT 1", (current_user.id, lesson_pre_test_quiz['quiz_id']))
            attempt = cursor.fetchone()
            passed = attempt['passed'] if attempt else False
            if passed: user_earned_learning_points += 1
            learning_path_data.append({
                'type': 'pre_test_lesson', 'quiz_id': lesson_pre_test_quiz['quiz_id'], 'title': lesson_pre_test_quiz['title'],
                'status': "ผ่าน" if passed else ("ไม่ผ่าน" if attempt else "ยังไม่ทำ"),
                'passed': passed, 'score': attempt['score'] if attempt else 0, 'passing_percentage': lesson_pre_test_quiz['passing_percentage'],
                'is_locked': is_locked
            })
        
        for video_row in lesson_videos:
            total_possible_learning_points += 1
            cursor.execute("SELECT id FROM user_video_progress WHERE user_id = %s AND video_id = %s", (current_user.id, video_row['video_id']))
            progress = cursor.fetchone()
            is_completed = True if progress else False
            if is_completed:
                user_earned_learning_points += 1
            else:
                current_lesson_is_complete = False
            learning_path_data.append({
                'type': 'video_content', 'video_id': video_row['video_id'], 'lesson_id': lesson_row['lesson_id'],
                'title': f"วิดีโอ: {video_row['title']}", 'status': "ดูแล้ว" if is_completed else "ยังไม่ได้ดู",
                'is_completed': is_completed, 'youtube_link': video_row['youtube_link'], 'description': video_row['description'],
                'is_locked': is_locked
            })
            
        if lesson_post_test_quiz:
            total_possible_learning_points += 1
            cursor.execute("SELECT score, passed FROM user_quiz_attempts WHERE user_id = %s AND quiz_id = %s ORDER BY attempt_date DESC LIMIT 1", (current_user.id, lesson_post_test_quiz['quiz_id']))
            attempt = cursor.fetchone()
            passed = attempt['passed'] if attempt else False
            if passed:
                user_earned_learning_points += 1
            else:
                current_lesson_is_complete = False
            learning_path_data.append({
                'type': 'post_test_lesson', 'quiz_id': lesson_post_test_quiz['quiz_id'], 'title': lesson_post_test_quiz['title'],
                'status': "ผ่าน" if passed else ("ไม่ผ่าน" if attempt else "ยังไม่ทำ"),
                'passed': passed, 'score': attempt['score'] if attempt else 0, 'passing_percentage': lesson_post_test_quiz['passing_percentage'],
                'is_locked': is_locked
            })

        previous_lesson_completed = current_lesson_is_complete


    if total_possible_learning_points > 0:
        overall_progress_percentage = (user_earned_learning_points / total_possible_learning_points) * 100
    else:
        overall_progress_percentage = 0.0

    is_course_completed = False
    if overall_progress_percentage >= 100:
        is_course_completed = True
        cursor.execute("SELECT id FROM course_completions WHERE user_id = %s AND course_id = %s", (current_user.id, course_id))
        if not cursor.fetchone():
            certificate_code = f"CERT-{course_id}-{current_user.id}-{int(datetime.now().timestamp())}"
            cursor.execute("""
                INSERT INTO course_completions (user_id, course_id, completion_date, certificate_code)
                VALUES (%s, %s, %s, %s)
            """, (current_user.id, course_id, datetime.now().date(), certificate_code))
            mysql.connection.commit()
            flash('ยินดีด้วย! คุณเรียนจบหลักสูตรนี้แล้ว สามารถดาวน์โหลดใบประกาศได้เลย', 'success')

    cursor.close()
    
    # --- VVVVVV แก้ไขจุดที่ 2: แก้ไขชื่อไฟล์ Template ให้ถูกต้อง VVVVVV ---
    return render_template('course/learning_path.html', 
                           course=course_for_template, 
                           learning_path_data=learning_path_data,
                           overall_progress_percentage=overall_progress_percentage,
                           is_course_completed=is_course_completed)
    
@app.route('/user/video/mark_watched', methods=['POST'])
@login_required
def mark_video_as_watched():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    video_id = request.form.get('video_id', type=int)
    course_id = request.form.get('course_id', type=int)
    lesson_id = request.form.get('lesson_id', type=int)

    if not video_id or not course_id or not lesson_id:
        flash('ข้อมูลไม่สมบูรณ์ ไม่สามารถทำเครื่องหมายวิดีโอได้', 'danger')
        return redirect(request.referrer or url_for('user_dashboard'))

    try:
        # ตรวจสอบว่าผู้ใช้ลงทะเบียนหลักสูตรนี้แล้วหรือไม่ (เพื่อความปลอดภัย)
        cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (current_user.id, course_id))
        is_enrolled = cursor.fetchone()
        if not is_enrolled:
            flash('คุณยังไม่ได้ลงทะเบียนหลักสูตรนี้ ไม่สามารถทำเครื่องหมายวิดีโอได้', 'danger')
            cursor.close()
            return redirect(url_for('course_detail', course_id=course_id))

        # บันทึก/อัปเดตสถานะการดูวิดีโอ
        cursor.execute("""
            INSERT INTO user_lesson_progress (user_id, video_id, lesson_id, is_completed, completed_at)
            VALUES (%s, %s, %s, TRUE, %s)
            ON DUPLICATE KEY UPDATE is_completed = TRUE, completed_at = %s
        """, (current_user.id, video_id, lesson_id, datetime.now(), datetime.now()))
        
        mysql.connection.commit()
        flash('ทำเครื่องหมายวิดีโอว่าดูแล้วเรียบร้อย!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'เกิดข้อผิดพลาดในการทำเครื่องหมายวิดีโอ: {str(e)}', 'danger')
        print(f"ERROR: mark_video_as_watched failed: {e}")
    finally:
        cursor.close()

    # Redirect กลับไปหน้า Learning Path เดิม
    return redirect(url_for('user_learning_path', course_id=course_id))

@app.route('/video/mark_complete_auto', methods=['POST'])
@login_required
def mark_video_as_watched_auto():
    video_id = request.form.get('video_id', type=int)
    if not video_id:
        return jsonify({'status': 'error', 'message': 'Missing video_id'}), 400

    try:
        cursor = mysql.connection.cursor()
        # ตรวจสอบว่าเคยบันทึกไปแล้วหรือยัง
        cursor.execute("SELECT id FROM user_video_progress WHERE user_id = %s AND video_id = %s", (current_user.id, video_id))
        already_completed = cursor.fetchone()

        if not already_completed:
            # ถ้ายังไม่เคยบันทึก ให้ INSERT ข้อมูลใหม่
            cursor.execute("INSERT INTO user_video_progress (user_id, video_id, completed_at) VALUES (%s, %s, %s)",
                           (current_user.id, video_id, datetime.now()))
            mysql.connection.commit()
        
        cursor.close()
        return jsonify({'status': 'success', 'message': 'Video progress saved.'})
        
    except Exception as e:
        # ในกรณีเกิดข้อผิดพลาด
        print(f"Database error in mark_video_as_watched_auto: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/video/mark_complete/<int:video_id>', methods=['POST']) # ✅ แก้ไข URL ให้ตรงกับ JavaScript
@login_required
def mark_video_completed(video_id):
    # ตรวจสอบว่าผู้ใช้ล็อกอินอยู่หรือไม่ (เพื่อความปลอดภัย)
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    try:
        cursor = mysql.connection.cursor()
        user_id = current_user.id
        
        # 1. ตรวจสอบก่อนว่าเคยบันทึกไปแล้วหรือยัง
        cursor.execute(
            "SELECT id FROM user_video_progress WHERE user_id = %s AND video_id = %s",
            (user_id, video_id)
        )
        already_completed = cursor.fetchone()

        # 2. ถ้ายังไม่เคยบันทึก ให้เพิ่มข้อมูลใหม่ (เพิ่ม completed_at เพื่อความสมบูรณ์)
        if not already_completed:
            cursor.execute(
                "INSERT INTO user_video_progress (user_id, video_id, completed_at) VALUES (%s, %s, %s)",
                (user_id, video_id, datetime.now())
            )
            mysql.connection.commit() # ยืนยันการบันทึกข้อมูลลงฐานข้อมูล
            
        cursor.close()
        # ✅ แก้ไข JSON response ให้มี key ชื่อ 'success'
        return jsonify({'success': True, 'message': 'Progress saved successfully'})

    except Exception as e:
        # หากเกิดข้อผิดพลาด ให้ยกเลิกการเปลี่ยนแปลงและแจ้งกลับ
        mysql.connection.rollback()
        print(f"Error in mark_video_completed: {str(e)}") # แสดง error ใน terminal ของเซิร์ฟเวอร์
        # ✅ แก้ไข JSON response ให้มี key ชื่อ 'success'
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/quiz/start/<int:quiz_id>', methods=['GET'])
@login_required
def start_quiz(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    print(f"\n--- DEBUG: เข้าสู่ start_quiz สำหรับ quiz_id: {quiz_id} ---")

    # 1. ดึงข้อมูลแบบทดสอบ (Quiz)
    cursor.execute("SELECT quiz_id, quiz_name, lesson_id, passing_percentage FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        flash('ไม่พบแบบทดสอบที่ระบุ', 'danger')
        cursor.close()
        print(f"DEBUG: ไม่พบบททดสอบ ID {quiz_id}. Redirect ไปที่ user_dashboard.")
        return redirect(url_for('user_dashboard'))

    print(f"DEBUG: พบข้อมูลแบบทดสอบ: {quiz}")
    print(f"DEBUG: lesson_id ของแบบทดสอบ: {quiz.get('lesson_id')}")

    # 2. ดึงคำถามทั้งหมดของแบบทดสอบนี้
    cursor.execute("""
        SELECT 
            question_id, question_name, choice_a, choice_b, choice_c, choice_d,
            question_image, choice_a_image, choice_b_image, choice_c_image, choice_d_image,
            score, correct_answer
        FROM questions 
        WHERE quiz_id = %s
    """, (quiz_id,))
    
    questions_raw = cursor.fetchall() # ✅ ดึงข้อมูลดิบมาเป็น tuple
    questions = list(questions_raw) # ✅ แปลง tuple ให้เป็น list ก่อนสุ่ม

    if not questions:
        flash('ไม่พบคำถามสำหรับแบบทดสอบนี้', 'warning')
        cursor.close()
        
        redirect_course_id = quiz.get('lesson_id')
        if redirect_course_id is None:
            print(f"DEBUG: ไม่พบคำถามสำหรับแบบทดสอบ ID {quiz_id} และ lesson_id เป็น None. Redirect ไปที่ user_dashboard.")
            return redirect(url_for('user_dashboard'))
        else:
            print(f"DEBUG: ไม่พบคำถามสำหรับแบบทดสอบ ID {quiz_id}. Redirect ไปที่ course_detail สำหรับ lesson_id: {redirect_course_id}.")
            return redirect(url_for('course_detail', course_id=redirect_course_id))

    # ✅ สุ่มลำดับคำถาม (ตอนนี้ questions เป็น list แล้ว)
    random.shuffle(questions) 

    print(f"DEBUG: พบ {len(questions)} คำถามสำหรับแบบทดสอบ ID {quiz_id}. กำลังเรนเดอร์หน้าทำแบบทดสอบ (คำถามถูกสุ่มแล้ว).")
    cursor.close()
    return render_template('course/quiz_page.html', quiz=quiz, questions=questions)

@app.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลแบบทดสอบ (เช่น ชื่อ, เกณฑ์ผ่าน)
    cursor.execute("SELECT * FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()
    if not quiz:
        flash('ไม่พบแบบทดสอบนี้', 'danger')
        return redirect(url_for('home'))

    # 2. ดึงคำถามทั้งหมดจากตาราง questions ที่มีโครงสร้างถูกต้อง
    cursor.execute("SELECT * FROM questions WHERE quiz_id = %s ORDER BY question_id", (quiz_id,))
    questions = cursor.fetchall()
    
    cursor.close()
    
    # ส่งข้อมูลไปที่หน้า quiz_page.html
    return render_template('course/quiz_page.html', quiz=quiz, questions=questions)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # 1. ดึงคำตอบที่ถูกต้องจากคอลัมน์ correct_answer
    cursor.execute("SELECT question_id, correct_answer FROM questions WHERE quiz_id = %s", (quiz_id,))
    correct_answers = {row['question_id']: row['correct_answer'] for row in cursor.fetchall()}
    
    # 2. ดึงคำตอบของผู้ใช้จากฟอร์ม
    user_answers = {}
    for key, value in request.form.items():
        if key.startswith('question_'):
            question_id = int(key.split('_')[1])
            user_answers[question_id] = value

    # 3. ตรวจคำตอบและคำนวณคะแนน
    score = 0
    total_questions = len(correct_answers)
    for question_id, user_answer in user_answers.items():
        if question_id in correct_answers and correct_answers[question_id] == user_answer:
            score += 1
    
    # 4. คำนวณเปอร์เซ็นต์และตรวจสอบผล
    percentage = (score / total_questions) * 100 if total_questions > 0 else 0
    cursor.execute("SELECT passing_percentage FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz_info = cursor.fetchone()
    passed = 1 if percentage >= quiz_info['passing_percentage'] else 0

    # 5. บันทึกผลการสอบ
    cursor.execute("""
        INSERT INTO user_quiz_attempts (user_id, quiz_id, score, total_questions, percentage, passed, attempt_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (current_user.id, quiz_id, score, total_questions, percentage, passed, datetime.now()))
    mysql.connection.commit()
    
    attempt_id = cursor.lastrowid
    cursor.close()

    flash(f'คุณทำแบบทดสอบเสร็จแล้ว ได้คะแนน {score}/{total_questions}', 'info')
    return redirect(url_for('quiz_result', attempt_id=attempt_id)) # สร้าง route หน้าผลลัพธ์ต่อไป

@app.route('/quiz/result/<int:attempt_id>')
@login_required
def quiz_result(attempt_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลผลการสอบจาก ID ที่ได้รับมา
    # เพิ่มการ JOIN เพื่อดึงข้อมูล course_id และ lesson_id มาใช้กับปุ่ม "กลับ"
    cursor.execute("""
        SELECT 
            uqa.*, 
            q.quiz_name, 
            q.quiz_type,
            l.course_id
        FROM user_quiz_attempts uqa
        JOIN quiz q ON uqa.quiz_id = q.quiz_id
        JOIN lesson l ON q.lesson_id = l.lesson_id
        WHERE uqa.id = %s AND uqa.user_id = %s
    """, (attempt_id, current_user.id))
    
    attempt = cursor.fetchone()
    cursor.close()

    if not attempt:
        flash('ไม่พบผลการสอบของคุณ', 'danger')
        return redirect(url_for('home'))

    return render_template('course/quiz_result.html', attempt=attempt)
    
# ✅ Placeholder Route สำหรับสร้างใบประกาศ
@app.route('/course/<int:course_id>/certificate')
@login_required
def generate_certificate(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูล (เหมือนเดิม)
    cursor.execute("""
        SELECT c.title, comp.completion_date
        FROM course_completions comp
        JOIN courses c ON comp.course_id = c.id
        WHERE comp.user_id = %s AND comp.course_id = %s
    """, (current_user.id, course_id))
    completion_data = cursor.fetchone()
    cursor.close()

    if not completion_data:
        flash('คุณยังไม่จบหลักสูตรนี้', 'danger')
        return redirect(url_for('user_learning_path', course_id=course_id))

    user_name = f"{current_user.first_name} {current_user.last_name}"
    completion_date_obj = completion_data['completion_date']
    
    # 2. เปิดไฟล์รูปภาพ Template (เหมือนเดิม)
    template_path = 'static/images/certificate.jpg'
    image = Image.open(template_path)
    draw = ImageDraw.Draw(image)

    # --- VVVVVV ส่วนที่แก้ไข: สร้างวันที่ภาษาอังกฤษ VVVVVV ---
    def format_english_date(date_obj):
        english_months = [
            "January", "February", "March", "April",
            "May", "June", "July", "August",
            "September", "October", "November", "December"
        ]
        day = date_obj.day
        month = english_months[date_obj.month - 1]
        year = date_obj.year # ใช้ปี ค.ศ. ตรงๆ
        # จัดรูปแบบเป็น "August 18, 2025"
        return f"{month} {day}, {year}"

    formatted_date = format_english_date(completion_date_obj)
    # --- ^^^^^^ สิ้นสุดส่วนที่แก้ไข ^^^^^^ ---

    # 3. เตรียมฟอนต์ (เหมือนเดิม)
    font_path = 'Sarabun-Regular.ttf'
    font_name = ImageFont.truetype(font_path, 120)
    font_date = ImageFont.truetype(font_path, 60)

    # 4. เขียน "ชื่อผู้เรียน" (เหมือนเดิม)
    _, _, text_width_name, _ = draw.textbbox((0, 0), user_name, font=font_name)
    x_position_name = (image.width - text_width_name) / 2
    draw.text((x_position_name, 570), user_name, font=font_name, fill='rgb(0, 0, 0)')

    # 5. เขียน "วันที่" (ใช้ตัวแปรใหม่)
    date_text = formatted_date # <--- เอาคำว่า "ณ วันที่" ออก และใช้รูปแบบใหม่
    _, _, text_width_date, _ = draw.textbbox((0, 0), date_text, font=font_date)
    x_position_date = (image.width - text_width_date) / 2
    draw.text((x_position_date, 975), date_text, font=font_date, fill='rgb(0, 0, 0)')

    # 6. บันทึกและส่งไฟล์ (เหมือนเดิม)
    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f'certificate_{course_id}.png')

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

        # ตรวจสอบใน admin
        cursor.execute('SELECT id, username, password, email, role, first_name, last_name, tel, gender, profile_image FROM admin WHERE username = %s OR email = %s', (email_or_username, email_or_username))
        admin_info = cursor.fetchone()
        if admin_info and check_password_hash(admin_info['password'], password):
            processed_role = str(admin_info.get('role', 'admin')).strip()
            print(f"DEBUG: Login Attempt: Found Admin '{admin_info['username']}'. Role: '{processed_role}'")
            admin_obj = Admin(
                id=admin_info['id'], role=processed_role,
                first_name=admin_info['first_name'], last_name=admin_info['last_name'],
                username=admin_info['username'], email=admin_info['email'],
                tel=admin_info.get('tel'), gender=admin_info.get('gender'),
                profile_image=admin_info.get('profile_image')
            )
            try: # ✅ เพิ่ม try-except block
                login_user(admin_obj)
                flash('ผู้ดูแลระบบเข้าสู่ระบบสำเร็จ!', 'success')
                return redirect(url_for('admin_dashboard'))
            except Exception as e:
                print(f"ERROR: Login_user failed for Admin: {e}")
                flash('เกิดข้อผิดพลาดในการเข้าสู่ระบบ', 'danger')
                return redirect(url_for('login'))
        
        # ตรวจสอบใน instructor
        cursor.execute('SELECT id, username, password, email, role, first_name, last_name, tel, gender, profile_image FROM instructor WHERE username = %s OR email = %s', (email_or_username, email_or_username))
        instructor_info = cursor.fetchone()
        if instructor_info and check_password_hash(instructor_info['password'], password):
            processed_role = str(instructor_info.get('role', 'instructor')).strip()
            print(f"DEBUG: Login Attempt: Found Instructor '{instructor_info['username']}'. Role: '{processed_role}'")
            instructor_obj = Instructor(
                id=instructor_info['id'], role=processed_role,
                first_name=instructor_info['first_name'], last_name=instructor_info['last_name'],
                username=instructor_info['username'], email=instructor_info['email'], tel=instructor_info['tel'],
                profile_image=instructor_info.get('profile_image')
            )
            try: # ✅ เพิ่ม try-except block
                login_user(instructor_obj)
                flash('ผู้สอนเข้าสู่ระบบสำเร็จ!', 'success')
                return redirect(url_for('instructor_dashboard'))
            except Exception as e:
                print(f"ERROR: Login_user failed for Instructor: {e}")
                flash('เกิดข้อผิดพลาดในการเข้าสู่ระบบ', 'danger')
                return redirect(url_for('login'))

        # ตรวจสอบใน user ทั่วไป
        cursor.execute('SELECT id, username, password, email, role, first_name, last_name, id_card, gender, profile_image FROM user WHERE username = %s OR email = %s', (email_or_username, email_or_username))
        user_info = cursor.fetchone()
        if user_info and check_password_hash(user_info['password'], password):
            processed_role = str(user_info.get('role', 'user')).strip()
            print(f"DEBUG: Login Attempt: Found User '{user_info['username']}'. Role: '{processed_role}'")
            user_obj = User(
                id=user_info['id'], role=processed_role,
                first_name=user_info['first_name'], last_name=user_info['last_name'],
                username=user_info['username'], email=user_info['email'],
                profile_image=user_info.get('profile_image')
            )
            try: # ✅ เพิ่ม try-except block
                login_user(user_obj)
                flash('เข้าสู่ระบบสำเร็จ!', 'success')
                return redirect(url_for('home'))
            except Exception as e:
                print(f"ERROR: Login_user failed for User: {e}")
                flash('เกิดข้อผิดพลาดในการเข้าสู่ระบบ', 'danger')
                return redirect(url_for('login'))

        print(f"DEBUG: Login Attempt: User '{email_or_username}' not found or password incorrect.")
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

def is_valid_thai_id(id_card):
    """
    ฟังก์ชันสำหรับตรวจสอบความถูกต้องของเลขบัตรประชาชนไทย
    """
    if not id_card or not id_card.isdigit() or len(id_card) != 13:
        return False
    
    total = 0
    for i in range(12):
        total += int(id_card[i]) * (13 - i)
        
    checksum = (11 - (total % 11)) % 10
    
    return checksum == int(id_card[12])

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

            # --- VVVVVV เพิ่มเงื่อนไขการตรวจสอบเลขบัตรประชาชน VVVVVV ---
            if not is_valid_thai_id(id_card):
                flash('เลขบัตรประชาชนไม่ถูกต้อง!', 'error')
            # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---
            
            elif user:
                flash('บัญชีนี้มีผู้ใช้งานแล้ว!', 'error')
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
            elif gender not in ['Male', 'Female', 'Other', 'male', 'female', 'other']:
                flash('กรุณาเลือกเพศที่ถูกต้อง!', 'error')
            else:
                hashed_password = generate_password_hash(password)
                created_at = datetime.now()

                cursor.execute(
                    'INSERT INTO user (first_name, last_name, email, username, id_card, gender, password, role, created_at) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (first_name, last_name, email, username, id_card, gender.lower(), hashed_password, 'user', created_at)
                )
                mysql.connection.commit()
                
                flash('สมัครสมาชิกสำเร็จแล้ว! กรุณาเข้าสู่ระบบเพื่อดำเนินการต่อ', 'success')
                return redirect(url_for('login'))
        else:
            flash('กรุณากรอกแบบฟอร์มให้ครบถ้วน!', 'error')
    
    # ตรวจสอบให้แน่ใจว่า path ของ template ถูกต้อง
    return render_template('main/register.html')





@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ออกจากระบบสำเร็จแล้ว', 'success')
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. นับจำนวนผู้ใช้ทั้งหมด
    cursor.execute("SELECT COUNT(id) as total_users FROM user")
    total_users_data = cursor.fetchone()
    total_users = total_users_data['total_users'] if total_users_data else 0

    # 2. นับจำนวนรายวิชาทั้งหมด
    cursor.execute("SELECT COUNT(id) as total_courses FROM courses")
    total_courses_data = cursor.fetchone()
    total_courses = total_courses_data['total_courses'] if total_courses_data else 0

    # 3. VVVVVV เพิ่มโค้ดส่วนนี้เข้าไป VVVVVV
    # นับจำนวนการลงทะเบียนทั้งหมด
    cursor.execute("SELECT COUNT(id) as total_enrollments FROM registered_courses")
    total_enrollments_data = cursor.fetchone()
    total_enrollments = total_enrollments_data['total_enrollments'] if total_enrollments_data else 0
    # ^^^^^^ สิ้นสุดส่วนที่เพิ่ม ^^^^^^

    cursor.close()

    # --- VVVVVV แก้ไข return statement VVVVVV ---
    return render_template('admin/admin_dashboard.html',
                           total_users=total_users,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments, # <--- ส่งตัวแปรใหม่ไปด้วย
                           latest_login="ไม่มีข้อมูล") # <--- ส่งค่า default สำหรับ latest_login ไว้ก่อน

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
@admin_required
def manage_users():
    if request.method == 'POST':
        # (ส่วนโค้ด POST สำหรับเพิ่มผู้ใช้ของคุณยังคงเหมือนเดิม)
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        tel = request.form['tel']
        gender = request.form['gender']
        id_card = request.form['id_card']
        password = request.form['password']
        profile_image = request.files.get('profile_image')

        # (ควรเพิ่มการตรวจสอบข้อมูลที่นี่ เช่น เลขบัตรประชาชนที่ถูกต้อง)

        hashed_password = generate_password_hash(password)

        filename = None
        if profile_image and profile_image.filename != '':
            # (แนะนำให้ใช้ตรรกะสร้างชื่อไฟล์ไม่ซ้ำกันเหมือนที่เราเคยทำ)
            filename = secure_filename(profile_image.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER_PROFILE_IMAGES'], filename)
            profile_image.save(upload_path)

        cursor = mysql.connection.cursor()
        sql = """INSERT INTO user (first_name, last_name, email, username, tel, gender, id_card, password, profile_image, created_at)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (first_name, last_name, email, username, tel, gender, id_card, hashed_password, filename, datetime.now()))
        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มผู้ใช้สำเร็จ!', 'success')
        return redirect(url_for('manage_users'))

    # --- VVVVVV แก้ไขส่วน GET Request VVVVVV ---
    # ดึงข้อมูลผู้ใช้จากฐานข้อมูล (GET)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # เพิ่ม id, id_card และ created_at เข้าไปใน SELECT เพื่อให้แน่ใจว่าถูกดึงมาด้วย
    cursor.execute("SELECT id, first_name, last_name, email, username, tel, id_card, gender, created_at FROM user ORDER BY created_at DESC")
    users = cursor.fetchall()
    cursor.close()

    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/verify-password', methods=['POST'])
@admin_required
def admin_verify_password():
    password_to_check = request.json.get('password')

    if not password_to_check:
        return jsonify({'success': False, 'message': 'Password is required'}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT password FROM admin WHERE id = %s", (current_user.id,))
    admin = cursor.fetchone()
    cursor.close()

    if admin and check_password_hash(admin['password'], password_to_check):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'รหัสผ่านไม่ถูกต้อง'})


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
@admin_required # ใช้ decorator สำหรับ admin
def attendance_students():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลการลงทะเบียนทั้งหมดในระบบ
    # เพิ่มการ JOIN กับตาราง instructor เพื่อดึงชื่อผู้สอนมาแสดงผลด้วย
    cursor.execute("""
        SELECT 
            rc.registered_at,
            u.first_name,
            u.last_name,
            c.title as course_title,
            i.first_name AS instructor_first_name,
            i.last_name AS instructor_last_name
        FROM registered_courses rc
        JOIN user u ON rc.user_id = u.id
        JOIN courses c ON rc.course_id = c.id
        JOIN instructor i ON c.instructor_id = i.id
        ORDER BY rc.registered_at DESC
    """)
    
    enrollments = cursor.fetchall()
    cursor.close()

    return render_template('admin/attendance_students.html', enrollments=enrollments)

@app.route('/admin/enrollment-report')
@admin_required
def admin_enrollment_report():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # --- VVVVVV แก้ไข Query ให้ดึงชื่อมาตรงๆ VVVVVV ---
    cursor.execute("""
        SELECT
            u.first_name,                       -- <--- ไม่ใช้ AS user_first_name
            u.last_name,                        -- <--- ไม่ใช้ AS user_last_name
            c.title AS course_title,
            i.first_name AS instructor_first_name,
            i.last_name AS instructor_last_name,
            rc.registered_at
        FROM registered_courses rc
        JOIN user u ON rc.user_id = u.id
        JOIN courses c ON rc.course_id = c.id
        LEFT JOIN instructor i ON c.instructor_id = i.id
        ORDER BY rc.registered_at DESC
    """)
    enrollments = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/enrollment_report.html', enrollments=enrollments)

@app.route('/admin/attendance/exams')
@admin_required # ใช้ decorator สำหรับ admin
def attendance_exams():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงประวัติการทำข้อสอบทั้งหมดในระบบ
    # เพิ่มการ JOIN กับตาราง instructor เพื่อดึงชื่อผู้สอนมาแสดงผลด้วย
    cursor.execute("""
        SELECT 
            u.first_name,
            u.last_name,
            c.title AS course_title,
            q.quiz_name,
            i.first_name AS instructor_first_name,
            i.last_name AS instructor_last_name,
            uqa.attempt_date,
            uqa.score,
            uqa.passed
        FROM user_quiz_attempts uqa
        JOIN user u ON uqa.user_id = u.id
        JOIN quiz q ON uqa.quiz_id = q.quiz_id
        JOIN lesson l ON q.lesson_id = l.lesson_id
        JOIN courses c ON l.course_id = c.id
        JOIN instructor i ON c.instructor_id = i.id
        ORDER BY uqa.attempt_date DESC
    """)
    
    quiz_attempts = cursor.fetchall()
    cursor.close()

    return render_template('admin/attendance_exams.html', quiz_attempts=quiz_attempts)

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
@login_required 
def edit_course(course_id):
    # ตรวจสอบสิทธิ์ ว่าเป็น admin หรือ instructor เท่านั้น
    if current_user.role not in ['admin', 'instructor']:
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('home'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    current_role = current_user.role

    # --- ส่วนจัดการการบันทึกฟอร์ม (POST Request) ---
    if request.method == 'POST':
        # 1. รับข้อมูลจากฟอร์ม
        title = request.form['title']
        instructor_id = request.form['instructor_id']
        category_id = request.form['category_id']
        description = request.form['description']
        status = request.form['status']
        
        # --- VVVVVV ส่วนที่เพิ่มเข้ามา: จัดการไฟล์ VVVVVV ---

        # 2. ดึงชื่อไฟล์เดิมจากฐานข้อมูลมาก่อน
        cursor.execute("SELECT featured_image, featured_video FROM courses WHERE id = %s", (course_id,))
        current_files = cursor.fetchone()
        image_filename = current_files.get('featured_image')
        video_filename = current_files.get('featured_video')

        # 3. จัดการรูปภาพใหม่ (ถ้ามี)
        image_file = request.files.get('course_image')
        if image_file and image_file.filename != '' and allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            # สร้างชื่อไฟล์ใหม่ที่ไม่ซ้ำกัน
            unique_prefix = f"{course_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            image_filename = secure_filename(f"{unique_prefix}_{image_file.filename}")
            # บันทึกไฟล์
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER_COURSE_IMAGES'], image_filename))

        # 4. จัดการวิดีโอใหม่ (ถ้ามี)
        video_file = request.files.get('featured_video')
        if video_file and video_file.filename != '' and allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
            unique_prefix = f"{course_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            video_filename = secure_filename(f"{unique_prefix}_{video_file.filename}")
            video_file.save(os.path.join(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], video_filename))

        # --- ^^^^^^ สิ้นสุดส่วนที่เพิ่มเข้ามา ^^^^^^ ---
        
        # 5. อัปเดตข้อมูลในฐานข้อมูล (เพิ่ม featured_image และ featured_video)
        cursor.execute("""
            UPDATE courses 
            SET title = %s, instructor_id = %s, categories_id = %s, 
                description = %s, status = %s, featured_image = %s, featured_video = %s
            WHERE id = %s
        """, (title, instructor_id, category_id, description, status, image_filename, video_filename, course_id))
        
        mysql.connection.commit()
        cursor.close()
        flash('อัปเดตหลักสูตรเรียบร้อยแล้ว!', 'success')
        
        # Redirect กลับไปหน้า dashboard ของแต่ละ role
        if current_role == 'admin':
            return redirect(url_for('admin_dashboard')) 
        else:
            return redirect(url_for('instructor_dashboard'))

    # --- ส่วนแสดงข้อมูลเดิมในฟอร์ม (GET Request) ---
    # (โค้ดส่วนนี้ของคุณถูกต้องแล้ว ไม่ต้องแก้ไข)
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course_data = cursor.fetchone()
    cursor.execute("SELECT id, first_name, last_name FROM instructor")
    instructors = cursor.fetchall()
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    cursor.close()

    if not course_data:
        flash('ไม่พบหลักสูตรที่ต้องการแก้ไข', 'danger')
        if current_role == 'admin':
            return redirect(url_for('admin_dashboard')) 
        else:
            return redirect(url_for('instructor_dashboard'))

    return render_template(f'{current_role}/edit_course.html', 
                           course=course_data, 
                           instructors=instructors, 
                           categories=categories)




@app.route('/admin/course/delete/<int:course_id>', methods=['POST'])
@admin_required
def delete_course(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # 1. ค้นหาชื่อไฟล์ก่อนลบ
        cursor.execute("SELECT featured_image, featured_video FROM courses WHERE id = %s", (course_id,))
        course_files = cursor.fetchone()

        if not course_files:
            flash('ไม่พบหลักสูตรที่ต้องการลบ', 'danger')
            return redirect(url_for('course_list')) # <--- แก้ไขตรงนี้

        # 2. ลบข้อมูลออกจากฐานข้อมูล
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        mysql.connection.commit()

        # 3. ลบไฟล์ออกจากเซิร์ฟเวอร์
        if course_files.get('featured_image'):
            image_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_IMAGES'], course_files['featured_image'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        if course_files.get('featured_video'):
            video_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], course_files['featured_video'])
            if os.path.exists(video_path):
                os.remove(video_path)

        flash('ลบหลักสูตรเรียบร้อยแล้ว', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'เกิดข้อผิดพลาดในการลบหลักสูตร: {str(e)}', 'danger')
    finally:
        cursor.close()

    # --- VVVVVV แก้ไข redirect ให้ตรงกับชื่อฟังก์ชัน VVVVVV ---
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
    form = LessonForm()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูล Courses มาใส่ใน Dropdown
    cursor.execute('SELECT id, title FROM courses WHERE status = "publish" ORDER BY title')
    courses_data = cursor.fetchall()
    form.course_id.choices = [(course['id'], course['title']) for course in courses_data]
    form.course_id.choices.insert(0, (0, '-- เลือกหลักสูตร --'))

    # ดึงข้อมูล Instructors มาใส่ใน Dropdown
    cursor.execute('SELECT id, first_name, last_name FROM instructor ORDER BY first_name')
    instructors_data = cursor.fetchall()
    form.instructor_id.choices = [(ins['id'], f"{ins['first_name']} {ins['last_name']}") for ins in instructors_data]
    form.instructor_id.choices.insert(0, (0, '-- เลือกผู้สอน --'))

    if form.validate_on_submit():
        lesson_name = form.title.data
        course_id = form.course_id.data
        instructor_id = form.instructor_id.data
        lesson_date = form.lesson_date.data
        description = form.description.data # (เพิ่มการดึง description)

        if course_id == 0:
            flash('กรุณาเลือกหลักสูตร', 'danger')
        elif instructor_id == 0:
            flash('กรุณาเลือกผู้สอน', 'danger')
        else:
            if lesson_date is None:
                lesson_date = datetime.now().date()

            # แก้ไข INSERT query ให้ถูกต้อง
            cursor.execute(
                'INSERT INTO lesson (lesson_name, course_id, instructor_id, lesson_date, description) VALUES (%s, %s, %s, %s, %s)',
                (lesson_name, course_id, instructor_id, lesson_date, description)
            )
            mysql.connection.commit()
            
            flash('เพิ่มบทเรียนใหม่สำเร็จ!', 'success')
            # (ตรวจสอบให้แน่ใจว่าคุณมี endpoint 'admin_manage_lessons' อยู่จริง)
            return redirect(url_for('admin_dashboard')) 

    cursor.close()
    return render_template('admin/add_lesson.html', form=form)

# VVVVVV แก้ไขบรรทัดนี้ให้ถูกต้อง VVVVVV
@app.route('/admin/lesson/edit/<int:lesson_id>', methods=['GET', 'POST'])
@admin_required
def edit_lesson(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลบทเรียนและชื่อคอร์ส
    cursor.execute("""
        SELECT l.lesson_id, l.lesson_name, l.lesson_date, l.course_id, c.title as course_name
        FROM lesson l
        JOIN courses c ON l.course_id = c.id
        WHERE l.lesson_id = %s
    """, (lesson_id,))
    lesson_data = cursor.fetchone()

    if not lesson_data:
        flash('ไม่พบบทเรียน', 'danger')
        cursor.close()
        return redirect(url_for('admin_dashboard'))

    # 2. สร้างฟอร์มจาก WTForms
    form = LessonForm()

    # 3. ส่วนจัดการการบันทึกข้อมูล (POST)
    if form.validate_on_submit():
        updated_title = form.title.data
        updated_lesson_date = form.lesson_date.data

        # อัปเดตเฉพาะ title และ date
        cursor.execute("""
            UPDATE lesson SET lesson_name = %s, lesson_date = %s
            WHERE lesson_id = %s
        """, (updated_title, updated_lesson_date, lesson_id))
        
        mysql.connection.commit()
        cursor.close()
        flash('บทเรียนได้รับการแก้ไขเรียบร้อยแล้ว!', 'success')
        return redirect(url_for('admin_dashboard'))

    # 4. ส่วนแสดงข้อมูลครั้งแรก (GET)
    form.title.data = lesson_data['lesson_name']
    form.lesson_date.data = lesson_data['lesson_date']

    # 5. สร้าง Object ซ้อนกันเพื่อให้ HTML ของคุณใช้งานได้
    class TempCourse:
        def __init__(self, name, id):
            self.course_name = name
            self.id = id

    class TempLesson:
        def __init__(self, data, course_obj):
            self.id = data['lesson_id']
            self.course = course_obj

    course_object = TempCourse(lesson_data['course_name'], lesson_data['course_id'])
    lesson_for_template = TempLesson(lesson_data, course_object)

    cursor.close()
    return render_template('admin/edit_lesson.html', form=form, lesson=lesson_for_template)

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

    # ดึงข้อมูลบทเรียนหลัก
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson_data = cursor.fetchone()

    if not lesson_data:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('admin_dashboard'))

    # สร้าง object จำลอง lesson สำหรับเทมเพลต (เพื่อให้เข้าถึง lesson.title หรือ lesson.lesson_id ได้)
    lesson_obj_for_template = type('Lesson', (object,), {
        'title': lesson_data['lesson_name'],
        'lesson_id': lesson_data['lesson_id']
    })()


    if request.method == 'POST':
        selected_quiz_id = request.form.get('quiz_id')

        if not selected_quiz_id:
            flash('กรุณาเลือกแบบทดสอบ', 'danger')
            cursor.close()
            return redirect(url_for('add_quiz_to_lesson', lesson_id=lesson_id))

        # ตรวจสอบว่าแบบทดสอบนี้มีอยู่จริงหรือไม่
        cursor.execute("SELECT quiz_name FROM quiz WHERE quiz_id = %s", (selected_quiz_id,))
        quiz_info = cursor.fetchone()

        if not quiz_info:
            flash('ไม่พบแบบทดสอบที่เลือก', 'danger')
            cursor.close()
            return redirect(url_for('add_quiz_to_lesson', lesson_id=lesson_id))

        quiz_name_to_link = quiz_info['quiz_name']

        # ตรวจสอบว่าแบบทดสอบนี้ผูกกับบทเรียนนี้อยู่แล้วหรือไม่
        cursor.execute("""
            SELECT * FROM quiz_video
            WHERE lesson_id = %s AND quiz_id = %s
        """, (lesson_id, selected_quiz_id))
        existing_link = cursor.fetchone()

        if existing_link:
            flash('แบบทดสอบนี้ถูกเพิ่มในบทเรียนนี้แล้ว', 'warning')
        else:
            try:
                # เพิ่ม entry ในตาราง quiz_video เพื่อผูกแบบทดสอบกับบทเรียน
                # (video_id เป็น PK, quiz_id เป็น FK, title เป็นชื่อแบบทดสอบ)
                cursor.execute("""
                    INSERT INTO quiz_video (lesson_id, quiz_id, title)
                    VALUES (%s, %s, %s)
                """, (lesson_id, selected_quiz_id, quiz_name_to_link))
                mysql.connection.commit()
                flash('เพิ่มแบบทดสอบเข้าสู่บทเรียนสำเร็จ', 'success')
            except Exception as e:
                mysql.connection.rollback()
                flash(f'เกิดข้อผิดพลาดในการเพิ่มแบบทดสอบ: {str(e)}', 'danger')
        
        cursor.close()
        return redirect(url_for('quiz_and_video', lesson_id=lesson_id))

    # สำหรับ GET request: ดึงแบบทดสอบที่มีอยู่ทั้งหมดมาให้เลือก
    cursor.execute("""
        SELECT q.quiz_id, q.quiz_name, l.lesson_name
        FROM quiz q
        LEFT JOIN lesson l ON q.lesson_id = l.lesson_id
        ORDER BY q.quiz_name ASC
    """)
    available_quizzes = cursor.fetchall()
    
    cursor.close()
    return render_template('admin/add_quiz_to_lesson.html', 
                           lesson=lesson_obj_for_template, 
                           available_quizzes=available_quizzes)


@app.route('/admin/lesson/<int:lesson_id>/add_video', methods=['GET', 'POST'])
@admin_required
def add_video(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        time_duration = request.form.get('time_duration')
        
        # --- VVVVVV ส่วนที่แก้ไขทั้งหมด VVVVVV ---
        
        video_source = request.form.get('video_source')
        youtube_link = None
        video_filename = None

        if video_source == 'youtube':
            youtube_link = request.form.get('youtube_link')
        
        elif video_source == 'upload':
            video_file = request.files.get('video_file')
            if video_file and allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                original_filename, file_extension = os.path.splitext(video_file.filename)
                timestamp = str(int(time.time()))
                video_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")
                
                video_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], video_filename)
                video_file.save(video_path)

        # จัดการรูปภาพตัวอย่าง
        image_file = request.files.get('video_image')
        image_filename = None
        if image_file and allowed_file(image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            original_filename, file_extension = os.path.splitext(image_file.filename)
            timestamp = str(int(time.time()))
            image_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")
            
            image_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEO_IMAGES'], image_filename)
            image_file.save(image_path)

        # บันทึกลงฐานข้อมูล (เพิ่มคอลัมน์ video_file)
        try:
            cursor.execute("""
                INSERT INTO quiz_video (lesson_id, title, description, time_duration, youtube_link, video_file, video_image)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (lesson_id, title, description, time_duration, youtube_link, video_filename, image_filename))
            mysql.connection.commit()
            cursor.close()
            flash('เพิ่มวิดีโอใหม่สำเร็จ!', 'success')
            # (ตรวจสอบให้แน่ใจว่าคุณมี endpoint 'quiz_and_video' อยู่จริง)
            return redirect(url_for('quiz_and_video', lesson_id=lesson_id))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
            return redirect(url_for('add_video', lesson_id=lesson_id))

    # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

    cursor.close()
    return render_template('admin/add_video.html', lesson=lesson)




@app.route('/admin/video/<int:video_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_video(video_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลวิดีโอปัจจุบัน
    cursor.execute("SELECT * FROM quiz_video WHERE video_id = %s", (video_id,))
    video = cursor.fetchone()

    if not video:
        flash('ไม่พบวิดีโอที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('admin_dashboard'))

    # 2. เตรียมข้อมูลบทเรียนสำหรับเทมเพลต (สำคัญมาก)
    lesson_id_from_video = video.get('lesson_id') # ดึง lesson_id จากข้อมูลวิดีโอ
    
    # สร้างอ็อบเจกต์จำลอง lesson โดยมีค่าเริ่มต้นที่ปลอดภัย
    # นี่คือการสร้างคลาสชั่วคราวแบบ anonymous เพื่อให้มี attribute เหมือน lesson object ใน ORM
    TempLessonForTemplate = type('Lesson', (object,), {
        'title': 'บทเรียนไม่ทราบชื่อ', # ค่าเริ่มต้นที่ปลอดภัย
        'lesson_id': None # ค่าเริ่มต้นที่ปลอดภัย
    })

    lesson_obj_for_template = TempLessonForTemplate() # สร้าง instance ด้วยค่าเริ่มต้น

    if lesson_id_from_video:
        cursor.execute("SELECT lesson_id, lesson_name FROM lesson WHERE lesson_id = %s", (lesson_id_from_video,))
        lesson_data = cursor.fetchone()
        if lesson_data:
            lesson_obj_for_template.title = lesson_data['lesson_name']
            lesson_obj_for_template.lesson_id = lesson_data['lesson_id']
        else:
            # กรณีที่ lesson_id มีอยู่แต่หาบทเรียนไม่เจอ
            lesson_obj_for_template.title = 'ไม่พบบทเรียน (ID: {})'.format(lesson_id_from_video)
            lesson_obj_for_template.lesson_id = lesson_id_from_video
    else:
        # กรณีที่ video_id นั้นไม่มี lesson_id ผูกอยู่เลย (อาจเป็นข้อมูลที่ไม่สมบูรณ์)
        lesson_obj_for_template.title = 'ไม่พบบทเรียนที่เชื่อมโยง'
        lesson_obj_for_template.lesson_id = None # ไม่มี lesson_id ให้ผูก


    if request.method == 'POST':
        title = request.form['title']
        youtube_link = request.form['youtube_link']
        description = request.form.get('description', '')
        time_duration = request.form.get('time_duration', '')
        
        # จัดการการอัปโหลดรูปภาพใหม่ (โค้ดเดิมที่ถูกต้องแล้ว)
        new_video_image = request.files.get('video_image')
        filename = video['video_image'] # ใช้ชื่อไฟล์เดิมเป็นค่าเริ่มต้น

        if new_video_image and new_video_image.filename != '' and allowed_file(new_video_image.filename, ALLOWED_IMAGE_EXTENSIONS):
            filename = secure_filename(new_video_image.filename)
            upload_path = os.path.join(current_app.root_path, 'static/video_images')
            os.makedirs(upload_path, exist_ok=True)
            new_video_image.save(os.path.join(upload_path, filename))
        elif not new_video_image and not video['video_image']:
            filename = '' # หรือ 'default.jpg' ถ้าคุณต้องการภาพเริ่มต้น
            
        # อัปเดตข้อมูลในฐานข้อมูล
        cursor.execute("""
            UPDATE quiz_video
            SET title=%s, youtube_link=%s, description=%s, time_duration=%s, video_image=%s
            WHERE video_id=%s
        """, (title, youtube_link, description, time_duration, filename, video_id))
        mysql.connection.commit()
        cursor.close()

        flash('แก้ไขวิดีโอเรียบร้อยแล้ว', 'success')
        # เปลี่ยนเส้นทางกลับไปที่หน้า quiz_and_video ของบทเรียนที่เกี่ยวข้อง
        # ตรวจสอบให้แน่ใจว่า lesson_id_from_video ไม่ใช่ None ก่อนส่ง
        redirect_lesson_id = lesson_id_from_video if lesson_id_from_video is not None else lesson_obj_for_template.lesson_id
        if redirect_lesson_id is None:
             # ถ้าไม่มี lesson_id เลย ให้เปลี่ยนเส้นทางไปที่ admin_dashboard แทน
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('quiz_and_video', lesson_id=redirect_lesson_id))

    cursor.close()
    return render_template('admin/edit_video.html', video=video, lesson=lesson_obj_for_template)


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
    
    # ดึงบทเรียนทั้งหมดมาแสดงใน dropdown (เหมือนเดิม)
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson ORDER BY lesson_name")
    lessons = cursor.fetchall()

    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name')
        quiz_type = request.form.get('quiz_type')
        passing_percentage = request.form.get('passing_percentage')
        lesson_id = request.form.get('lesson_id', type=int) 

        # 1. ตรวจสอบว่าผู้ใช้เลือกบทเรียนแล้วจริงๆ
        if not lesson_id or lesson_id == 0:
            flash('กรุณาเลือกบทเรียนที่ต้องการเพิ่มแบบทดสอบ', 'danger')
            # ส่ง lessons กลับไปที่ template อีกครั้ง
            return render_template('admin/add_quiz.html', lessons=lessons)

        # 2. ตรวจสอบว่ากรอกข้อมูลครบถ้วน
        if not all([quiz_name, quiz_type, passing_percentage]):
            flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'danger')
            return render_template('admin/add_quiz.html', lessons=lessons)
            
        # 3. บันทึกข้อมูลลงฐานข้อมูล (เพิ่ม try-except)
        try:
            cursor.execute("""
                INSERT INTO quiz (quiz_name, lesson_id, passing_percentage, quiz_date, quiz_type)
                VALUES (%s, %s, %s, NOW(), %s)
            """, (quiz_name, lesson_id, passing_percentage, quiz_type))
            mysql.connection.commit()
            
            flash('เพิ่มแบบทดสอบใหม่สำเร็จ!', 'success')
            
            # --- VVVVVV แก้ไข redirect ให้ส่ง lesson_id ไปด้วย VVVVVV ---
            return redirect(url_for('quiz_list', lesson_id=lesson_id)) 
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}', 'danger')
        finally:
            cursor.close()
        # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

    cursor.close()
    return render_template('admin/add_quiz.html', lessons=lessons)



# ตัวอย่างหน้า edit และ delete (คุณสามารถเพิ่มเองได้ตามโครงสร้างนี้)
@app.route('/admin/quiz/edit/', defaults={'quiz_id': 0}, methods=['GET', 'POST'])
@app.route('/admin/quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
def edit_quiz(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # ✅ กำหนด choices สำหรับ quiz_type (ใช้กับ QuizForm)
    quiz_type_choices = [('Pre-test', 'Pre-test'), ('Post_test', 'Post-test')]

    # ✅ ดึงรายการบทเรียนทั้งหมดมาเพื่อเติม choices ให้กับ lesson_id (ใช้กับ QuizForm)
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson ORDER BY lesson_name ASC")
    lessons_for_choices = cursor.fetchall()
    lesson_id_choices = [(l['lesson_id'], l['lesson_name']) for l in lessons_for_choices]
    lesson_id_choices.insert(0, (0, '-- เลือกบทเรียน --'))


    # === Logic สำหรับหน้าเลือกแบบทดสอบ (ถ้า quiz_id เป็น 0 หรือไม่ได้ระบุ) ===
    if quiz_id == 0:
        form = QuizSelectionForm() # ✅ ใช้ QuizSelectionForm
        
        # ✅ กำหนด choices สำหรับ select_quiz_id
        cursor.execute("""
            SELECT q.quiz_id, q.quiz_name, l.lesson_name
            FROM quiz q
            LEFT JOIN lesson l ON q.lesson_id = l.lesson_id
            ORDER BY q.quiz_name ASC
        """)
        all_quizzes_for_selection = cursor.fetchall()
        form.select_quiz_id.choices = [(q['quiz_id'], f"{q['quiz_name']} (บทเรียน: {q['lesson_name'] or 'ไม่ระบุ'})") for q in all_quizzes_for_selection]
        form.select_quiz_id.choices.insert(0, (0, '-- เลือกแบบทดสอบ --'))

        if request.method == 'POST':
            if form.validate_on_submit(): # ✅ ตรวจสอบ validation ของ QuizSelectionForm
                selected_quiz_id = form.select_quiz_id.data # ✅ รับค่าจาก form.select_quiz_id.data
                if selected_quiz_id and int(selected_quiz_id) != 0:
                    return redirect(url_for('edit_quiz', quiz_id=selected_quiz_id))
                else:
                    flash('กรุณาเลือกแบบทดสอบที่ต้องการแก้ไข', 'danger')
            else:
                flash('กรุณาเลือกแบบทดสอบที่ถูกต้อง', 'danger') # ข้อความทั่วไปสำหรับ selection form error
                print(f"DEBUG: Quiz Selection Form Errors: {form.errors}") # Debugging selection form errors
            
        cursor.close()
        return render_template('admin/edit_quiz.html', form=form, selection_mode=True)


    # === Logic สำหรับหน้าแก้ไขแบบทดสอบจริง (เมื่อ quiz_id ถูกส่งมา) ===
    form = QuizForm() # ✅ ใช้ QuizForm สำหรับโหมดแก้ไข
    form.quiz_type.choices = quiz_type_choices # กำหนด choices
    form.lesson_id.choices = lesson_id_choices # กำหนด choices

    cursor.execute("SELECT * FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz_data = cursor.fetchone()

    if not quiz_data:
        flash('ไม่พบแบบทดสอบที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('edit_quiz')) # Redirect กลับไปหน้าเลือกแบบทดสอบ

    # เติมข้อมูลลงในฟอร์มสำหรับการแก้ไข (เฉพาะเมื่อเป็น GET request)
    if request.method == 'GET':
        form.quiz_name.data = quiz_data.get('quiz_name')
        form.quiz_type.data = quiz_data.get('quiz_type')
        form.passing_percentage.data = quiz_data.get('passing_percentage')
        form.lesson_id.data = quiz_data.get('lesson_id') # ป้อน lesson_id เดิมของแบบทดสอบ


    # ดึงคำถามที่เกี่ยวข้องกับแบบทดสอบนี้
    questions = []
    cursor.execute("SELECT * FROM questions WHERE quiz_id = %s", (quiz_id,))
    questions = cursor.fetchall()


    # สร้าง lesson_obj_for_template (เหมือนเดิม)
    lesson_id_from_quiz = quiz_data.get('lesson_id')
    lesson_obj_for_template = None
    if lesson_id_from_quiz:
        cursor.execute("SELECT lesson_id, lesson_name, course_id FROM lesson WHERE lesson_id = %s", (lesson_id_from_quiz,))
        lesson_data = cursor.fetchone()
        if lesson_data:
            cursor.execute("SELECT title FROM courses WHERE id = %s", (lesson_data['course_id'],))
            course_data = cursor.fetchone()
            course_name_for_lesson = course_data['title'] if course_data else "ไม่ทราบชื่อคอร์ส"
            lesson_obj_for_template = LessonForTemplate(lesson_data['lesson_id'], lesson_data['lesson_name'], lesson_data['course_id'], course_name_for_lesson)
        else:
            lesson_obj_for_template = LessonForTemplate(quiz_id, 'ไม่พบบทเรียน (ID: {})'.format(lesson_id_from_quiz), None, "ไม่ทราบชื่อคอร์ส")
    else:
        lesson_obj_for_template = LessonForTemplate(quiz_id, 'ไม่พบบทเรียนที่เชื่อมโยง', None, "ไม่ทราบชื่อคอร์ส")
    
    
    if form.validate_on_submit(): # จะทำงานเมื่อ submit ฟอร์มแก้ไข
        print(f"\n--- DEBUG: Admin Edit Quiz - Form Validation PASSED for quiz_id: {quiz_id} ---")
        updated_quiz_name = form.quiz_name.data
        updated_quiz_type = form.quiz_type.data
        updated_passing_percentage = form.passing_percentage.data
        updated_lesson_id = form.lesson_id.data

        if updated_lesson_id == 0:
            flash('กรุณาเลือกบทเรียนที่เกี่ยวข้อง', 'danger')
            cursor.close()
            print(f"DEBUG: Validation failed: updated_lesson_id is 0.")
            return render_template('admin/edit_quiz.html', quiz=quiz_data, questions=questions, lesson=lesson_obj_for_template, form=form, selection_mode=False)

        try:
            cursor.execute("""
                UPDATE quiz SET
                    quiz_name = %s,
                    quiz_type = %s,
                    passing_percentage = %s,
                    lesson_id = %s
                WHERE quiz_id = %s
            """, (updated_quiz_name, updated_quiz_type, updated_passing_percentage, updated_lesson_id, quiz_id))
            
            mysql.connection.commit()
            flash('แก้ไขแบบทดสอบเรียบร้อยแล้ว!', 'success')
            cursor.close()
            print(f"DEBUG: Database update successful for quiz_id: {quiz_id}.")

            if lesson_id_from_quiz is None:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('quiz_and_video', lesson_id=lesson_id_from_quiz))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึก: {str(e)}', 'danger')
            cursor.close()
            print(f"ERROR: Database update failed for quiz_id {quiz_id}: {e}")
            return render_template('admin/edit_quiz.html', quiz=quiz_data, questions=questions, lesson=lesson_obj_for_template, form=form, selection_mode=False)
    else: # ✅ เพิ่ม else block สำหรับ form.validate_on_submit()
        print(f"\n--- DEBUG: Admin Edit Quiz - Form Validation FAILED for quiz_id: {quiz_id} ---")
        print(f"DEBUG: Form Errors: {form.errors}") # ✅ พิมพ์ข้อผิดพลาดของฟอร์ม
        # ฟังก์ชันจะเรนเดอร์เทมเพลตเดิม (admin/edit_quiz.html) โดยอัตโนมัติ
        # และแสดงข้อผิดพลาดของฟอร์ม (ถ้าเทมเพลตมีการแสดงผล)

    cursor.close()
    return render_template('admin/edit_quiz.html', quiz=quiz_data, questions=questions, lesson=lesson_obj_for_template, form=form, selection_mode=False)

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
@admin_required # หรือ @instructor_required
def edit_question(question_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        # --- ส่วนของการรับข้อมูลและอัปเดต (POST) ---
        question_name = request.form['question_name']
        choice_a = request.form['choice_a']
        choice_b = request.form['choice_b']
        choice_c = request.form['choice_c']
        choice_d = request.form['choice_d']
        correct_answer = request.form['correct_answer']
        
        # ดึงชื่อไฟล์รูปเดิมมาก่อน
        cursor.execute("SELECT question_image FROM questions WHERE question_id = %s", (question_id,))
        question_image_filename = cursor.fetchone()['question_image']

        # ตรวจสอบว่ามีการอัปโหลดไฟล์ใหม่หรือไม่
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # (Optional) อาจจะต้องลบไฟล์รูปเก่าออกจาก server ที่นี่
                file.save(os.path.join(app.config['UPLOAD_FOLDER_QUESTION_IMAGES'], filename))
                question_image_filename = filename # อัปเดตเป็นชื่อไฟล์ใหม่

        # อัปเดตข้อมูลลงฐานข้อมูล
        cursor.execute("""
            UPDATE questions SET 
            question_name = %s, 
            question_image = %s,
            choice_a = %s,
            choice_b = %s,
            choice_c = %s,
            choice_d = %s,
            correct_answer = %s
            WHERE question_id = %s
        """, (question_name, question_image_filename, choice_a, choice_b, choice_c, choice_d, correct_answer, question_id))
        
        mysql.connection.commit()
        cursor.close()
        flash('แก้ไขคำถามเรียบร้อยแล้ว', 'success')
        # ตรงนี้ให้ redirect กลับไปหน้าจัดการเนื้อหาของบทเรียนนั้นๆ
        return redirect(url_for('admin_dashboard')) # ควรแก้ให้ไปยังหน้าที่ถูกต้อง
    
    # --- ส่วนของการดึงข้อมูลมาแสดง (GET) ---
    cursor.execute("SELECT * FROM questions WHERE question_id = %s", (question_id,))
    question = cursor.fetchone()
    cursor.close()

    if not question:
        flash('ไม่พบคำถามที่ต้องการแก้ไข', 'danger')
        return redirect(url_for('admin_dashboard'))

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
            # แยกชื่อไฟล์และนามสกุลออกจากกัน
            original_filename, file_extension = os.path.splitext(course_image.filename)
            # สร้างชื่อไฟล์ใหม่ที่ไม่ซ้ำกัน
            timestamp = str(int(time.time()))
            image_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")
            
            image_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_IMAGES'], image_filename)
            course_image.save(image_path)

        # วิดีโอแนะนำ (ใช้ชื่อ 'featured_video' ให้ตรงกับฐานข้อมูล)
        featured_video = request.files.get('featured_video')
        video_filename = None
        if featured_video and allowed_file(featured_video.filename, ALLOWED_VIDEO_EXTENSIONS):
            original_filename, file_extension = os.path.splitext(featured_video.filename)
            timestamp = str(int(time.time()))
            video_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")
            
            video_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], video_filename)
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



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # --- ส่วนกำหนดค่าตาม Role ---
    user_id = current_user.id
    current_role = current_user.role
    table_name, select_query_columns, update_query_template = None, None, None

    if current_role == 'admin':
        table_name = "admin"
        select_query_columns = "id, username, email, first_name, last_name, tel, gender, profile_image, role"
        update_query_template = "UPDATE admin SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s, profile_image=%s WHERE id=%s"
    elif current_role == 'instructor':
        table_name = "instructor"
        select_query_columns = "id, username, email, first_name, last_name, tel, gender, profile_image, role"
        update_query_template = "UPDATE instructor SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s, profile_image=%s WHERE id=%s"
    elif current_role == 'user':
        table_name = "user"
        select_query_columns = "id, username, email, first_name, last_name, id_card, gender, profile_image, role"
        update_query_template = "UPDATE user SET first_name=%s, last_name=%s, email=%s, username=%s, id_card=%s, gender=%s, profile_image=%s WHERE id=%s"

    if not table_name:
        flash("ไม่พบข้อมูลผู้ใช้สำหรับแก้ไข", "danger")
        return redirect(url_for('login'))

    # --- ส่วนจัดการฟอร์มเมื่อกดบันทึก (POST) ---
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # 1. รับข้อมูลจากฟอร์มและไฟล์
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            username = request.form['username']
            email = request.form['email']
            id_card = request.form.get('id_card') # สำหรับ user
            tel = request.form.get('tel') # สำหรับ admin/instructor
            gender = request.form.get('gender')

            profile_image_file = request.files.get('profile_image')
            cursor.execute(f"SELECT profile_image FROM {table_name} WHERE id = %s", (user_id,))
            current_user_data = cursor.fetchone()
            filename = current_user_data.get('profile_image')

            if profile_image_file and allowed_file(profile_image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                unique_prefix = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                filename = secure_filename(f"{unique_prefix}_{profile_image_file.filename}")
                upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER_PROFILE_IMAGES'])
                os.makedirs(upload_path, exist_ok=True)
                profile_image_file.save(os.path.join(upload_path, filename))

            # 2. อัปเดตลงฐานข้อมูล
            update_values = []
            if current_role in ['admin', 'instructor']:
                update_values = (first_name, last_name, email, username, tel, gender, filename, user_id)
            elif current_role == 'user':
                update_values = (first_name, last_name, email, username, id_card, gender, filename, user_id)

            cursor.execute(update_query_template, update_values)
            mysql.connection.commit()

            # --- 3. รีเฟรช Session ทันที ---
            cursor.execute(f"SELECT {select_query_columns} FROM {table_name} WHERE id = %s", (user_id,))
            updated_user_data = cursor.fetchone()

            user_obj = None
            if current_role == 'admin': user_obj = Admin(**updated_user_data)
            elif current_role == 'instructor': user_obj = Instructor(**updated_user_data)
            elif current_role == 'user': user_obj = User(**updated_user_data)

            if user_obj:
                login_user(user_obj, remember=True)

            flash('แก้ไขโปรไฟล์เรียบร้อยแล้ว!', 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึกโปรไฟล์: {str(e)}', 'danger')
        finally:
            cursor.close()

        # --- 4. Redirect กลับมาที่หน้าเดิม ---
        return redirect(url_for('edit_profile'))

    # --- สำหรับการแสดงหน้าเว็บครั้งแรก (GET) ---
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT {select_query_columns} FROM {table_name} WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()

    if not user_data:
        flash("ไม่พบข้อมูลโปรไฟล์", "danger")
        return redirect(url_for('login'))

    return render_template(f'{current_role}/edit_profile.html', user=user_data)

@app.route('/instructor/dashboard')
@login_required # ควรใช้ @instructor_required ถ้ามี
def instructor_dashboard():
    # ตรวจสอบสิทธิ์ว่าเป็นอาจารย์
    if current_user.role != 'instructor':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('home'))

    instructor_id = current_user.id
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. นับจำนวนคอร์สทั้งหมดของอาจารย์คนนี้
    cursor.execute("SELECT COUNT(id) as total FROM courses WHERE instructor_id = %s", (instructor_id,))
    course_count = cursor.fetchone()['total']

    # 2. นับจำนวนนักเรียนทั้งหมด (ที่ไม่ซ้ำกัน)
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as total 
        FROM registered_courses 
        WHERE course_id IN (SELECT id FROM courses WHERE instructor_id = %s)
    """, (instructor_id,))
    student_count = cursor.fetchone()['total']

    # 3. นับจำนวนบทเรียนทั้งหมด
    cursor.execute("""
        SELECT COUNT(lesson_id) as total 
        FROM lesson 
        WHERE course_id IN (SELECT id FROM courses WHERE instructor_id = %s)
    """, (instructor_id,))
    lesson_count = cursor.fetchone()['total']

    # 4. ดึงข้อมูลคอร์สล่าสุด 5 รายการ
    cursor.execute("""
        SELECT 
            c.id, c.title, c.status,
            (SELECT COUNT(user_id) FROM registered_courses WHERE course_id = c.id) as student_count
        FROM courses c
        WHERE c.instructor_id = %s
        ORDER BY c.id DESC
        LIMIT 5
    """, (instructor_id,))
    recent_courses = cursor.fetchall()

    cursor.close()

    # ส่งข้อมูลทั้งหมดไปที่หน้าเว็บ
    return render_template('instructor/instructor_dashboard.html',
                           course_count=course_count,
                           student_count=student_count,
                           lesson_count=lesson_count,
                           recent_courses=recent_courses)

@app.route('/registered_courses')
@login_required # เพิ่ม decorator เพื่อให้ต้องล็อกอินก่อน
def registered_courses():
    # ตรวจสอบสิทธิ์ว่าเป็นอาจารย์
    if current_user.role != 'instructor':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('home'))

    instructor_id = current_user.id
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลการลงทะเบียนทั้งหมดที่เกี่ยวข้องกับอาจารย์คนนี้
    cursor.execute("""
        SELECT 
            rc.registered_at,
            u.id as user_id,
            u.first_name,
            u.last_name,
            c.id as course_id,
            c.title as course_title
        FROM registered_courses rc
        JOIN user u ON rc.user_id = u.id
        JOIN courses c ON rc.course_id = c.id
        WHERE c.instructor_id = %s
        ORDER BY rc.registered_at DESC
    """, (instructor_id,))
    enrollments = cursor.fetchall()

    # 2. คำนวณความคืบหน้าสำหรับแต่ละการลงทะเบียน
    for enrollment in enrollments:
        user_id = enrollment['user_id']
        course_id = enrollment['course_id']
        
        # นับจำนวนเนื้อหาทั้งหมดในคอร์ส (วิดีโอ + Post-test)
        cursor.execute("""
            SELECT COUNT(qv.video_id) 
            FROM quiz_video qv 
            JOIN lesson l ON qv.lesson_id = l.lesson_id 
            WHERE l.course_id = %s
        """, (course_id,))
        total_items_result = cursor.fetchone()
        total_items = total_items_result['COUNT(qv.video_id)'] if total_items_result else 0

        # นับจำนวนวิดีโอที่ดูจบแล้ว
        cursor.execute("""
            SELECT COUNT(uvp.id) 
            FROM user_video_progress uvp
            JOIN quiz_video qv ON uvp.video_id = qv.video_id
            JOIN lesson l ON qv.lesson_id = l.lesson_id
            WHERE uvp.user_id = %s AND l.course_id = %s
        """, (user_id, course_id))
        completed_videos_result = cursor.fetchone()
        completed_videos = completed_videos_result['COUNT(uvp.id)'] if completed_videos_result else 0

        # นับจำนวน Post-test ที่ทำผ่านแล้ว
        cursor.execute("""
            SELECT COUNT(uqa.id)
            FROM user_quiz_attempts uqa
            JOIN quiz q ON uqa.quiz_id = q.quiz_id
            JOIN lesson l ON q.lesson_id = l.lesson_id
            WHERE uqa.user_id = %s AND l.course_id = %s AND q.quiz_type = 'Post_test' AND uqa.passed = 1
        """, (user_id, course_id))
        passed_post_tests_result = cursor.fetchone()
        passed_post_tests = passed_post_tests_result['COUNT(uqa.id)'] if passed_post_tests_result else 0

        completed_items = completed_videos + passed_post_tests
        
        progress = (completed_items / total_items) * 100 if total_items > 0 else 0
        enrollment['progress'] = progress

    cursor.close()

    return render_template('instructor/registered_courses.html', enrollments=enrollments)

@app.route('/instructor/attendance/exams')
@login_required
def instructor_attendance_exams():
    if current_user.role != 'instructor':
        flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
        return redirect(url_for('home'))

    instructor_id = current_user.id
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # VVVVVV แก้ไข Query: เพิ่ม l.lesson_name เข้าไปใน SELECT VVVVVV
    cursor.execute("""
        SELECT 
            u.first_name,
            u.last_name,
            c.title AS course_title,
            l.lesson_name, 
            q.quiz_name,
            uqa.attempt_date,
            uqa.score,
            uqa.passed
        FROM user_quiz_attempts uqa
        JOIN user u ON uqa.user_id = u.id
        JOIN quiz q ON uqa.quiz_id = q.quiz_id
        JOIN lesson l ON q.lesson_id = l.lesson_id
        JOIN courses c ON l.course_id = c.id
        WHERE c.instructor_id = %s
        ORDER BY uqa.attempt_date DESC
    """, (instructor_id,))
    
    quiz_attempts = cursor.fetchall()
    cursor.close()

    return render_template('instructor/attendance_exams.html', quiz_attempts=quiz_attempts)

@app.route('/instructor/categories', methods=['GET', 'POST'])
@instructor_required # ✅ แก้ไข: ใช้ @instructor_required เพื่อให้เฉพาะ Instructor เข้าถึงได้
def instructor_category():
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

    return render_template('instructor/category_list.html', categories=categories)

@app.route('/instructor/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@instructor_required # ✅ แก้ไข: ใช้ @instructor_required
def instructor_edit_category(category_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
    category = cursor.fetchone()

    if not category:
        flash('ไม่พบหมวดหมู่', 'danger')
        return redirect(url_for('instructor_category')) # ✅ แก้ไข: ชี้ไปที่ instructor_category

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
            return redirect(url_for('instructor_category')) # ✅ แก้ไข: ชี้ไปที่ instructor_category

    cursor.close()
    return render_template('instructor/edit_category.html', category=category)

@app.route('/instructor/categories/delete/<int:category_id>', methods=['POST'])
@instructor_required # ✅ แก้ไข: ใช้ @instructor_required
def instructor_delete_category(category_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    mysql.connection.commit()
    cursor.close()

    flash('ลบหมวดหมู่เรียบร้อยแล้ว', 'success')
    return redirect(url_for('instructor_category')) # ✅ แก้ไข: ชี้ไปที่ instructor_category

@app.route('/instructor/courses')
@instructor_required
def instructor_course_list():
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
    
    return render_template('instructor/course_list.html', courses=courses)

@app.route('/instructor/course/add', methods=['GET', 'POST'])
@instructor_required
def instructor_add_course():
    if request.method == 'POST':
        # 1. รับข้อมูลจากฟอร์ม
        course_name = request.form.get('course_name')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        status = request.form.get('status')
        
        # --- VVVVVV จุดที่แก้ไขทั้งหมด VVVVVV ---

        # 2. กำหนด ID ของผู้สอนเป็นคนที่ล็อกอินอยู่โดยอัตโนมัติ
        instructor_id = current_user.id

        # 3. จัดการรูปภาพหลักสูตร (ใช้ตรรกะสร้างชื่อไฟล์ใหม่)
        course_image = request.files.get('course_image')
        image_filename = None
        if course_image and allowed_file(course_image.filename, ALLOWED_IMAGE_EXTENSIONS):
            original_filename, file_extension = os.path.splitext(course_image.filename)
            timestamp = str(int(time.time()))
            image_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")
            image_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_IMAGES'], image_filename)
            course_image.save(image_path)

        # 4. จัดการวิดีโอแนะนำ (ใช้ตรรกะสร้างชื่อไฟล์ใหม่)
        featured_video = request.files.get('featured_video')
        video_filename = None
        if featured_video and allowed_file(featured_video.filename, ALLOWED_VIDEO_EXTENSIONS):
            original_filename, file_extension = os.path.splitext(featured_video.filename)
            timestamp = str(int(time.time()))
            video_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")
            video_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], video_filename)
            featured_video.save(video_path)

        # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

        # 5. บันทึกลงฐานข้อมูล (ใช้ instructor_id จาก current_user)
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO courses (title, instructor_id, categories_id, description, featured_image, featured_video, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (course_name, instructor_id, category_id, description, image_filename, video_filename, status))
            mysql.connection.commit()
            cursor.close()
            flash('เพิ่มหลักสูตรใหม่สำเร็จ!', 'success')
            return redirect(url_for('instructor_dashboard'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}', 'danger')
            return redirect(url_for('instructor_add_course'))

    # --- ส่วนของ GET (แสดงฟอร์ม) ---
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()
    cursor.close()
    
    return render_template('instructor/add_course.html', categories=categories)

@app.route('/instructor/course/edit/<int:course_id>', methods=['GET', 'POST']) # URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_edit_course(course_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_edit_course'
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor) # ใช้ DictCursor เพื่อให้เข้าถึงข้อมูลด้วยชื่อคอลัมน์ได้

    if request.method == 'POST':
        course_name = request.form['course_name']
        description = request.form['description']
        instructor_id = request.form['instructor_id'] # ID ของผู้สอนที่เลือก
        category_id = request.form['category_id']
        status = request.form['status'] # 'publish' หรือ 'draft'

        # รูปภาพหลักสูตร (ถ้ามีการอัปโหลดใหม่)
        course_image_file = request.files.get('course_image')
        image_filename = None # ค่าเริ่มต้น ถ้าไม่มีการอัปโหลดใหม่

        # ดึงชื่อรูปภาพเดิมจาก DB ก่อน เพื่อใช้เป็นค่าเริ่มต้น
        cur.execute("SELECT featured_image, featured_video FROM courses WHERE id = %s", (course_id,))
        existing_course_data = cur.fetchone()
        current_image = existing_course_data['featured_image'] if existing_course_data else None
        current_video = existing_course_data['featured_video'] if existing_course_data else None

        if course_image_file and allowed_file(course_image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            filename = secure_filename(course_image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename)
            course_image_file.save(image_path)
            image_filename = filename
        else:
            image_filename = current_image # ใช้รูปเดิมถ้าไม่อัปโหลดใหม่

        # วิดีโอแนะนำ (ถ้ามีการอัปโหลดใหม่)
        featured_video_file = request.files.get('featured_video')
        video_filename = None # ค่าเริ่มต้น

        if featured_video_file and allowed_file(featured_video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
            filename = secure_filename(featured_video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], filename)
            featured_video_file.save(video_path)
            video_filename = filename
        else:
            video_filename = current_video # ใช้วิดีโอเดิมถ้าไม่อัปโหลดใหม่


        cur.execute("""
            UPDATE courses SET
                title = %s,
                description = %s,
                instructor_id = %s,
                categories_id = %s,
                status = %s,
                featured_image = %s,
                featured_video = %s
            WHERE id = %s
        """, (course_name, description, instructor_id, category_id, status, image_filename, video_filename, course_id))

        mysql.connection.commit()
        flash('แก้ไขข้อมูลหลักสูตรเรียบร้อยแล้ว', 'success')
        cur.close()
        return redirect(url_for('instructor_course_list')) # ✅ กลับไปหน้ารายการหลักสูตรของ Instructor

    # สำหรับ GET request: ดึงข้อมูลหลักสูตรเดิมมาแสดงในฟอร์ม
    cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cur.fetchone()

    if not course:
        flash('ไม่พบหลักสูตรนี้', 'danger')
        cur.close()
        return redirect(url_for('instructor_course_list')) # ถ้าหาไม่เจอ ให้กลับไปหน้ารายการหลักสูตร

    # ดึง instructors (ต้องมี role instructor)
    cur.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS name FROM instructor")
    instructors = cur.fetchall()

    # ดึง categories
    cur.execute("SELECT id, name AS name FROM categories")
    categories = cur.fetchall()

    cur.close()
    # ✅ ใช้ template ของ Instructor
    return render_template('instructor/edit_course.html', course=course, instructors=instructors, categories=categories)

@app.route('/instructor/course/delete/<int:course_id>', methods=['POST'])
@instructor_required
def instructor_delete_course(course_id):
    instructor_id = current_user.id
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # --- VVVVVV ส่วนที่แก้ไขและเพิ่มเข้ามาทั้งหมด VVVVVV ---

        # 1. ตรวจสอบเพื่อความปลอดภัย: เช็คว่าคอร์สนี้เป็นของผู้สอนที่ล็อกอินอยู่จริงหรือไม่
        cursor.execute("SELECT featured_image, featured_video FROM courses WHERE id = %s AND instructor_id = %s", (course_id, instructor_id))
        course_files = cursor.fetchone()

        if not course_files:
            # ถ้าไม่พบคอร์ส หรือคอร์สไม่ได้เป็นของผู้สอนคนนี้
            flash('ไม่พบหลักสูตร หรือคุณไม่ได้รับอนุญาตให้ลบหลักสูตรนี้', 'danger')
            return redirect(url_for('instructor_dashboard'))

        # 2. ทำการลบข้อมูลออกจากฐานข้อมูลก่อน
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        mysql.connection.commit()

        # 3. ถ้าลบข้อมูลสำเร็จ ให้ทำการลบไฟล์ออกจากเซิร์ฟเวอร์
        # ลบไฟล์รูปภาพ (ถ้ามี)
        if course_files.get('featured_image'):
            # ใช้ Config Key ที่ถูกต้อง
            image_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_IMAGES'], course_files['featured_image'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # ลบไฟล์วิดีโอ (ถ้ามี)
        if course_files.get('featured_video'):
            # ใช้ Config Key ที่ถูกต้อง
            video_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], course_files['featured_video'])
            if os.path.exists(video_path):
                os.remove(video_path)

        # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

        flash('ลบหลักสูตรเรียบร้อยแล้ว', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'เกิดข้อผิดพลาดในการลบหลักสูตร: {str(e)}', 'danger')
    finally:
        cursor.close()

    # กลับไปหน้า Dashboard ของผู้สอน
    return redirect(url_for('instructor_dashboard'))


@app.route('/instructor/lesson/<int:course_id>')
@instructor_required
def instructor_lesson(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลหลักสูตร (course) เพื่อส่งไปแสดงใน template (เพื่อให้ lesson.course.course_name ในเทมเพลตใช้ได้)
    cursor.execute("SELECT id, title FROM courses WHERE id = %s", (course_id,))
    course_info = cursor.fetchone() # จะได้ข้อมูลคอร์สเป็น dictionary

    if not course_info:
        flash('ไม่พบหลักสูตรที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('instructor_course_list')) # หรือหน้าที่เหมาะสม

    # ดึงข้อมูลบทเรียน (lessons) ที่อยู่ในหลักสูตรนี้
    cursor.execute("""
    SELECT lesson_id, lesson_name, lesson_date, course_id
    FROM lesson 
    WHERE course_id = %s
    ORDER BY lesson_date DESC
    """, (course_id,))
    lesson_data_raw = cursor.fetchall() # ข้อมูลดิบจาก DB เป็น list of dicts

    lessons = []
    # สร้าง Object สำหรับ course ที่เกี่ยวข้องกับ lesson เพื่อให้ lesson.course.course_name ใช้งานได้
    # (เราจะใช้ course_info ตรงๆ สำหรับตัวแปร 'course' ที่ส่งไปเทมเพลต)
    # และใช้ course_info['title'] สำหรับการสร้าง LessonForTemplate
    
    for row in lesson_data_raw: # row แต่ละตัวคือ dictionary
        lesson_date = row['lesson_date']
        if isinstance(lesson_date, str):
            try:
                lesson_date = datetime.strptime(lesson_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                lesson_date = None

        # ✅ สร้าง LessonForTemplate object สำหรับแต่ละบทเรียน
        lessons.append(LessonForTemplate(
            lesson_id=row['lesson_id'],
            lesson_name=row['lesson_name'],
            course_id=row['course_id'],
            course_name=course_info['title'] # ใช้ชื่อคอร์สจาก course_info ที่ดึงมา
        ))

    cursor.close()
    # ✅ ส่ง course_info (ที่เป็น dictionary) และ lessons (list of LessonForTemplate objects) ไป
    return render_template('instructor/lesson.html', course=course_info, lessons=lessons)

@app.route('/instructor/lesson/<int:lesson_id>/quiz_and_video', methods=['GET', 'POST']) # ✅ เปลี่ยน URL ให้เป็นของ instructor
@instructor_required # ✅ ใช้ decorator สำหรับ Instructor
def instructor_quiz_and_video(lesson_id): # ✅ เปลี่ยนชื่อฟังก์ชันเพื่อให้ไม่ซ้ำกับของ admin
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลบทเรียนหลัก
    cursor.execute("SELECT * FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        return redirect(url_for('instructor_dashboard')) # ✅ ชี้ไปที่ dashboard ของ instructor

    # 1. ดึงข้อมูลแบบทดสอบ (Quizzes) ที่ผูกกับบทเรียนนี้
    cursor.execute("""
        SELECT
            qv.video_id AS qv_id,
            qv.lesson_id,
            q.quiz_id,
            q.quiz_name,
            q.quiz_type,
            q.quiz_date,
            l.lesson_name
        FROM quiz_video qv
        INNER JOIN quiz q ON qv.quiz_id = q.quiz_id
        INNER JOIN lesson l ON q.lesson_id = l.lesson_id
        WHERE qv.lesson_id = %s AND qv.quiz_id IS NOT NULL
        ORDER BY qv.video_id ASC
    """, (lesson_id,))
    quizzes_for_lesson = cursor.fetchall()

    # 2. ดึงข้อมูลวิดีโอ (Videos) ที่ผูกกับบทเรียนนี้
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
        WHERE qv.lesson_id = %s AND qv.quiz_id IS NULL
        ORDER BY qv.video_id ASC
    """, (lesson_id,))
    videos_for_lesson = cursor.fetchall()

    cursor.close()

    # ✅ เปลี่ยนไปใช้ template สำหรับ instructor
    return render_template('instructor/quiz_and_video.html',
                            lesson=lesson,
                            quizzes=quizzes_for_lesson,
                            videos=videos_for_lesson)
    
@app.route('/instructor/lesson/<int:lesson_id>/quiz/add', methods=['GET', 'POST']) # URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_add_quiz_to_lesson(lesson_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_add_quiz_to_lesson'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลบทเรียนหลัก
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson_data = cursor.fetchone()

    if not lesson_data:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('instructor_dashboard')) # ✅ ชี้ไปที่ dashboard ของ instructor

    lesson_obj_for_template = type('Lesson', (object,), {
        'title': lesson_data['lesson_name'],
        'lesson_id': lesson_data['lesson_id']
    })()

    if request.method == 'POST':
        selected_quiz_id = request.form.get('quiz_id')

        if not selected_quiz_id:
            flash('กรุณาเลือกแบบทดสอบ', 'danger')
            cursor.close()
            return redirect(url_for('instructor_add_quiz_to_lesson', lesson_id=lesson_id)) # ✅ ชี้ไปที่ instructor_add_quiz_to_lesson

        # ตรวจสอบว่าแบบทดสอบนี้มีอยู่จริงหรือไม่
        cursor.execute("SELECT quiz_name FROM quiz WHERE quiz_id = %s", (selected_quiz_id,))
        quiz_info = cursor.fetchone()

        if not quiz_info:
            flash('ไม่พบแบบทดสอบที่เลือก', 'danger')
            cursor.close()
            return redirect(url_for('instructor_add_quiz_to_lesson', lesson_id=lesson_id)) # ✅ ชี้ไปที่ instructor_add_quiz_to_lesson

        quiz_name_to_link = quiz_info['quiz_name']

        # ตรวจสอบว่าแบบทดสอบนี้ผูกกับบทเรียนนี้อยู่แล้วหรือไม่
        cursor.execute("""
            SELECT * FROM quiz_video
            WHERE lesson_id = %s AND quiz_id = %s
        """, (lesson_id, selected_quiz_id))
        existing_link = cursor.fetchone()

        if existing_link:
            flash('แบบทดสอบนี้ถูกเพิ่มในบทเรียนนี้แล้ว', 'warning')
        else:
            try:
                cursor.execute("""
                    INSERT INTO quiz_video (lesson_id, quiz_id, title)
                    VALUES (%s, %s, %s)
                """, (lesson_id, selected_quiz_id, quiz_name_to_link))
                mysql.connection.commit()
                flash('เพิ่มแบบทดสอบเข้าสู่บทเรียนสำเร็จ', 'success')
            except Exception as e:
                mysql.connection.rollback()
                flash(f'เกิดข้อผิดพลาดในการเพิ่มแบบทดสอบ: {str(e)}', 'danger')
        
        cursor.close()
        return redirect(url_for('instructor_quiz_and_video', lesson_id=lesson_id)) # ✅ ชี้ไปที่ instructor_quiz_and_video

    # สำหรับ GET request: ดึงแบบทดสอบที่มีอยู่ทั้งหมดมาให้เลือก
    cursor.execute("""
        SELECT q.quiz_id, q.quiz_name, l.lesson_name
        FROM quiz q
        LEFT JOIN lesson l ON q.lesson_id = l.lesson_id
        ORDER BY q.quiz_name ASC
    """)
    available_quizzes = cursor.fetchall()
    
    cursor.close()
    return render_template('instructor/add_quiz_to_lesson.html', 
                           lesson=lesson_obj_for_template, 
                           available_quizzes=available_quizzes)
    
@app.route('/instructor/lesson/<int:lesson_id>/add_video', methods=['GET', 'POST'])
@instructor_required
def instructor_add_video(lesson_id): # <--- ตรวจสอบชื่อฟังก์ชันให้ตรงกับของคุณ
    # ดึงข้อมูลบทเรียนมาแสดง
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        time_duration = request.form.get('time_duration')
        
        video_source = request.form.get('video_source') # รับค่าจาก radio button
        youtube_link = None
        video_filename = None

        if video_source == 'youtube':
            youtube_link = request.form.get('youtube_link')
        
        elif video_source == 'upload':
            video_file = request.files.get('video_file')
            if video_file and allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
                # สร้างชื่อไฟล์ใหม่ที่ไม่ซ้ำกัน
                original_filename, file_extension = os.path.splitext(video_file.filename)
                timestamp = str(int(time.time()))
                video_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")
                
                video_path = os.path.join(app.config['UPLOAD_FOLDER_COURSE_VIDEOS'], video_filename)
                video_file.save(video_path)

        # จัดการรูปภาพตัวอย่าง (ใช้ตรรกะสร้างชื่อไฟล์ใหม่เหมือนกัน)
        video_image = request.files.get('video_image')
        image_filename = None
        if video_image and allowed_file(video_image.filename, ALLOWED_IMAGE_EXTENSIONS):
            original_filename, file_extension = os.path.splitext(video_image.filename)
            timestamp = str(int(time.time()))
            image_filename = secure_filename(f"{timestamp}_{original_filename}{file_extension}")

            image_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEO_IMAGES'], image_filename)
            video_image.save(image_path)

        # บันทึกลงฐานข้อมูล (เพิ่มคอลัมน์ video_file)
        try:
            cursor.execute("""
                INSERT INTO quiz_video (lesson_id, title, description, time_duration, youtube_link, video_file, video_image)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (lesson_id, title, description, time_duration, youtube_link, video_filename, image_filename))
            mysql.connection.commit()
            flash('เพิ่มวิดีโอใหม่สำเร็จ!', 'success')
            return redirect(url_for('instructor_dashboard')) # หรือหน้าที่ต้องการ
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'danger')
            return redirect(url_for('instructor_add_video', lesson_id=lesson_id))
        finally:
            cursor.close()

    cursor.close()
    return render_template('instructor/add_video.html', lesson=lesson) # <--- ตรวจสอบชื่อไฟล์ให้ตรง

@app.route('/instructor/video/edit/<int:video_id>', methods=['GET', 'POST']) # URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_edit_video(video_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_edit_video'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลวิดีโอปัจจุบัน
    cursor.execute("SELECT * FROM quiz_video WHERE video_id = %s", (video_id,))
    video = cursor.fetchone()

    if not video:
        flash('ไม่พบวิดีโอที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('instructor_dashboard')) # ✅ ชี้ไปที่ dashboard ของ instructor

    # 2. เตรียมข้อมูลบทเรียนสำหรับเทมเพลต (สำคัญมาก)
    lesson_id_from_video = video.get('lesson_id')
    
    # สร้างอ็อบเจกต์จำลอง lesson โดยมีค่าเริ่มต้นที่ปลอดภัย
    TempLessonForTemplate = type('Lesson', (object,), {
        'title': 'บทเรียนไม่ทราบชื่อ',
        'lesson_id': None
    })

    lesson_obj_for_template = TempLessonForTemplate()

    if lesson_id_from_video:
        cursor.execute("SELECT lesson_id, lesson_name FROM lesson WHERE lesson_id = %s", (lesson_id_from_video,))
        lesson_data = cursor.fetchone()
        if lesson_data:
            lesson_obj_for_template.title = lesson_data['lesson_name']
            lesson_obj_for_template.lesson_id = lesson_data['lesson_id']
        else:
            lesson_obj_for_template.title = 'ไม่พบบทเรียน (ID: {})'.format(lesson_id_from_video)
            lesson_obj_for_template.lesson_id = lesson_id_from_video
    else:
        lesson_obj_for_template.title = 'ไม่พบบทเรียนที่เชื่อมโยง'
        lesson_obj_for_template.lesson_id = None


    if request.method == 'POST':
        title = request.form['title']
        youtube_link = request.form['youtube_link']
        description = request.form.get('description', '')
        time_duration = request.form.get('time_duration', '')
        
        # จัดการการอัปโหลดรูปภาพใหม่ (โค้ดเดิมที่ถูกต้องแล้ว)
        new_video_image = request.files.get('video_image')
        filename = video.get('video_image') # ใช้ .get() เพื่อป้องกัน KeyError ถ้าไม่มีคอลัมน์นี้

        if new_video_image and new_video_image.filename != '' and allowed_file(new_video_image.filename, ALLOWED_IMAGE_EXTENSIONS):
            filename = secure_filename(new_video_image.filename)
            upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER_VIDEO_IMAGES'])
            os.makedirs(upload_path, exist_ok=True)
            new_video_image.save(os.path.join(upload_path, filename))
            # Optional: ลบรูปเก่าถ้าเปลี่ยนใหม่
            if video.get('video_image') and os.path.exists(os.path.join(upload_path, video['video_image'])):
                try: os.remove(os.path.join(upload_path, video['video_image']))
                except Exception as e: print(f"ERROR: Could not delete old video image: {e}")
        elif new_video_image and new_video_image.filename == '':
            # ผู้ใช้เลือก "choose file" แต่ไม่ได้เลือกไฟล์ -> ใช้รูปเดิม
            pass
        # else: ถ้าไม่ส่งไฟล์มาและไม่มีไฟล์เดิม ก็เป็น None หรือค่าว่าง


        # อัปเดตข้อมูลในฐานข้อมูล
        try:
            cursor.execute("""
                UPDATE quiz_video
                SET title=%s, youtube_link=%s, description=%s, time_duration=%s, video_image=%s
                WHERE video_id=%s
            """, (title, youtube_link, description, time_duration, filename, video_id))
            mysql.connection.commit()
            flash('แก้ไขวิดีโอเรียบร้อยแล้ว', 'success')
            cursor.close()

            # เปลี่ยนเส้นทางกลับไปที่หน้า quiz_and_video ของบทเรียนที่เกี่ยวข้อง
            redirect_lesson_id = lesson_id_from_video if lesson_id_from_video is not None else lesson_obj_for_template.lesson_id
            if redirect_lesson_id is None:
                return redirect(url_for('instructor_dashboard')) # ✅ ชี้ไปที่ instructor_dashboard
            else:
                return redirect(url_for('instructor_quiz_and_video', lesson_id=redirect_lesson_id)) # ✅ ชี้ไปที่ instructor_quiz_and_video

        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึก: {str(e)}', 'danger')
            cursor.close()
            return render_template('instructor/edit_video.html', video=video, lesson=lesson_obj_for_template)


    cursor.close()
    # ✅ ใช้ template ของ Instructor
    return render_template('instructor/edit_video.html', video=video, lesson=lesson_obj_for_template)

@app.route('/instructor/lesson_content/remove/<int:qv_entry_id>', methods=['POST']) # URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_remove_lesson_content(qv_entry_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_remove_lesson_content'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    lesson_id_to_redirect = None

    print(f"\n--- DEBUG: Entering instructor_remove_lesson_content for qv_entry_id: {qv_entry_id} ---")

    try:
        cursor.execute("SELECT lesson_id FROM quiz_video WHERE video_id = %s", (qv_entry_id,))
        result = cursor.fetchone()
        print(f"DEBUG: SELECT result for qv_entry_id {qv_entry_id}: {result}")

        if result:
            lesson_id_to_redirect = result['lesson_id']
            print(f"DEBUG: Found lesson_id: {lesson_id_to_redirect}. Attempting DELETE.")
            cursor.execute("DELETE FROM quiz_video WHERE video_id = %s", (qv_entry_id,))
            mysql.connection.commit()
            print("DEBUG: DELETE successful, commit done.")
            flash('ลบเนื้อหาออกจากบทเรียนเรียบร้อยแล้ว', 'success')
        else:
            print(f"DEBUG: No entry found for qv_entry_id {qv_entry_id}. Flashing 'danger' and redirecting to instructor_dashboard.")
            flash('ไม่พบรายการเนื้อหาที่ระบุเพื่อลบ', 'danger')
            return redirect(url_for('instructor_dashboard')) # ✅ ชี้ไปที่ instructor_dashboard

    except Exception as e:
        mysql.connection.rollback()
        print(f"ERROR: Exception during deletion: {e}")
        flash(f'เกิดข้อผิดพลาดในการลบเนื้อหา: {e}', 'danger')
    finally:
        cursor.close()
        print("DEBUG: Cursor closed.")

    if lesson_id_to_redirect:
        print(f"DEBUG: Redirecting to instructor_quiz_and_video for lesson_id: {lesson_id_to_redirect}")
        return redirect(url_for('instructor_quiz_and_video', lesson_id=lesson_id_to_redirect)) # ✅ ชี้ไปที่ instructor_quiz_and_video
    else:
        print("DEBUG: Fallback redirect to instructor_dashboard (lesson_id_to_redirect was None).")
        return redirect(url_for('instructor_dashboard'))
    
@app.route('/instructor/quiz/<int:lesson_id>') # ✅ เปลี่ยน URL ให้เป็นของ instructor
@instructor_required # ✅ ใช้ decorator สำหรับ Instructor
def instructor_quiz_list(lesson_id): # ✅ เปลี่ยนชื่อฟังก์ชันเพื่อให้ไม่ซ้ำกับของ admin
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
    # ✅ เปลี่ยนไปใช้ template สำหรับ instructor
    return render_template('instructor/quiz_list.html', quizzes=quizzes, lesson_id=lesson_id)

@app.route('/instructor/quiz/<int:quiz_id>/questions')
@instructor_required
def instructor_quiz_questions(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # ดึงข้อมูลแบบทดสอบ
    cursor.execute("SELECT quiz_id, quiz_name, lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone() # ✅ ตรงนี้ quiz จะถูกกำหนดค่า

    if not quiz: # ถ้า quiz เป็น None (ไม่พบบททดสอบ)
        flash('ไม่พบแบบทดสอบที่ระบุ', 'danger')
        cursor.close()
        # ✅ แก้ไขตรงนี้: ไม่สามารถใช้ quiz_data ได้
        # ต้องพยายาม redirect ไปที่ instructor_dashboard หรือ instructor_course_list
        return redirect(url_for('instructor_dashboard')) # fallback ไปที่ dashboard ของ Instructor

    # ดึงคำถามทั้งหมดของแบบทดสอบนี้
    questions = [] # กำหนดค่าเริ่มต้นเพื่อความปลอดภัย
    cursor.execute("SELECT * FROM questions WHERE quiz_id = %s", (quiz_id,))
    questions = cursor.fetchall()
    cursor.close()

    # ส่ง quiz (ที่เป็น dictionary) และ questions ไปยังเทมเพลต
    return render_template('instructor/quiz_questions.html', quiz=quiz, questions=questions, lesson_id=quiz['lesson_id'])

@app.route('/instructor/quiz/edit/<int:quiz_id>', methods=['GET', 'POST']) # URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_edit_quiz(quiz_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_edit_quiz'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    form = QuizForm() # สร้างฟอร์มตั้งแต่ต้น

    # ✅ ดึงรายการแบบทดสอบทั้งหมดมาใส่ใน Dropdown 'select_quiz_id' เสมอ
    cursor.execute("""
        SELECT q.quiz_id, q.quiz_name, l.lesson_name
        FROM quiz q
        LEFT JOIN lesson l ON q.lesson_id = l.lesson_id
        ORDER BY q.quiz_name ASC
    """)
    all_quizzes_for_selection = cursor.fetchall()
    form.select_quiz_id.choices = [(q['quiz_id'], f"{q['quiz_name']} (บทเรียน: {q['lesson_name'] or 'ไม่ระบุ'})") for q in all_quizzes_for_selection]
    form.select_quiz_id.choices.insert(0, (0, '-- เลือกแบบทดสอบ --'))

    # ✅ กำหนด choices สำหรับ quiz_type เสมอ
    form.quiz_type.choices = [('Pre-test', 'Pre-test'), ('Post_test', 'Post-test')]

    # ✅ ดึงรายการบทเรียนทั้งหมดมาเพื่อเติม choices ให้กับ form.lesson_id เสมอ
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson ORDER BY lesson_name ASC")
    lessons_for_choices = cursor.fetchall()
    form.lesson_id.choices = [(l['lesson_id'], l['lesson_name']) for l in lessons_for_choices]
    form.lesson_id.choices.insert(0, (0, '-- เลือกบทเรียน --')) # เพิ่มตัวเลือกเริ่มต้น

    
    cursor.execute("SELECT * FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz_data = cursor.fetchone()

    if not quiz_data:
        flash('ไม่พบแบบทดสอบที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('instructor_quiz_list', lesson_id=quiz_data.get('lesson_id', 0))) # หรือไป dashboard

    # เติมข้อมูลลงในฟอร์มสำหรับการแก้ไข (เฉพาะเมื่อเป็น GET request)
    if request.method == 'GET':
        form.quiz_name.data = quiz_data.get('quiz_name')
        form.quiz_type.data = quiz_data.get('quiz_type')
        form.passing_percentage.data = quiz_data.get('passing_percentage')
        form.lesson_id.data = quiz_data.get('lesson_id') # ป้อน lesson_id เดิมของแบบทดสอบ


    # ดึงคำถามที่เกี่ยวข้องกับแบบทดสอบนี้
    questions = [] # กำหนดค่าเริ่มต้นเพื่อความปลอดภัย
    cursor.execute("SELECT * FROM questions WHERE quiz_id = %s", (quiz_id,))
    questions = cursor.fetchall()


    # สร้าง lesson_obj_for_template (เหมือนเดิม)
    lesson_id_from_quiz = quiz_data.get('lesson_id')
    lesson_obj_for_template = None
    if lesson_id_from_quiz:
        cursor.execute("SELECT lesson_id, lesson_name, course_id FROM lesson WHERE lesson_id = %s", (lesson_id_from_quiz,))
        lesson_data = cursor.fetchone()
        if lesson_data:
            cursor.execute("SELECT title FROM courses WHERE id = %s", (lesson_data['course_id'],))
            course_data = cursor.fetchone()
            course_name_for_lesson = course_data['title'] if course_data else "ไม่ทราบชื่อคอร์ส"
            lesson_obj_for_template = LessonForTemplate(lesson_data['lesson_id'], lesson_data['lesson_name'], lesson_data['course_id'], course_name_for_lesson)
        else:
            lesson_obj_for_template = LessonForTemplate(quiz_id, 'ไม่พบบทเรียน (ID: {})'.format(lesson_id_from_quiz), None, "ไม่ทราบชื่อคอร์ส")
    else:
        lesson_obj_for_template = LessonForTemplate(quiz_id, 'ไม่พบบทเรียนที่เชื่อมโยง', None, "ไม่ทราบชื่อคอร์ส")
    
    
    if form.validate_on_submit(): # จะทำงานเมื่อ submit ฟอร์มแก้ไข
        updated_quiz_name = form.quiz_name.data
        updated_quiz_type = form.quiz_type.data
        updated_passing_percentage = form.passing_percentage.data
        updated_lesson_id = form.lesson_id.data

        if updated_lesson_id == 0:
            flash('กรุณาเลือกบทเรียนที่เกี่ยวข้อง', 'danger')
            cursor.close()
            return render_template('instructor/edit_quiz.html', quiz=quiz_data, questions=questions, lesson=lesson_obj_for_template, form=form) # ส่ง selection_mode=False ด้วย

        try:
            cursor.execute("""
                UPDATE quiz SET
                    quiz_name = %s,
                    quiz_type = %s,
                    passing_percentage = %s,
                    lesson_id = %s
                WHERE quiz_id = %s
            """, (updated_quiz_name, updated_quiz_type, updated_passing_percentage, updated_lesson_id, quiz_id))
            
            mysql.connection.commit()
            flash('แก้ไขแบบทดสอบเรียบร้อยแล้ว!', 'success')
            cursor.close()

            if lesson_id_from_quiz is None:
                return redirect(url_for('instructor_dashboard'))
            else:
                return redirect(url_for('instructor_quiz_and_video', lesson_id=lesson_id_from_quiz))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึก: {str(e)}', 'danger')
            cursor.close()
            return render_template('instructor/edit_quiz.html', quiz=quiz_data, questions=questions, lesson=lesson_obj_for_template, form=form) # ส่ง selection_mode=False ด้วย
    
    cursor.close()
    return render_template('instructor/edit_quiz.html', quiz=quiz_data, questions=questions, lesson=lesson_obj_for_template, form=form) # ส่ง selection_mode=False

@app.route('/instructor/quiz/delete/<int:quiz_id>', methods=['POST']) # ✅ URL สำหรับ Instructor และใช้ POST เท่านั้น
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_delete_quiz(quiz_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_delete_quiz'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึง lesson_id ก่อนลบ เพื่อใช้ในการ redirect กลับ
    # เนื่องจากเราต้องการ lesson_id เพื่อ redirect กลับไปหน้า quiz_and_video ของบทเรียนนั้น
    # เราจึงดึงจากตาราง quiz เพราะ quiz มี lesson_id ผูกอยู่
    cursor.execute("SELECT lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz_info = cursor.fetchone()

    if not quiz_info:
        flash('ไม่พบแบบทดสอบนี้', 'danger')
        cursor.close()
        # หากไม่พบ quiz_id หรือ lesson_id ให้ redirect ไปที่ instructor_dashboard
        return redirect(url_for('instructor_dashboard')) 

    lesson_id_to_redirect = quiz_info['lesson_id']

    try:
        # 2. ลบคำถามทั้งหมดที่เกี่ยวข้องกับแบบทดสอบนี้ก่อน (ถ้ามีตาราง questions)
        cursor.execute("DELETE FROM questions WHERE quiz_id = %s", (quiz_id,))
        # 3. ลบ entry ของแบบทดสอบในตาราง quiz_video (ถ้ามี)
        cursor.execute("DELETE FROM quiz_video WHERE quiz_id = %s", (quiz_id,))
        # 4. ลบแบบทดสอบจากตาราง quiz
        cursor.execute("DELETE FROM quiz WHERE quiz_id = %s", (quiz_id,))
        
        mysql.connection.commit()
        flash('ลบแบบทดสอบเรียบร้อยแล้ว', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'เกิดข้อผิดพลาดในการลบแบบทดสอบ: {str(e)}', 'danger')
    finally:
        cursor.close()

    # 5. เปลี่ยนเส้นทางกลับไปที่หน้ารายการแบบทดสอบของบทเรียนนั้นๆ
    return redirect(url_for('instructor_quiz_list', lesson_id=lesson_id_to_redirect))

@app.route('/instructor/quiz/<int:quiz_id>/questions/add', methods=['GET', 'POST']) # URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_add_question(quiz_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_add_question'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # ดึงข้อมูลแบบทดสอบ (เพื่อแสดงชื่อแบบทดสอบ)
    cursor.execute("SELECT quiz_id, quiz_name, lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz: # ถ้า quiz เป็น None (ไม่พบบททดสอบ)
        flash('ไม่พบแบบทดสอบที่ระบุ', 'danger')
        cursor.close()
        # ✅ แก้ไขตรงนี้: ถ้าหา quiz ไม่เจอ ให้ redirect ไปที่ instructor_dashboard
        # ไม่ต้องพยายามหา lesson_id เพราะ quiz อาจเป็น None
        return redirect(url_for('instructor_dashboard')) 


    if request.method == 'POST':
        question_name = request.form['question_name']
        choice_a = request.form['choice_a']
        choice_b = request.form['choice_b']
        choice_c = request.form['choice_c']
        choice_d = request.form['choice_d']
        correct_answer = request.form['correct_answer'].lower()
        score = int(request.form['score'])

        # ฟังก์ชันช่วยบันทึกรูปภาพ
        def save_image(file_key):
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename != '' and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER_QUESTION_IMAGES'])
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    return filename
            return ''

        question_image = save_image('question_image')
        choice_a_image = save_image('choice_a_image')
        choice_b_image = save_image('choice_b_image')
        choice_c_image = save_image('choice_c_image')
        choice_d_image = save_image('choice_d_image')

        try:
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
            flash('เพิ่มคำถามเรียบร้อยแล้ว', 'success')
            cursor.close()
            return redirect(url_for('instructor_quiz_questions', quiz_id=quiz_id))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการเพิ่มคำถาม: {str(e)}', 'danger')
            cursor.close()
            # ส่ง quiz และ lesson_id กลับไปด้วยเพื่อให้ template แสดงผลได้
            return render_template('instructor/add_question.html', quiz=quiz, lesson_id=quiz['lesson_id'])

    cursor.close()
    # ส่ง quiz และ lesson_id กลับไปด้วยเพื่อให้ template แสดงผลได้
    return render_template('instructor/add_question.html', quiz=quiz, lesson_id=quiz['lesson_id'])



# ✅ เพิ่มฟังก์ชันนี้สำหรับ Instructor (เพิ่มแบบทดสอบใหม่ทั้งหมด)
@app.route('/instructor/quiz/add_new', methods=['GET', 'POST']) # ✅ URL สำหรับ Instructor (เปลี่ยนเป็น add_new เพื่อไม่ให้สับสน)
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_add_quiz(): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_add_quiz'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    form = QuizForm() # ใช้ QuizForm ในการสร้างแบบทดสอบใหม่

    # ดึงบทเรียนทั้งหมดมาแสดงใน dropdown ของ LessonForm
    cursor.execute("SELECT lesson_id, lesson_name FROM lesson ORDER BY lesson_name ASC")
    lessons_for_choices = cursor.fetchall()
    form.lesson_id.choices = [(l['lesson_id'], l['lesson_name']) for l in lessons_for_choices]
    form.lesson_id.choices.insert(0, (0, '-- เลือกบทเรียน --')) # เพิ่มตัวเลือกเริ่มต้น

    # กำหนด choices สำหรับ quiz_type
    form.quiz_type.choices = [
        ('Pre-test', 'Pre-test'),
        ('Post_test', 'Post-test')
    ]

    if form.validate_on_submit():
        quiz_name = form.quiz_name.data
        quiz_type = form.quiz_type.data
        passing_percentage = form.passing_percentage.data
        lesson_id_selected = form.lesson_id.data # รับ lesson_id จากฟอร์ม
        quiz_date = datetime.now().date() # วันที่สร้างแบบทดสอบ

        if lesson_id_selected == 0:
            flash('กรุณาเลือกบทเรียนที่เกี่ยวข้อง', 'danger')
            cursor.close()
            return render_template('instructor/add_quiz.html', form=form)

        try:
            cursor.execute("""
                INSERT INTO quiz (quiz_name, lesson_id, passing_percentage, quiz_date, quiz_type)
                VALUES (%s, %s, %s, %s, %s)
            """, (quiz_name, lesson_id_selected, passing_percentage, quiz_date, quiz_type))
            mysql.connection.commit()
            flash('เพิ่มแบบทดสอบเรียบร้อยแล้ว', 'success')
            cursor.close()
            # Redirect ไปยังหน้ารายการแบบทดสอบของบทเรียนที่ถูกเลือก
            return redirect(url_for('instructor_quiz_list', lesson_id=lesson_id_selected))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการเพิ่มแบบทดสอบ: {str(e)}', 'danger')
            cursor.close()
            return render_template('instructor/add_quiz.html', form=form)

    cursor.close()
    return render_template('instructor/add_quiz.html', form=form)

@app.route('/instructor/add_lesson', methods=['GET', 'POST'])
@instructor_required
def instructor_add_lesson():
    form = LessonForm()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # --- VVVVVV จุดที่แก้ไข 1: กรองหลักสูตร VVVVVV ---
    # ดึงเฉพาะหลักสูตรที่ Instructor คนนี้เป็นเจ้าของเท่านั้น
    cursor.execute('SELECT id, title FROM courses WHERE instructor_id = %s ORDER BY title ASC', (current_user.id,))
    courses_data = cursor.fetchall()
    form.course_id.choices = [(course['id'], course['title']) for course in courses_data]
    form.course_id.choices.insert(0, (0, '-- เลือกหลักสูตรของคุณ --'))
    # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

    # ดึงข้อมูลผู้สอน (ยังคงไว้เพื่อให้ฟอร์มแสดงผลได้)
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM instructor ORDER BY first_name ASC")
    instructors_data = cursor.fetchall()
    form.instructor_id.choices = [(ins['id'], ins['full_name']) for ins in instructors_data]
    form.instructor_id.choices.insert(0, (0, '-- เลือกผู้สอน --'))


    if form.validate_on_submit():
        lesson_name = form.title.data
        course_id = form.course_id.data
        lesson_date = form.lesson_date.data if form.lesson_date.data else datetime.now().date()
        
        # --- VVVVVV จุดที่แก้ไข 2: ใช้ ID ของผู้สอนที่ล็อกอินอยู่เสมอ VVVVVV ---
        # ไม่รับค่า instructor_id จากฟอร์ม เพื่อความปลอดภัย
        instructor_id = current_user.id
        # --- ^^^^^^ สิ้นสุดการแก้ไข ^^^^^^ ---

        if course_id == 0:
            flash('กรุณาเลือกหลักสูตร', 'danger')
            # ส่งข้อมูลกลับไปที่ template อีกครั้ง
            return render_template('instructor/add_lesson.html', form=form, instructors=instructors_data, courses=courses_data)

        try:
            cursor.execute(
                'INSERT INTO lesson (lesson_name, course_id, instructor_id, lesson_date) VALUES (%s, %s, %s, %s)',
                (lesson_name, course_id, instructor_id, lesson_date)
            )
            mysql.connection.commit()
            flash('เพิ่มบทเรียนสำเร็จ', 'success')
            # (ตรวจสอบให้แน่ใจว่าคุณมี endpoint 'instructor_lesson' อยู่จริง)
            return redirect(url_for('instructor_dashboard')) 
        except Exception as e:
            mysql.connection.rollback()
            flash(f"เกิดข้อผิดพลาด: {str(e)}", "danger")
        finally:
            cursor.close()

    cursor.close()
    return render_template('instructor/add_lesson.html', form=form, instructors=instructors_data, courses=courses_data)


@app.route('/instructor/lesson/edit/<int:lesson_id>', methods=['GET', 'POST']) # ✅ URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator สำหรับ Instructor
def instructor_edit_lesson(lesson_id): # ✅ เปลี่ยนชื่อฟังก์ชันเพื่อให้ไม่ซ้ำกับของ admin
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลบทเรียน (จากตาราง 'lesson')
    cursor.execute("SELECT lesson_id, lesson_name, lesson_date, course_id FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson_data = cursor.fetchone()

    if not lesson_data:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        # ✅ Redirect ไปที่ instructor_dashboard หรือ instructor_lesson list
        return redirect(url_for('instructor_dashboard')) 

    # 2. ดึงข้อมูลคอร์สที่เกี่ยวข้องเพื่อแสดงในเทมเพลต (lesson.course.course_name)
    course_id = lesson_data['course_id']
    cursor.execute("SELECT id, title FROM courses WHERE id = %s", (course_id,))
    course_info = cursor.fetchone()
    course_name_for_template = course_info['title'] if course_info else "ไม่ระบุคอร์ส"

    # 3. สร้าง TempCourse และ TempLessonForTemplate objects เพื่อส่งให้เทมเพลต
    #    เพื่อให้เทมเพลตสามารถเข้าถึง attribute ได้เหมือน Lesson Model
    class TempCourse:
        def __init__(self, name, id):
            self.course_name = name
            self.id = id

    class TempLessonForTemplate:
        def __init__(self, data, course_name, course_id):
            self.id = data['lesson_id']
            self.lesson_id = data['lesson_id']
            self.title = data['lesson_name']
            self.lesson_date = data.get('lesson_date')
            self.course_id = course_id
            self.course = TempCourse(course_name, course_id)

    lesson_for_template = TempLessonForTemplate(lesson_data, course_name_for_template, course_id)

    # 4. สร้างฟอร์ม LessonForm และป้อนข้อมูลเดิม
    form_data = {
        'title': lesson_data.get('lesson_name'),
        'lesson_date': lesson_data.get('lesson_date'),
        'course_id': lesson_data.get('course_id'), # จำเป็นถ้า LessonForm มี course_id
        'instructor_id': lesson_data.get('instructor_id') # จำเป็นถ้า LessonForm มี instructor_id
    }
    form = LessonForm(data=form_data)

    # ดึงข้อมูลสำหรับ Dropdown ใน LessonForm (ถ้ามี)
    # เช่น courses_data และ instructors_data (ถ้า LessonForm มี course_id, instructor_id)
    cursor.execute('SELECT id, title FROM courses WHERE status = "publish"')
    courses_for_form = cursor.fetchall()
    form.course_id.choices = [(c['id'], c['title']) for c in courses_for_form]
    form.course_id.choices.insert(0, (0, '-- เลือกหลักสูตร --')) # ตัวเลือกเริ่มต้น
    
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM instructor")
    instructors_for_form = cursor.fetchall()
    form.instructor_id.choices = [(ins['id'], ins['full_name']) for ins in instructors_for_form]
    form.instructor_id.choices.insert(0, (0, '-- เลือกผู้สอน --')) # ตัวเลือกเริ่มต้น


    if form.validate_on_submit():
        updated_title = form.title.data
        updated_lesson_date = form.lesson_date.data
        updated_course_id = form.course_id.data
        updated_instructor_id = form.instructor_id.data

        # ตรวจสอบค่า 0 สำหรับ Dropdown
        if updated_course_id == 0:
            flash('กรุณาเลือกหลักสูตร', 'danger')
            cursor.close()
            return render_template('instructor/edit_lesson.html', form=form, lesson=lesson_for_template)
        if updated_instructor_id == 0:
            flash('กรุณาเลือกผู้สอน', 'danger')
            cursor.close()
            return render_template('instructor/edit_lesson.html', form=form, lesson=lesson_for_template)


        # 5. อัปเดตข้อมูลในฐานข้อมูล
        cursor.execute("""
            UPDATE lesson SET
                lesson_name = %s,
                lesson_date = %s,
                course_id = %s,       {# ✅ เพิ่ม course_id ใน UPDATE #}
                instructor_id = %s    {# ✅ เพิ่ม instructor_id ใน UPDATE #}
            WHERE lesson_id = %s
        """, (updated_title, updated_lesson_date, updated_course_id, updated_instructor_id, lesson_id))
        
        mysql.connection.commit()
        flash('บทเรียนได้รับการแก้ไขเรียบร้อยแล้ว!', 'success')
        cursor.close()
        # ✅ Redirect กลับไปที่ instructor_lesson ของ course ที่เกี่ยวข้อง
        return redirect(url_for('instructor_lesson', course_id=updated_course_id))

    cursor.close()
    # ✅ ใช้ template สำหรับ Instructor
    return render_template('instructor/edit_lesson.html', form=form, lesson=lesson_for_template)

@app.route('/instructor/lesson/delete/<int:lesson_id>', methods=['POST'])
@instructor_required
def instructor_delete_lesson(lesson_id):
    instructor_id = current_user.id
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ตรวจสอบเพื่อความปลอดภัย: เช็คว่าบทเรียนนี้อยู่ในคอร์สของผู้สอนที่ล็อกอินอยู่จริงหรือไม่
    cursor.execute("""
        SELECT l.lesson_id, c.id as course_id
        FROM lesson l
        JOIN courses c ON l.course_id = c.id
        WHERE l.lesson_id = %s AND c.instructor_id = %s
    """, (lesson_id, instructor_id))
    lesson_to_delete = cursor.fetchone()

    if not lesson_to_delete:
        flash('ไม่พบบทเรียน หรือคุณไม่ได้รับอนุญาตให้ลบบทเรียนนี้', 'danger')
        cursor.close()
        return redirect(url_for('instructor_dashboard'))

    # 2. ถ้าตรวจสอบผ่าน ให้ทำการลบ
    try:
        cursor.execute("DELETE FROM lesson WHERE lesson_id = %s", (lesson_id,))
        mysql.connection.commit()
        flash('ลบบทเรียนสำเร็จแล้ว', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'เกิดข้อผิดพลาดในการลบบทเรียน: {str(e)}', 'danger')
    finally:
        cursor.close()

    # 3. กลับไปยังหน้า Dashboard ของผู้สอน ซึ่งเป็นหน้าที่ปลอดภัยและมีอยู่แน่นอน
    return redirect(url_for('instructor_dashboard'))








@app.route('/user/dashboard')
@login_required
def user_dashboard():
    user_id = current_user.id
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลคอร์สทั้งหมดที่ผู้ใช้ลงทะเบียน
    cursor.execute("""
        SELECT c.id, c.title, c.featured_image, i.first_name, i.last_name
        FROM courses c
        JOIN registered_courses rc ON c.id = rc.course_id
        JOIN instructor i ON c.instructor_id = i.id
        WHERE rc.user_id = %s
        ORDER BY rc.registered_at DESC
    """, (user_id,))
    enrolled_courses = cursor.fetchall()

    # 2. คำนวณความคืบหน้าโดยรวม
    total_progress_sum = 0
    if enrolled_courses:
        for course in enrolled_courses:
            course_id = course['id']
            
            # --- Logic การคำนวณ Progress (เหมือนในหน้า Learning Path) ---
            # นับจำนวนเนื้อหาทั้งหมดในคอร์ส (วิดีโอ + Post-test)
            cursor.execute("""
                SELECT COUNT(qv.video_id) as total
                FROM quiz_video qv 
                JOIN lesson l ON qv.lesson_id = l.lesson_id 
                WHERE l.course_id = %s
            """, (course_id,))
            total_items = cursor.fetchone()['total']

            # นับจำนวนวิดีโอที่ดูจบแล้ว
            cursor.execute("""
                SELECT COUNT(uvp.id) as total
                FROM user_video_progress uvp
                JOIN quiz_video qv ON uvp.video_id = qv.video_id
                JOIN lesson l ON qv.lesson_id = l.lesson_id
                WHERE uvp.user_id = %s AND l.course_id = %s
            """, (user_id, course_id))
            completed_videos = cursor.fetchone()['total']

            # นับจำนวน Post-test ที่ทำผ่านแล้ว
            cursor.execute("""
                SELECT COUNT(uqa.id) as total
                FROM user_quiz_attempts uqa
                JOIN quiz q ON uqa.quiz_id = q.quiz_id
                JOIN lesson l ON q.lesson_id = l.lesson_id
                WHERE uqa.user_id = %s AND l.course_id = %s AND q.quiz_type = 'Post_test' AND uqa.passed = 1
            """, (user_id, course_id))
            passed_post_tests = cursor.fetchone()['total']

            completed_items = completed_videos + passed_post_tests
            
            course_progress = (completed_items / total_items) * 100 if total_items > 0 else 0
            total_progress_sum += course_progress
        
        # หาค่าเฉลี่ย
        overall_average_progress = total_progress_sum / len(enrolled_courses)
    else:
        overall_average_progress = 0

    cursor.close()

    return render_template('user/user_dashboard.html',
                           enrolled_courses_count=len(enrolled_courses),
                           recent_courses=enrolled_courses[:5], # แสดงแค่ 5 คอร์สล่าสุด
                           overall_average_progress=overall_average_progress)




if __name__ == '__main__':
    app.run(debug=True)