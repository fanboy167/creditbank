from flask import Flask, render_template, redirect, url_for, flash, session, request, current_app, jsonify 
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

UPLOAD_FOLDER_IMAGES = 'static/course_images'
UPLOAD_FOLDER_VIDEOS = 'static/course_videos'
UPLOAD_FOLDER_PROFILE_IMAGES = 'static/profile_images'
UPLOAD_FOLDER_QUESTION_IMAGES = 'static/question_images'
UPLOAD_FOLDER_VIDEO_IMAGES = 'static/video_images'

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

def allowed_file(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

app = Flask(__name__) # ✅ app = Flask(__name__) ต้องอยู่ตรงนี้

# ✅ กำหนดค่าเข้า app.config หลัง app = Flask(__name__)
app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
app.config['UPLOAD_FOLDER_VIDEOS'] = UPLOAD_FOLDER_VIDEOS
app.config['UPLOAD_FOLDER_PROFILE_IMAGES'] = UPLOAD_FOLDER_PROFILE_IMAGES
app.config['UPLOAD_FOLDER_QUESTION_IMAGES'] = UPLOAD_FOLDER_QUESTION_IMAGES
app.config['UPLOAD_FOLDER_VIDEO_IMAGES'] = UPLOAD_FOLDER_VIDEO_IMAGES

# ✅ สร้างโฟลเดอร์หลังกำหนดใน app.config
os.makedirs(app.config['UPLOAD_FOLDER_IMAGES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_VIDEOS'], exist_ok=True)
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
    title = StringField('ชื่อบทเรียน', validators=[DataRequired(message="กรุณาระบุชื่อบทเรียน")])
    description = TextAreaField('รายละเอียดบทเรียน', validators=[Optional()]) # เพิ่ม description กลับมา
    lesson_date = DateField('วันที่สร้างบทเรียน', format='%Y-%m-%d', validators=[Optional()])
    course_id = SelectField('หลักสูตร', coerce=int, validators=[DataRequired(message="กรุณาเลือกหลักสูตร")])
    instructor_id = SelectField('ผู้สอน', coerce=int, validators=[DataRequired(message="กรุณาเลือกผู้สอน")])
    
# ---------------------------------------------------------------------------------------------


class User(UserMixin):
    def __init__(self, id, role, first_name, last_name, username, email, profile_image=None):
        self.id = id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.profile_image = profile_image if profile_image else "default.png"
        self.profile_image_version = datetime.now().timestamp() # ✅ เพิ่ม version สำหรับ cache busting
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
    
    print(f"\n--- DEBUG: load_user for user_id: {user_id} ---")

    # 1. ตรวจสอบใน Admin Table ก่อน
    cursor.execute('SELECT id, username, password, email, role, first_name, last_name, tel, gender, profile_image FROM admin WHERE id = %s', (user_id,))
    admin_data = cursor.fetchone()
    if admin_data:
        db_role = str(admin_data.get('role', 'admin')).strip()
        print(f"DEBUG: Found user in 'admin' table. Role: '{db_role}'")
        admin_obj = Admin(
            id=admin_data['id'], role=db_role,
            first_name=admin_data['first_name'], last_name=admin_data['last_name'],
            username=admin_data['username'], email=admin_data['email'],
            tel=admin_data.get('tel'), gender=admin_data.get('gender'),
            profile_image=admin_data.get('profile_image')
        )
        admin_obj.profile_image_version = datetime.now().timestamp() # ✅ ตั้งค่า version
        return admin_obj

    # 2. ตรวจสอบใน Instructor Table
    cursor.execute('SELECT id, username, password, email, role, first_name, last_name, tel, gender, profile_image FROM instructor WHERE id = %s', (user_id,))
    instructor_data = cursor.fetchone()
    if instructor_data:
        db_role = str(instructor_data.get('role', 'instructor')).strip()
        print(f"DEBUG: Found user in 'instructor' table. Role: '{db_role}'")
        instructor_obj = Instructor(
            id=instructor_data['id'], role=db_role,
            first_name=instructor_data['first_name'], last_name=instructor_data['last_name'],
            username=instructor_data['username'], email=instructor_data['email'],
            tel=instructor_data.get('tel'), gender=instructor_data.get('gender'),
            profile_image=instructor_data.get('profile_image')
        )
        instructor_obj.profile_image_version = datetime.now().timestamp() # ✅ ตั้งค่า version
        return instructor_obj
    
    # 3. ตรวจสอบใน User Table
    cursor.execute('SELECT id, username, password, email, role, first_name, last_name, id_card, gender, profile_image FROM user WHERE id = %s', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        db_role = str(user_data.get('role', 'user')).strip()
        print(f"DEBUG: Found user in 'user' table. Role: '{db_role}'")
        user_obj = User(id=user_data['id'], role=db_role,
                    first_name=user_data['first_name'], last_name=user_data['last_name'],
                    username=user_data['username'], email=user_data['email'],
                    profile_image=user_data.get('profile_image'))
        user_obj.profile_image_version = datetime.now().timestamp() # ✅ ตั้งค่า version
        return user_obj
    
    print(f"DEBUG: User ID {user_id} not found in any table.")
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
    
    query = """
    SELECT
      c.id,
      c.title AS course_name,
      -- c.description, # ✅ ลบ description ออกจาก SELECT
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
    cursor.close()
    
    courses = []
    for row in courses_raw:
        courses.append({
            'id': row['id'],
            'course_name': row['course_name'],
            'description': row.get('description'), # ✅ ใช้ .get() เพื่อความปลอดภัย ถ้าคอลัมน์นี้ไม่มี
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
            'students_count': 0,
            'duration_hours': 'N/A'
        })
    return render_template('course/course.html', courses=courses)


@app.route('/course/<int:course_id>')
def course_detail(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    print(f"\n--- DEBUG: เข้าสู่ course_detail สำหรับ course_id: {course_id} ---")

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
    GROUP BY c.id, c.title, c.description, c.featured_image, c.featured_video,
             cat.id, cat.name, i.id, i.first_name, i.last_name, c.status,
             pre_q.quiz_id, pre_q.quiz_name, pre_q.passing_percentage
    LIMIT 1
    """
    
    # ✅ ดึง course_data ไว้ใน try-except block
    try:
        cursor.execute(query, (course_id,))
        course_data = cursor.fetchone() # ✅ course_data ถูกกำหนดตรงนี้
    except Exception as e:
        print(f"ERROR: SQL Error in course_detail query: {e}")
        flash(f"เกิดข้อผิดพลาดในการดึงข้อมูลหลักสูตร: {str(e)}", "danger")
        cursor.close()
        return redirect(url_for('course'))

    if not course_data:
        print(f"DEBUG: ไม่พบหลักสูตร ID {course_id} เลย. Redirect ไปที่ /course.")
        flash('ไม่พบหลักสูตรที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('course'))

    # ✅ ตรวจสอบสถานะหลังจากดึงข้อมูลมาแล้ว (ย้ายมาไว้ข้างนอก try-except)
    if course_data.get('status') != 'publish':
        print(f"DEBUG: หลักสูตร ID {course_id} สถานะไม่ใช่ 'publish' ('{course_data.get('status')}'). Redirect ไปที่ /course.")
        flash('หลักสูตรนี้ยังไม่ถูกเผยแพร่', 'danger')
        cursor.close()
        return redirect(url_for('course'))


    print(f"DEBUG: พบข้อมูลหลักสูตร: {course_data}")
    print(f"DEBUG: สถานะหลักสูตรจาก DB: '{course_data.get('status')}'")
    print(f"DEBUG: Course ID from DB: {course_data.get('id')}")

    # ✅ สร้าง course dictionary หลังจาก course_data ถูกกำหนดแล้ว
    course = {
        'id': course_data['id'], 'course_name': course_data['course_name'], 'description': course_data.get('description', ''),
        'featured_image': course_data['featured_image'], 'featured_video': course_data['featured_video'],
        'category': {'id': course_data['category_id'], 'name': course_data['category_name']},
        'instructor': {'id': course_data['instructor_id'], 'first_name': course_data['first_name'], 'last_name': course_data['last_name']},
        
        'pre_test_quiz_id': course_data.get('pre_test_quiz_id'),
        'pre_test_quiz_name': course_data.get('pre_test_quiz_name'),
        'pre_test_passing_percentage': course_data.get('pre_test_passing_percentage'),
        
        'students_count': 0, 
        'duration_hours': 'N/A'
    }

    # ✅ ดึงจำนวนนักเรียนที่ลงทะเบียนหลักสูตรนี้ (ย้ายมาไว้หลัง course_data ถูกกำหนด)
    cursor.execute("SELECT COUNT(id) AS student_count FROM registered_courses WHERE course_id = %s", (course_id,))
    student_count_result = cursor.fetchone()
    student_count = student_count_result['student_count'] if student_count_result else 0
    course['students_count'] = student_count # ✅ อัปเดตใน course dict

    # ✅ ดึงและคำนวณระยะเวลารวมของวิดีโอทั้งหมดในหลักสูตร (ย้ายมาไว้หลัง course_data ถูกกำหนด)
    total_duration_minutes = 0
    print(f"DEBUG: กำลังคำนวณระยะเวลารวมสำหรับ course_id: {course_id}")
    
    duration_query = """
        SELECT qv.time_duration, qv.title, qv.video_id, l.lesson_id, l.lesson_name
        FROM quiz_video qv
        JOIN lesson l ON qv.lesson_id = l.lesson_id
        WHERE l.course_id = %s AND qv.quiz_id IS NULL -- เฉพาะวิดีโอ
    """
    print(f"DEBUG: Executing duration query: {duration_query % course_id}")
    
    cursor.execute(duration_query, (course_id,))
    video_durations_raw = cursor.fetchall()
    
    print(f"DEBUG: วิดีโอที่ดึงมาเพื่อคำนวณระยะเวลา: {video_durations_raw}")

    for duration_row in video_durations_raw:
        duration_str = duration_row.get('time_duration')
        video_title = duration_row.get('title')
        video_id_debug = duration_row.get('video_id')
        lesson_id_debug = duration_row.get('lesson_id')

        if duration_str:
            try:
                parts = [int(p) for p in duration_str.split(':')]
                current_video_minutes = 0
                if len(parts) == 2: # MM:SS
                    current_video_minutes = parts[0] + parts[1] / 60
                elif len(parts) == 3: # HH:MM:SS
                    current_video_minutes = parts[0] * 60 + parts[1] + parts[2] / 60
                total_duration_minutes += current_video_minutes
                print(f"DEBUG: วิดีโอ '{video_title}' (ID: {video_id_debug}, Lesson: {lesson_id_debug}) ระยะเวลา '{duration_str}' -> {current_video_minutes:.2f} นาที. รวม: {total_duration_minutes:.2f} นาที")
            except ValueError:
                print(f"WARNING: วิดีโอ '{video_title}' (ID: {video_id_debug}) มีรูปแบบ time_duration ไม่ถูกต้อง: '{duration_str}'. ข้ามการคำนวณ.")
        else:
            print(f"WARNING: วิดีโอ '{video_title}' (ID: {video_id_debug}) ไม่มี time_duration หรือเป็น NULL.")
    
    course_duration_display = "N/A"
    if total_duration_minutes > 0:
        hours = int(total_duration_minutes // 60)
        minutes = int(total_duration_minutes % 60)
        if hours > 0:
            course_duration_display = f"{hours} ชม. {minutes} นาที"
        else:
            course_duration_display = f"{minutes} นาที"
    print(f"DEBUG: ระยะเวลารวมของหลักสูตร: {course_duration_display}")
    course['duration_hours'] = course_duration_display # ✅ อัปเดตใน course dict


    # 2. ดึงบทเรียนทั้งหมดของหลักสูตรนี้ (เหมือนเดิม)
    cursor.execute("""
        SELECT lesson_id, lesson_name, lesson_date, description
        FROM lesson
        WHERE course_id = %s
        ORDER BY lesson_date ASC
    """, (course_id,))
    lessons_in_course = cursor.fetchall()
    
    first_lesson_id = None
    if lessons_in_course:
        first_lesson_id = lessons_in_course[0].get('lesson_id')

    # 3. ตรวจสอบสถานะการลงทะเบียนและผลแบบทดสอบของผู้ใช้ปัจจุบัน (เหมือนเดิม)
    is_enrolled = False
    user_pre_test_attempt = None
    user_score_display = 0
    total_score_possible_display = 0
    percentage_score_display = 0.0
    passed_display = False

    if current_user.is_authenticated:
        cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (current_user.id, course_id,))
        if cursor.fetchone():
            is_enrolled = True
        
        if is_enrolled and course['pre_test_quiz_id']:
            cursor.execute("SELECT SUM(score) AS total_score FROM questions WHERE quiz_id = %s", (course['pre_test_quiz_id'],))
            total_score_result = cursor.fetchone()
            total_score_possible_display = total_score_result['total_score'] if total_score_result and total_score_result['total_score'] is not None else 0

            cursor.execute("""
                SELECT id, score, passed, attempt_date
                FROM user_quiz_attempts
                WHERE user_id = %s AND quiz_id = %s
                ORDER BY attempt_date DESC LIMIT 1
            """, (current_user.id, course['pre_test_quiz_id']))
            user_pre_test_attempt = cursor.fetchone()

            if user_pre_test_attempt:
                user_score_display = user_pre_test_attempt['score']
                passed_display = user_pre_test_attempt['passed']
                percentage_score_display = (user_score_display / total_score_possible_display) * 100 if total_score_possible_display > 0 else 0
                
    cursor.close()
    print(f"DEBUG: กำลังเรนเดอร์ course/course_detail.html สำหรับ course_id: {course_id}.")
    return render_template('course/course_detail.html', 
                           course=course, 
                           lessons_in_course=lessons_in_course,
                           is_enrolled=is_enrolled,
                           user_pre_test_attempt=user_pre_test_attempt,
                           user_score_display=user_score_display,           
                           total_score_possible_display=total_score_possible_display, 
                           percentage_score_display=percentage_score_display, 
                           passed_display=passed_display,
                           first_lesson_id=first_lesson_id)
    
@app.route('/user/lesson/<int:lesson_id>')
@login_required # ผู้ใช้ต้องล็อกอินก่อน
def user_view_lesson(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลบทเรียน
    cursor.execute("SELECT lesson_id, lesson_name, description, course_id FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard')) # หรือกลับไปหน้า course list

    # 2. ตรวจสอบว่าผู้ใช้ลงทะเบียนหลักสูตรนี้แล้วหรือไม่
    # ดึงข้อมูลหลักสูตรของบทเรียนนี้
    # ✅ ลบ pre_test_quiz_id ออกจาก SELECT
    cursor.execute("SELECT id, title FROM courses WHERE id = %s", (lesson['course_id'],)) 
    course_of_lesson = cursor.fetchone()

    if not course_of_lesson:
        flash('ไม่พบหลักสูตรที่เกี่ยวข้องกับบทเรียนนี้', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard'))

    # ตรวจสอบการลงทะเบียนหลักสูตร
    cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (current_user.id, course_of_lesson['id']))
    is_enrolled_in_course = cursor.fetchone()

    if not is_enrolled_in_course:
        flash('คุณยังไม่ได้ลงทะเบียนหลักสูตรนี้ กรุณาลงทะเบียนก่อน', 'warning')
        cursor.close()
        return redirect(url_for('course_detail', course_id=course_of_lesson['id']))

    # ✅ ลบ Logic การตรวจสอบ Pre-test ออกจากตรงนี้
    # เพราะการตรวจสอบนี้เกิดขึ้นที่หน้า course_detail ก่อนที่จะเข้ามาหน้านี้ได้
    # if course_of_lesson['pre_test_quiz_id']:
    #     cursor.execute("SELECT passed FROM user_quiz_attempts WHERE user_id = %s AND quiz_id = %s ORDER BY attempt_date DESC LIMIT 1",
    #                    (current_user.id, course_of_lesson['pre_test_quiz_id']))
    #     pre_test_result = cursor.fetchone()

    #     if not pre_test_result or not pre_test_result['passed']:
    #         flash('คุณต้องทำแบบทดสอบ Pre-test ของหลักสูตรนี้ให้ผ่านก่อนจึงจะเข้าถึงบทเรียนได้', 'warning')
    #         cursor.close()
    #         return redirect(url_for('course_detail', course_id=course_of_lesson['id']))


    # 4. ดึงเนื้อหา (วิดีโอ/แบบทดสอบ) ที่ผูกกับบทเรียนนี้
    cursor.execute("""
        SELECT video_id, title, youtube_link, description, time_duration, video_image, quiz_id
        FROM quiz_video
        WHERE lesson_id = %s AND quiz_id IS NULL
        ORDER BY video_id ASC
    """, (lesson_id,))
    lesson_contents = cursor.fetchall()

    cursor.close()
    return render_template('course/user_view_lesson.html', 
                           lesson=lesson, 
                           course=course_of_lesson, 
                           lesson_contents=lesson_contents)

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
    
@app.route('/user/course/<int:course_id>/learning_path')
@login_required
def user_learning_path(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลหลักสูตร (ไม่มี Pre-test quiz หลักสูตรใน SELECT แล้ว)
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
    try:
        cursor.execute(query, (course_id,))
        course_data = cursor.fetchone()
    except Exception as e:
        print(f"ERROR: SQL Error in user_learning_path course query: {e}")
        flash(f"เกิดข้อผิดพลาดในการดึงข้อมูลหลักสูตรสำหรับเส้นทางการเรียนรู้: {str(e)}", "danger")
        cursor.close()
        return redirect(url_for('user_dashboard'))

    if not course_data:
        flash('ไม่พบหลักสูตรที่ระบุ หรือหลักสูตรยังไม่เผยแพร่', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard'))

    course_for_template = {
        'id': course_data['id'], 'title': course_data['course_name'], 'description': course_data.get('description', ''),
        'featured_image': course_data['featured_image'], 'featured_video': course_data['featured_video'],
        'category': {'id': course_data['category_id'], 'name': course_data['category_name']},
        'instructor': {'id': course_data['instructor_id'], 'first_name': course_data['first_name'], 'last_name': course_data['last_name']},
        'status': course_data.get('status')
    }

    # 2. ตรวจสอบว่าผู้ใช้ลงทะเบียนหลักสูตรนี้แล้วหรือไม่
    cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (current_user.id, course_id,))
    is_enrolled = cursor.fetchone()
    if not is_enrolled:
        flash('คุณยังไม่ได้ลงทะเบียนหลักสูตรนี้ กรุณาลงทะเบียนก่อน', 'warning')
        cursor.close()
        return redirect(url_for('course_detail', course_id=course_id))

    # 3. ดึงบทเรียนทั้งหมดของหลักสูตรนี้
    cursor.execute("""
        SELECT lesson_id, lesson_name, description
        FROM lesson
        WHERE course_id = %s
        ORDER BY lesson_date ASC
    """, (course_id,))
    lessons_raw = cursor.fetchall()

    learning_path_data = []
    
    VIDEO_WEIGHT = 1
    QUIZ_WEIGHT = 1 # ใช้สำหรับ Pre-test บทเรียน, Post-test บทเรียน, Quiz Content

    total_possible_learning_points = 0
    user_earned_learning_points = 0

    # 4. ลบ Pre-test หลักสูตร (ไม่มีส่วนนี้แล้ว)
    # if course_for_template['pre_test_quiz_id_course']: ...

    # 5. วนลูปบทเรียนและเนื้อหา (Pre-test บทเรียน, วิดีโอ, Post-test บทเรียน)
    for lesson_row in lessons_raw:
        learning_path_data.append({
            'type': 'lesson',
            'lesson_id': lesson_row['lesson_id'],
            'title': lesson_row['lesson_name'],
            'description': lesson_row['description']
        })
        
        # ดึงเนื้อหา (วิดีโอและแบบทดสอบ) ที่ผูกกับบทเรียนนี้
        cursor.execute("""
            SELECT video_id, title, youtube_link, description, time_duration, video_image, quiz_id
            FROM quiz_video
            WHERE lesson_id = %s
            ORDER BY video_id ASC
        """, (lesson_row['lesson_id'],))
        contents_raw = cursor.fetchall()

        # แยกวิดีโอ, Pre-test บทเรียน, Post-test บทเรียน
        lesson_pre_test_quiz = None # เปลี่ยนชื่อตัวแปร
        lesson_post_test_quiz = None # เปลี่ยนชื่อตัวแปร
        lesson_videos = []
        lesson_other_quizzes = [] # สำหรับแบบทดสอบอื่นๆ ที่ไม่ใช่ pre/post

        for content_row in contents_raw:
            if content_row['quiz_id']: # ถ้าเป็นแบบทดสอบ
                cursor.execute("SELECT quiz_name, quiz_type, passing_percentage FROM quiz WHERE quiz_id = %s", (content_row['quiz_id'],))
                quiz_info = cursor.fetchone()

                if quiz_info and quiz_info['quiz_type'] == 'Pre-test': # ✅ Pre-test บทเรียน
                    lesson_pre_test_quiz = {
                        'quiz_id': content_row['quiz_id'],
                        'title': f"แบบทดสอบก่อนบทเรียน: {quiz_info['quiz_name']}",
                        'passing_percentage': quiz_info['passing_percentage']
                    }
                elif quiz_info and quiz_info['quiz_type'] == 'Post_test': # ✅ Post-test บทเรียน
                    lesson_post_test_quiz = {
                        'quiz_id': content_row['quiz_id'],
                        'title': f"แบบทดสอบหลังบทเรียน: {quiz_info['quiz_name']}",
                        'passing_percentage': quiz_info['passing_percentage']
                    }
                else: # แบบทดสอบอื่นๆ ที่ไม่ใช่ Pre/Post-test ของบทเรียน
                     lesson_other_quizzes.append({
                        'quiz_id': content_row['quiz_id'],
                        'title': f"แบบทดสอบ: {quiz_info['quiz_name'] if quiz_info else content_row['title']}",
                        'passing_percentage': quiz_info['passing_percentage'] if quiz_info else 0
                    })

            else: # ถ้าเป็นวิดีโอ
                lesson_videos.append(content_row) # เก็บวิดีโอไว้ใน list แยกต่างหาก

        # ✅ เพิ่ม Pre-test บทเรียน (ถ้ามี)
        if lesson_pre_test_quiz:
            total_possible_learning_points += QUIZ_WEIGHT
            cursor.execute("SELECT score, passed FROM user_quiz_attempts WHERE user_id = %s AND quiz_id = %s ORDER BY attempt_date DESC LIMIT 1",
                           (current_user.id, lesson_pre_test_quiz['quiz_id']))
            pre_test_attempt_lesson = cursor.fetchone()
            
            pre_test_status_lesson = "ยังไม่ทำ"
            pre_test_score = pre_test_attempt_lesson['score'] if pre_test_attempt_lesson and pre_test_attempt_lesson['score'] is not None else 0
            pre_test_passed = pre_test_attempt_lesson['passed'] if pre_test_attempt_lesson and pre_test_attempt_lesson['passed'] is not None else False

            if pre_test_attempt_lesson:
                pre_test_status_lesson = "ผ่าน" if pre_test_passed else "ไม่ผ่าน"
                if pre_test_passed:
                    user_earned_learning_points += QUIZ_WEIGHT
            
            learning_path_data.append({
                'type': 'pre_test_lesson', # ประเภทใหม่สำหรับ Pre-test บทเรียน
                'quiz_id': lesson_pre_test_quiz['quiz_id'],
                'title': lesson_pre_test_quiz['title'],
                'status': pre_test_status_lesson,
                'passed': pre_test_passed,
                'score': pre_test_score,
                'passing_percentage': lesson_pre_test_quiz['passing_percentage']
            })
        
        # เพิ่มวิดีโอของบทเรียน
        for video_row in lesson_videos:
            total_possible_learning_points += VIDEO_WEIGHT
            cursor.execute("SELECT is_completed FROM user_lesson_progress WHERE user_id = %s AND video_id = %s",
                           (current_user.id, video_row['video_id']))
            video_progress = cursor.fetchone()
            
            video_status = "ยังไม่ได้ดู"
            is_video_completed = video_progress['is_completed'] if video_progress and video_progress['is_completed'] is not None else False

            if video_progress and is_video_completed:
                video_status = "ดูแล้ว"
                user_earned_learning_points += VIDEO_WEIGHT

            learning_path_data.append({
                'type': 'video_content',
                'video_id': video_row['video_id'],
                'lesson_id': lesson_row['lesson_id'],
                'title': f"วิดีโอ: {video_row['title']}",
                'status': video_status,
                'is_completed': is_video_completed,
                'youtube_link': video_row['youtube_link'],
                'description': video_row['description']
            })

        # เพิ่ม Post-test บทเรียน (ถ้ามี)
        if lesson_post_test_quiz: # ✅ ใช้ lesson_post_test_quiz
            total_possible_learning_points += QUIZ_WEIGHT
            cursor.execute("SELECT score, passed FROM user_quiz_attempts WHERE user_id = %s AND quiz_id = %s ORDER BY attempt_date DESC LIMIT 1",
                           (current_user.id, lesson_post_test_quiz['quiz_id']))
            post_test_attempt_lesson = cursor.fetchone()
            
            post_test_status_lesson = "ยังไม่ทำ"
            post_test_score = post_test_attempt_lesson['score'] if post_test_attempt_lesson and post_test_attempt_lesson['score'] is not None else 0
            post_test_passed = post_test_attempt_lesson['passed'] if post_test_attempt_lesson and post_test_attempt_lesson['passed'] is not None else False

            if post_test_attempt_lesson:
                post_test_status_lesson = "ผ่าน" if post_test_passed else "ไม่ผ่าน"
                if post_test_passed:
                    user_earned_learning_points += QUIZ_WEIGHT
            
            learning_path_data.append({
                'type': 'post_test_lesson', # ประเภทใหม่สำหรับ Post-test บทเรียน
                'quiz_id': lesson_post_test_quiz['quiz_id'],
                'title': lesson_post_test_quiz['title'],
                'status': post_test_status_lesson,
                'passed': post_test_passed,
                'score': post_test_score,
                'passing_percentage': lesson_post_test_quiz['passing_percentage']
            })
        
        # ✅ เพิ่มแบบทดสอบอื่นๆ ที่ไม่ใช่ Pre/Post-test ของบทเรียน
        for other_quiz_row in lesson_other_quizzes:
            total_possible_learning_points += QUIZ_WEIGHT # นับน้ำหนัก
            
            # ตรวจสอบผลแบบทดสอบของเนื้อหานั้นๆ
            other_quiz_status = "ยังไม่ทำ"
            other_quiz_passed = False
            user_other_quiz_attempt = None
            cursor.execute("SELECT score, passed FROM user_quiz_attempts WHERE user_id = %s AND quiz_id = %s ORDER BY attempt_date DESC LIMIT 1",
                           (current_user.id, other_quiz_row['quiz_id']))
            user_other_quiz_attempt = cursor.fetchone()
            
            other_quiz_score = user_other_quiz_attempt['score'] if user_other_quiz_attempt and user_other_quiz_attempt['score'] is not None else 0
            other_quiz_passed = user_other_quiz_attempt['passed'] if user_other_quiz_attempt and user_other_quiz_attempt['passed'] is not None else False

            if user_other_quiz_attempt:
                other_quiz_status = "ผ่าน" if other_quiz_passed else "ไม่ผ่าน"
                if other_quiz_passed:
                    user_earned_learning_points += QUIZ_WEIGHT

            learning_path_data.append({
                'type': 'quiz_content', # ใช้ประเภท 'quiz_content'
                'quiz_id': other_quiz_row['quiz_id'],
                'title': other_quiz_row['title'],
                'status': other_quiz_status,
                'passed': other_quiz_passed,
                'score': other_quiz_score,
                'passing_percentage': other_quiz_row['passing_percentage']
            })


    # 6. ลบ Post-test หลักสูตรออก (ไม่มีส่วนนี้แล้ว)
    # ...

    # 7. คำนวณเปอร์เซ็นต์ความคืบหน้ารวม
    if total_possible_learning_points > 0:
        overall_progress_percentage = (user_earned_learning_points / total_possible_learning_points) * 100
    else:
        overall_progress_percentage = 0.0

    cursor.close()
    return render_template('course/learning_path.html', 
                           course=course_for_template, 
                           learning_path_data=learning_path_data,
                           overall_progress_percentage=overall_progress_percentage)
    
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

@app.route('/user/video/mark_watched_auto', methods=['POST'])
@login_required
def mark_video_as_watched_auto():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    user_id = current_user.id # ดึง user_id จาก Flask-Login
    video_id = request.form.get('video_id', type=int)
    lesson_id = request.form.get('lesson_id', type=int)
    course_id = request.form.get('course_id', type=int)

    # ตรวจสอบข้อมูลที่รับมา
    if not user_id or not video_id or not lesson_id or not course_id:
        print(f"ERROR: mark_video_as_watched_auto - Missing data: user_id={user_id}, video_id={video_id}, lesson_id={lesson_id}, course_id={course_id}")
        return jsonify({'status': 'error', 'message': 'ข้อมูลไม่สมบูรณ์'}), 400

    try:
        # ตรวจสอบว่าผู้ใช้ลงทะเบียนหลักสูตรนี้แล้วหรือไม่ (เพื่อความปลอดภัย)
        cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (user_id, course_id))
        is_enrolled = cursor.fetchone()
        if not is_enrolled:
            print(f"WARNING: User {user_id} not enrolled in course {course_id}. Cannot mark video {video_id} as watched.")
            cursor.close()
            return jsonify({'status': 'error', 'message': 'คุณยังไม่ได้ลงทะเบียนหลักสูตรนี้'}), 403

        # บันทึก/อัปเดตสถานะการดูวิดีโอ
        cursor.execute("""
            INSERT INTO user_lesson_progress (user_id, video_id, lesson_id, is_completed, completed_at)
            VALUES (%s, %s, %s, TRUE, %s)
            ON DUPLICATE KEY UPDATE is_completed = TRUE, completed_at = %s
        """, (user_id, video_id, lesson_id, datetime.now(), datetime.now()))
        
        mysql.connection.commit()
        print(f"DEBUG: Video {video_id} marked as watched by user {user_id} successfully.")
        return jsonify({'status': 'success', 'message': 'ทำเครื่องหมายวิดีโอว่าดูแล้วเรียบร้อย!'})
    except Exception as e:
        mysql.connection.rollback()
        print(f"ERROR: mark_video_as_watched_auto failed: {e}")
        return jsonify({'status': 'error', 'message': f'เกิดข้อผิดพลาดในการทำเครื่องหมายวิดีโอ: {str(e)}'}), 500
    finally:
        cursor.close()

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

@app.route('/quiz/submit/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลแบบทดสอบ (Quiz) เพื่อตรวจสอบเกณฑ์ผ่าน
    cursor.execute("SELECT quiz_id, quiz_name, passing_percentage, lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    print(f"\n--- DEBUG: submit_quiz for quiz_id: {quiz_id} ---")

    if not quiz:
        flash('แบบทดสอบไม่ถูกต้อง', 'danger')
        cursor.close()
        print(f"DEBUG: ไม่พบบททดสอบ ID {quiz_id}. Redirect ไปที่ user_dashboard.")
        return redirect(url_for('user_dashboard'))

    # 2. ดึงคำถามทั้งหมดของแบบทดสอบนี้ (พร้อมคำตอบที่ถูกต้อง)
    cursor.execute("SELECT question_id, correct_answer, score FROM questions WHERE quiz_id = %s", (quiz_id,))
    questions_data = cursor.fetchall()

    user_score = 0
    total_score_possible = 0
    percentage_score = 0.0
    passed = False

    if questions_data:
        total_score_possible = sum(q['score'] for q in questions_data)
        
        for question in questions_data:
            question_id_str = str(question['question_id'])
            user_answer = request.form.get(f'question_{question_id_str}')
            
            if user_answer and user_answer.lower() == question['correct_answer'].lower():
                user_score += question['score']

        percentage_score = (user_score / total_score_possible) * 100 if total_score_possible > 0 else 0
        passed = percentage_score >= quiz['passing_percentage']
    else:
        flash('แบบทดสอบนี้ไม่มีคำถาม', 'warning')
        print("DEBUG: แบบทดสอบไม่มีคำถาม.")

    # บันทึกผลการทำแบบทดสอบลงในตาราง user_quiz_attempts
    try:
        cursor.execute("""
            INSERT INTO user_quiz_attempts (user_id, quiz_id, score, passed, attempt_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_user.id, quiz_id, user_score, passed, datetime.now()))
        mysql.connection.commit()
        flash(f"คุณทำแบบทดสอบ '{quiz['quiz_name']}' เสร็จสิ้น! คะแนน: {user_score}/{total_score_possible} ({percentage_score:.2f}%)", 'success')
        print("DEBUG: Quiz attempt saved to DB successfully!")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"เกิดข้อผิดพลาดในการบันทึกผลแบบทดสอบ: {str(e)}", 'danger')
        print(f"ERROR: Database insertion failed in submit_quiz: {e}")
    finally:
        cursor.close()

    redirect_lesson_id = quiz.get('lesson_id')
    print(f"DEBUG: quiz.get('lesson_id') = '{redirect_lesson_id}' (Type: {type(redirect_lesson_id)})")

    # ✅ ดึง course_id จาก lesson_id เพื่อใช้ในการ redirect
    if redirect_lesson_id is not None:
        cursor_temp = mysql.connection.cursor(MySQLdb.cursors.DictCursor) # ใช้ cursor ใหม่เพื่อความปลอดภัย
        cursor_temp.execute("SELECT course_id FROM lesson WHERE lesson_id = %s", (redirect_lesson_id,))
        lesson_info = cursor_temp.fetchone()
        cursor_temp.close()

        if lesson_info and lesson_info.get('course_id') is not None:
            final_redirect_course_id = lesson_info['course_id']
            print(f"DEBUG: Redirecting to course_detail for course_id: {final_redirect_course_id}.")
            return redirect(url_for('course_detail', course_id=final_redirect_course_id))
        else:
            print(f"DEBUG: ไม่พบ course_id สำหรับ lesson_id {redirect_lesson_id}. Redirect ไปที่ /course.")
            flash('ไม่พบหลักสูตรที่เกี่ยวข้องกับแบบทดสอบนี้', 'danger')
            return redirect(url_for('course'))
    else:
        print(f"DEBUG: lesson_id for quiz {quiz_id} is None. Redirecting to /course.")
        flash('ไม่พบหลักสูตรที่เกี่ยวข้องกับแบบทดสอบนี้', 'danger')
        return redirect(url_for('course'))
# ✅ Placeholder Route สำหรับสร้างใบประกาศ
@app.route('/course/certificate/<int:course_id>', methods=['GET'])
@login_required
def generate_certificate(course_id):
    # ในอนาคต Logic ตรงนี้จะตรวจสอบว่าผู้ใช้ผ่านหลักสูตรจริงไหม แล้วค่อยสร้าง PDF/Image certificate
    flash(f"กำลังจะออกใบประกาศสำหรับหลักสูตร ID: {course_id} (ฟังก์ชันยังไม่สมบูรณ์)", "info")
    # ✅ คุณจะต้องสร้าง logic การสร้างใบประกาศจริงในอนาคต
    return redirect(url_for('user_dashboard'))

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
    form = LessonForm()

    cursor.execute('SELECT id, title FROM courses WHERE status = "publish"')
    courses_data = cursor.fetchall()
    form.course_id.choices = [(course['id'], course['title']) for course in courses_data]
    form.course_id.choices.insert(0, (0, '-- เลือกหลักสูตร --'))

    cursor.execute('SELECT id, first_name, last_name FROM instructor')
    instructors_data = cursor.fetchall()
    form.instructor_id.choices = [(ins['id'], f"{ins['first_name']} {ins['last_name']}") for ins in instructors_data]
    form.instructor_id.choices.insert(0, (0, '-- เลือกผู้สอน --'))

    if form.validate_on_submit():
        lesson_name = form.title.data
        course_id = form.course_id.data
        instructor_id = form.instructor_id.data
        # ลบบรรทัดนี้ออก: video_url = form.video_url.data
        lesson_date = form.lesson_date.data

        if course_id == 0:
            flash('กรุณาเลือกหลักสูตร', 'danger')
            cursor.close()
            return render_template('admin/add_lesson.html', form=form)
        if instructor_id == 0:
            flash('กรุณาเลือกผู้สอน', 'danger')
            cursor.close()
            return render_template('admin/add_lesson.html', form=form)

        if lesson_date is None:
            lesson_date = datetime.now().date()

        # อัปเดต INSERT query (ลบ 'video_url' ออก)
        cursor.execute(
            'INSERT INTO lesson (lesson_name, course_id, instructor_id, lesson_date) VALUES (%s, %s, %s, %s)',
            (lesson_name, course_id, instructor_id, lesson_date)
        )
        # ตรวจสอบว่าจำนวน %s ใน query (4 ตัว) ตรงกับจำนวน parameter ที่ส่งไป (lesson_name, course_id, instructor_id, lesson_date) (4 ตัว)
        # ตัวอย่างข้างบนถูกต้องแล้ว

        mysql.connection.commit()
        cursor.close()
        flash('เพิ่มบทเรียนสำเร็จ', 'success')
        return redirect(url_for('lesson', course_id=course_id))

    cursor.close()
    return render_template('admin/add_lesson.html', form=form)

@app.route('/admin/lesson/edit/<int:lesson_id>', methods=['GET', 'POST'])
@admin_required
def edit_lesson(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลบทเรียน (ลบ 'video_url' ออกจาก SELECT)
    cursor.execute("SELECT lesson_id, lesson_name, lesson_date, course_id FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson_data = cursor.fetchone()

    if not lesson_data:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('admin_dashboard'))

    course_id = lesson_data['course_id']
    cursor.execute("SELECT title FROM courses WHERE id = %s", (course_id,))
    course_info = cursor.fetchone()
    course_name_for_template = course_info['title'] if course_info else "ไม่ระบุคอร์ส"

    class TempCourse:
        def __init__(self, name, id):
            self.course_name = name
            self.id = id

    class TempLessonForTemplate:
        def __init__(self, data, course_name, course_id):
            self.id = data['lesson_id']
            self.lesson_id = data['lesson_id']
            self.title = data['lesson_name']
            # ลบบรรทัดนี้ออก: self.video_url = data.get('video_url', '')
            self.lesson_date = data.get('lesson_date')
            self.course_id = course_id
            self.course = TempCourse(course_name, course_id)

    lesson_for_template = TempLessonForTemplate(lesson_data, course_name_for_template, course_id)

    # 4. สร้างฟอร์มด้วย Flask-WTF และป้อนข้อมูลเดิม (ลบ 'video_url' ออกจาก form_data)
    form_data = {
        'title': lesson_data.get('lesson_name'),
        # ลบบรรทัดนี้ออก: 'video_url': lesson_data.get('video_url', ''),
        'lesson_date': lesson_data.get('lesson_date')
    }
    form = LessonForm(data=form_data)

    if form.validate_on_submit():
        updated_title = form.title.data
        # ลบบรรทัดนี้ออก: updated_video_url = form.video_url.data
        updated_lesson_date = form.lesson_date.data

        # 6. อัปเดตข้อมูลในฐานข้อมูล (ลบ 'video_url' ออกจาก UPDATE query)
        cursor.execute("""
            UPDATE lesson SET
                lesson_name = %s,
                lesson_date = %s
            WHERE lesson_id = %s
        """, (updated_title, updated_lesson_date, lesson_id))
        # ตรวจสอบว่าจำนวน %s ใน query (2 ตัว) ตรงกับจำนวน parameter ที่ส่งไป (updated_title, updated_lesson_date, lesson_id) (3 ตัว)
        # จริงๆ แล้วคือ (updated_title, updated_lesson_date) เป็นตัวแปรที่ใช้กับ %s 2 ตัวแรก
        # lesson_id ใช้กับ WHERE lesson_id = %s สุดท้าย
        # ดังนั้น จำนวน parameter ต้องเป็น 3 ตัว (updated_title, updated_lesson_date, lesson_id)
        # ตัวอย่างข้างบนถูกต้องแล้ว

        mysql.connection.commit()
        flash('บทเรียนได้รับการแก้ไขเรียบร้อยแล้ว!', 'success')
        return redirect(url_for('lesson', course_id=lesson_for_template.course_id))

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



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    user_id = current_user.id
    current_role = current_user.role

    table_name = ""
    redirect_dashboard_url = ""
    select_query_columns = ""
    update_query_template = ""
    
    if current_role == 'admin':
        table_name = "admin"
        redirect_dashboard_url = 'admin_dashboard'
        select_query_columns = "id, username, email, first_name, last_name, tel, gender, profile_image, role" # ✅ เพิ่ม role
        update_query_template = """
            UPDATE admin SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s, profile_image=%s
            WHERE id=%s
        """
    elif current_role == 'instructor':
        table_name = "instructor"
        redirect_dashboard_url = 'instructor_dashboard'
        select_query_columns = "id, username, email, first_name, last_name, tel, gender, profile_image, role" # ✅ เพิ่ม role
        update_query_template = """
            UPDATE instructor SET first_name=%s, last_name=%s, email=%s, username=%s, tel=%s, gender=%s, profile_image=%s
            WHERE id=%s
        """
    elif current_role == 'user':
        table_name = "user"
        redirect_dashboard_url = 'user_dashboard'
        select_query_columns = "id, username, email, first_name, last_name, id_card, gender, profile_image, role" # ✅ เพิ่ม role
        update_query_template = """
            UPDATE user SET first_name=%s, last_name=%s, email=%s, username=%s, id_card=%s, gender=%s, profile_image=%s
            WHERE id=%s
        """
    else:
        flash("ไม่พบข้อมูลผู้ใช้สำหรับแก้ไข", "danger")
        return redirect(url_for('login'))


    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        tel = request.form.get('tel')
        gender = request.form.get('gender')
        id_card = request.form.get('id_card')
        
        profile_image_file = request.files.get('profile_image')
        
        cursor.execute(f"SELECT {select_query_columns} FROM {table_name} WHERE id = %s", (user_id,))
        current_user_data = cursor.fetchone() # ข้อมูลเดิม
        
        filename = current_user_data.get('profile_image') # ค่าเริ่มต้นคือรูปเดิม

        if profile_image_file and allowed_file(profile_image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            filename = secure_filename(profile_image_file.filename)
            upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER_PROFILE_IMAGES'])
            os.makedirs(upload_path, exist_ok=True)
            profile_image_file.save(os.path.join(upload_path, filename))
            if current_user_data.get('profile_image') and os.path.exists(os.path.join(upload_path, current_user_data['profile_image'])):
                try: os.remove(os.path.join(upload_path, current_user_data['profile_image']))
                except Exception as e: print(f"ERROR: Could not delete old profile image: {e}")
        elif profile_image_file and profile_image_file.filename == '':
            pass


        update_values = []
        if current_role == 'admin' or current_role == 'instructor':
            update_values = (first_name, last_name, email, username, tel, gender, filename, user_id)
        elif current_role == 'user':
            update_values = (first_name, last_name, email, username, id_card, gender, filename, user_id)
        
        try:
            cursor.execute(update_query_template, update_values)
            mysql.connection.commit()
            flash('แก้ไขโปรไฟล์เรียบร้อยแล้ว!', 'success')
            
            # ✅ รีโหลด current_user object โดยใช้ _update_current_user
            if not _update_current_user(user_id, current_role, table_name, select_query_columns):
                flash('เกิดข้อผิดพลาดในการรีโหลดโปรไฟล์', 'danger')
                print(f"ERROR: Failed to reload current_user for ID {user_id}, Role {current_role}")
            
            cursor.close()
            return redirect(url_for(redirect_dashboard_url))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึกโปรไฟล์: {str(e)}', 'danger')
            print(f"ERROR: Profile update failed: {e}")
            cursor.close()
            return render_template(f'{current_role}/edit_profile.html', user=current_user_data)


    cursor.execute(f"SELECT {select_query_columns} FROM {table_name} WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()

    if not user_data:
        flash("ไม่พบข้อมูลโปรไฟล์", "danger")
        return redirect(url_for('login'))
    
    return render_template(f'{current_role}/edit_profile.html', user=user_data)

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

@app.route('/instructor/course/add', methods=['GET', 'POST']) # URL สำหรับ Instructor
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_add_course(): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_add_course'
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึง instructor (รวมชื่อ + นามสกุล)
    # ควรดึงเฉพาะ instructor ที่ล็อกอินอยู่ หรือ instructor ที่เกี่ยวข้องกับหลักสูตรของเขา
    # แต่สำหรับตอนนี้ ดึง instructor ทั้งหมดไปก่อนเพื่อไม่ให้เกิดข้อผิดพลาด
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS name FROM instructor")
    instructors = cursor.fetchall()

    # ดึง categories
    cursor.execute("SELECT id, name AS name FROM categories")
    categories = cursor.fetchall()

    if request.method == 'POST':
        course_name = request.form['course_name']
        instructor_id = request.form['instructor_id'] # ควรเป็น ID ของ instructor ที่ล็อกอินอยู่
        category_id = request.form['category_id']
        description = request.form['description']
        status = request.form['status'] # เช่น 'publish', 'draft'

        # รูปภาพหลักสูตร
        course_image = request.files.get('course_image')
        image_filename = None
        if course_image and allowed_file(course_image.filename, ALLOWED_IMAGE_EXTENSIONS):
            image_filename = secure_filename(course_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], image_filename)
            os.makedirs(image_path, exist_ok=True)
            course_image.save(image_path)

        # วิดีโอแนะนำ (ใช้ชื่อ 'featured_video' ให้ตรงกับฐานข้อมูล)
        featured_video = request.files.get('featured_video')
        video_filename = None
        if featured_video and allowed_file(featured_video.filename, ALLOWED_VIDEO_EXTENSIONS):
            video_filename = secure_filename(featured_video.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], video_filename)
            os.makedirs(video_path, exist_ok=True)
            featured_video.save(video_path)

        # บันทึกลงฐานข้อมูล
        cursor.execute("""
            INSERT INTO courses (title, instructor_id, categories_id, description, featured_image, featured_video, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (course_name, instructor_id, category_id, description, image_filename, video_filename, status))

        mysql.connection.commit()
        cursor.close()

        flash('เพิ่มหลักสูตรเรียบร้อยแล้ว', 'success')
        return redirect(url_for('instructor_course_list')) # ✅ กลับไปหน้ารายการหลักสูตรของ Instructor

    cursor.close()
    # ✅ ใช้ template ของ Instructor
    return render_template('instructor/add_course.html', instructors=instructors, categories=categories)

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

@app.route('/instructor/course/delete/<int:course_id>', methods=['POST']) # URL สำหรับ Instructor และใช้ POST เท่านั้น
@instructor_required # ✅ ใช้ decorator ของ Instructor
def instructor_delete_course(course_id): # ✅ ชื่อฟังก์ชันนี้คือ endpoint 'instructor_delete_course'
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ดึงข้อมูลหลักสูตรก่อน เพื่อให้รู้ชื่อไฟล์รูปภาพและวิดีโอ (ถ้ามี)
    cur.execute("SELECT featured_image, featured_video FROM courses WHERE id = %s", (course_id,))
    course = cur.fetchone()

    # ลบไฟล์รูปภาพและวิดีโอ (ถ้ามี)
    if course:
        if course['featured_image']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], course['featured_image'])
            try:
                os.remove(image_path)
            except FileNotFoundError:
                print(f"File not found: {image_path}") # พิมพ์ข้อความถ้าหาไฟล์ไม่เจอ
        if course['featured_video']:
            video_path = os.path.join(app.config['UPLOAD_FOLDER_VIDEOS'], course['featured_video'])
            try:
                os.remove(video_path)
            except FileNotFoundError:
                print(f"File not found: {video_path}") # พิมพ์ข้อความถ้าหาไฟล์ไม่เจอ

    # ลบหลักสูตรจากฐานข้อมูล
    cur.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    mysql.connection.commit()

    cur.close()
    flash('ลบหลักสูตรเรียบร้อยแล้ว', 'success')
    return redirect(url_for('instructor_course_list'))


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
def instructor_add_video(lesson_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT lesson_id, lesson_name FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('instructor_dashboard'))

    if request.method == 'POST':
        # --- DEBUG: รับ POST Request ---
        print(f"\n--- DEBUG: instructor_add_video - POST Request Received for Lesson ID: {lesson_id} ---")
        print(f"DEBUG: Form Data: {request.form}")
        print(f"DEBUG: Files Data: {request.files}")
        # --- สิ้นสุด DEBUG ---

        title = request.form.get('title', '').strip() # ใช้ .get() และ .strip() ให้ปลอดภัย
        youtube_link = request.form.get('youtube_link', '').strip()
        description = request.form.get('description', '').strip()
        time_duration = request.form.get('time_duration', '').strip()
        video_image = None

        # ✅ เพิ่มการตรวจสอบข้อมูลเบื้องต้น
        if not title:
            flash('กรุณาระบุหัวข้อวิดีโอ', 'danger')
            cursor.close()
            return render_template('instructor/add_video.html', lesson=lesson)
        if not youtube_link: # หรือตรวจสอบว่าเป็น URL ที่ถูกต้อง
             flash('กรุณาระบุลิงก์ YouTube', 'danger')
             cursor.close()
             return render_template('instructor/add_video.html', lesson=lesson)


        # อัปโหลดรูปภาพ (ถ้ามี)
        if 'video_image' in request.files:
            file = request.files['video_image']
            if file and file.filename != '' and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER_VIDEO_IMAGES'])
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                video_image = filename
                print(f"DEBUG: Video image uploaded: {video_image}")
            elif file and file.filename == '':
                print("DEBUG: No video image file selected.")
            else:
                flash('ไฟล์รูปภาพไม่ถูกต้อง', 'warning')
                print("DEBUG: Invalid video image file.")
        
        # --- DEBUG: ข้อมูลที่จะบันทึก ---
        print(f"DEBUG: Data to insert:")
        print(f"DEBUG: Title: '{title}'")
        print(f"DEBUG: YouTube Link: '{youtube_link}'")
        print(f"DEBUG: Description: '{description}'")
        print(f"DEBUG: Time Duration: '{time_duration}'")
        print(f"DEBUG: Video Image: '{video_image}'")
        print(f"DEBUG: Lesson ID: {lesson_id}")
        # --- สิ้นสุด DEBUG ---

        # บันทึกข้อมูลลงฐานข้อมูล
        try:
            cursor.execute("""
                INSERT INTO quiz_video (title, youtube_link,  time_duration, video_image, lesson_id, quiz_id)
                VALUES (%s, %s, %s, %s, %s, %s, NULL)
            """, (title, youtube_link, description, time_duration, video_image, lesson_id))
            mysql.connection.commit()
            flash('เพิ่มวิดีโอสำเร็จ', 'success')
            print("DEBUG: Video saved to DB successfully!")
            cursor.close()
            return redirect(url_for('instructor_quiz_and_video', lesson_id=lesson_id))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการเพิ่มวิดีโอ: {str(e)}', 'danger')
            print(f"ERROR: Database insertion failed: {e}") # พิมพ์ข้อผิดพลาดฐานข้อมูลเต็มๆ
            cursor.close()
            return render_template('instructor/add_video.html', lesson=lesson)


    cursor.close()
    return render_template('instructor/add_video.html', lesson=lesson)

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

@app.route('/instructor/add_lesson', methods=['GET', 'POST']) # ✅ URL สำหรับ Instructor (ไม่มี course_id ใน URL)
@instructor_required # ✅ ใช้ decorator สำหรับ Instructor
def instructor_add_lesson(): # ✅ เปลี่ยนชื่อฟังก์ชันเพื่อให้ไม่ซ้ำกับของ admin
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    form = LessonForm()

    # ดึงหลักสูตรทั้งหมดที่ Instructor สามารถเลือกได้ (อาจจะกรองแค่หลักสูตรของ Instructor คนนั้นๆ)
    # สำหรับตอนนี้ ดึงหลักสูตรทั้งหมดที่มีสถานะ "publish" เหมือนเดิม
    cursor.execute('SELECT id, title FROM courses WHERE status = "publish" ORDER BY title ASC')
    courses_data = cursor.fetchall()
    form.course_id.choices = [(course['id'], course['title']) for course in courses_data]
    form.course_id.choices.insert(0, (0, '-- เลือกหลักสูตร --'))

    # ดึงผู้สอนทั้งหมด (ในอนาคตอาจจะกรองแค่ Instructor ที่ล็อกอินอยู่)
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM instructor ORDER BY first_name ASC")
    instructors_data = cursor.fetchall()
    form.instructor_id.choices = [(ins['id'], ins['full_name']) for ins in instructors_data]
    form.instructor_id.choices.insert(0, (0, '-- เลือกผู้สอน --'))

    if form.validate_on_submit():
        lesson_name = form.title.data
        course_id = form.course_id.data
        instructor_id = form.instructor_id.data
        lesson_date = form.lesson_date.data if form.lesson_date.data else datetime.now().date()

        if course_id == 0:
            flash('กรุณาเลือกหลักสูตร', 'danger')
            cursor.close()
            # ✅ ต้องส่ง instructors_data และ courses_data กลับไปด้วย
            return render_template('instructor/add_lesson.html', form=form, instructors=instructors_data, courses=courses_data)
        if instructor_id == 0:
            flash('กรุณาเลือกผู้สอน', 'danger')
            cursor.close()
            # ✅ ต้องส่ง instructors_data และ courses_data กลับไปด้วย
            return render_template('instructor/add_lesson.html', form=form, instructors=instructors_data, courses=courses_data)

        try:
            cursor.execute(
                'INSERT INTO lesson (lesson_name, course_id, instructor_id, lesson_date) VALUES (%s, %s, %s, %s)',
                (lesson_name, course_id, instructor_id, lesson_date)
            )
            mysql.connection.commit()
            flash('เพิ่มบทเรียนสำเร็จ', 'success')
            cursor.close()
            # ✅ Redirect ไปยังหน้ารายการบทเรียนของหลักสูตรที่เพิ่ม
            return redirect(url_for('instructor_lesson', course_id=course_id))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"เกิดข้อผิดพลาดในการเพิ่มบทเรียน: {str(e)}", "danger")
            cursor.close()
            # ✅ ต้องส่ง instructors_data และ courses_data กลับไปด้วย
            return render_template('instructor/add_lesson.html', form=form, instructors=instructors_data, courses=courses_data)

    cursor.close()
    # ✅ ส่ง instructors_data และ courses_data ไปให้เทมเพลต
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



@app.route('/user/dashboard')
def user_dashboard():
    return render_template('user/user_dashboard.html')




if __name__ == '__main__':
    app.run(debug=True)