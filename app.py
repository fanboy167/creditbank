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
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, IntegerField
from wtforms.validators import DataRequired, URL, Optional, Length, NumberRange


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

class QuizForm(FlaskForm):
    quiz_name = StringField('ชื่อแบบทดสอบ', validators=[DataRequired(message="กรุณาระบุชื่อแบบทดสอบ"), Length(max=255)])
    # quiz_type จะเป็น SelectField ที่กำหนด choices ใน route
    quiz_type = SelectField('ประเภทแบบทดสอบ', coerce=str, validators=[DataRequired(message="กรุณาเลือกประเภท")])
    # passing_percentage เป็น IntegerField และกำหนดช่วงค่า
    passing_percentage = IntegerField('เปอร์เซ็นต์ผ่าน', validators=[DataRequired(message="กรุณาระบุเปอร์เซ็นต์ผ่าน"), NumberRange(min=0, max=100, message="ต้องอยู่ระหว่าง 0-100")])
    select_quiz_id = SelectField('เลือกแบบทดสอบที่ต้องการแก้ไข', coerce=int)
    lesson_id = SelectField('บทเรียนที่เกี่ยวข้อง', coerce=int, validators=[DataRequired(message="กรุณาเลือกบทเรียน")])
# ---------------------------------------------------------------------------------------------

class LessonForm(FlaskForm):
    title = StringField('ชื่อบทเรียน', validators=[DataRequired(message="กรุณาระบุชื่อบทเรียน")])
    # ใช้ Optional() ถ้า URL ไม่จำเป็นต้องใส่เสมอไป
    # ตรวจสอบ format ของวันที่ในฐานข้อมูลของคุณว่าตรงกับ '%Y-%m-%d' หรือไม่ ถ้าไม่ตรงให้ปรับแก้
    lesson_date = DateField('วันที่สร้างบทเรียน', format='%Y-%m-%d')
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

    # 1. ดึงข้อมูลหลักสูตรที่ระบุ
    # ✅ แก้ไข SQL Query เพื่อดึง Pre-test quiz อย่างถูกต้อง
    query = """
    SELECT
      c.id, c.title AS course_name, c.description, c.featured_image, c.featured_video,
      cat.id AS category_id, cat.name AS category_name,
      i.id AS instructor_id, i.first_name, i.last_name,
      
      -- ดึงข้อมูล Pre-test quiz ที่ผูกกับหลักสูตรนี้
      -- เราจะ LEFT JOIN กับตาราง lesson และ quiz โดยตรง
      -- และใช้ WHERE clause เพื่อกรอง Pre-test
      pre_q.quiz_id AS pre_test_quiz_id,
      pre_q.quiz_name AS pre_test_quiz_name,
      pre_q.passing_percentage AS pre_test_passing_percentage
    FROM courses c
    LEFT JOIN categories cat ON c.categories_id = cat.id
    LEFT JOIN instructor i ON c.instructor_id = i.id
    
    -- LEFT JOIN กับ lesson และ quiz เพื่อหา Pre-test
    -- โดยจะเลือกเฉพาะ quiz ที่เป็น Pre-test และผูกกับ lesson ของ course นี้
    LEFT JOIN lesson AS l_pre ON l_pre.course_id = c.id
    LEFT JOIN quiz AS pre_q ON pre_q.lesson_id = l_pre.lesson_id AND pre_q.quiz_type = 'Pre-test'
    
    WHERE c.id = %s AND c.status = 'publish'
    -- เนื่องจากเราใช้ LEFT JOIN และ LIMIT 1, ถ้ามีหลาย Pre-test ในหลักสูตร
    -- มันจะเลือกมาแค่ 1 ตัวแรกที่เจอ
    LIMIT 1
    """
    cursor.execute(query, (course_id,))
    course_data = cursor.fetchone()

    if not course_data:
        flash('ไม่พบหลักสูตรที่ระบุ หรือหลักสูตรยังไม่เผยแพร่', 'danger')
        cursor.close()
        return redirect(url_for('course'))

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

    # 2. ดึงบทเรียนทั้งหมดของหลักสูตรนี้ (เหมือนเดิม)
    cursor.execute("""
        SELECT lesson_id, lesson_name, lesson_date
        FROM lesson
        WHERE course_id = %s
        ORDER BY lesson_date ASC
    """, (course_id,))
    lessons_in_course = cursor.fetchall()
    
    # ดึง ID ของบทเรียนแรกสุด
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
        cursor.execute("SELECT * FROM registered_courses WHERE user_id = %s AND course_id = %s", (current_user.id, course_id))
        if cursor.fetchone():
            is_enrolled = True
        
        if is_enrolled and course['pre_test_quiz_id']: # ตรวจสอบว่ามี Pre-test quiz_id
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
    cursor.execute("SELECT lesson_id, lesson_name, course_id FROM lesson WHERE lesson_id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash('ไม่พบบทเรียนที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard')) # หรือกลับไปหน้า course list

    # 2. ตรวจสอบว่าผู้ใช้ลงทะเบียนหลักสูตรนี้แล้วหรือไม่
    # ดึงข้อมูลหลักสูตรของบทเรียนนี้
    cursor.execute("SELECT id, title FROM courses WHERE id = %s", (lesson['course_id'],)) # ✅ ลบ pre_test_quiz_id ออกจาก SELECT
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
    # เพราะการตรวจสอบนี้ควรจะเกิดขึ้นที่หน้า course_detail ก่อนที่จะเข้ามาหน้านี้ได้
    # if course_of_lesson['pre_test_quiz_id']:
    #     cursor.execute("SELECT passed FROM user_quiz_attempts WHERE user_id = %s AND quiz_id = %s ORDER BY attempt_date DESC LIMIT 1",
    #                    (current_user.id, course_of_lesson['pre_test_quiz_id']))
    #     pre_test_result = cursor.fetchone()

    #     if not pre_test_result or not pre_test_result['passed']:
    #         flash('คุณต้องทำแบบทดสอบ Pre-test ของหลักสูตรนี้ให้ผ่านก่อนจึงจะเข้าถึงบทเรียนได้', 'warning')
    #         cursor.close()
    #         return redirect(url_for('course_detail', course_id=course_of_lesson['id']))


    # 4. ดึงเนื้อหา (วิดีโอ/แบบทดสอบ) ที่ผูกกับบทเรียนนี้ (เหมือนเดิม)
    cursor.execute("""
        SELECT video_id, title, youtube_link, description, time_duration, video_image, quiz_id
        FROM quiz_video
        WHERE lesson_id = %s
        ORDER BY video_id ASC
    """, (lesson_id,))
    lesson_contents = cursor.fetchall()

    cursor.close()
    return render_template('course/user_view_lesson.html', 
                           lesson=lesson, 
                           course=course_of_lesson, # ส่งข้อมูลหลักสูตรไปด้วย
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
        return redirect(url_for('course_detail', course_id=course_id)) # ✅ เปลี่ยนไปกลับ course_detail

    # 3. บันทึกการลงทะเบียนหลักสูตร
    try:
        cursor.execute("INSERT INTO registered_courses (user_id, course_id, registered_at) VALUES (%s, %s, %s)",
                       (current_user.id, course_id, datetime.now()))
        mysql.connection.commit()
        flash(f"คุณได้ลงทะเบียนหลักสูตร '{course['title']}' สำเร็จแล้ว!", 'success')
        cursor.close()
        return redirect(url_for('course_detail', course_id=course_id)) # ✅ เปลี่ยนไปกลับ course_detail

    except Exception as e:
        mysql.connection.rollback()
        flash(f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}", 'danger')
        cursor.close()
        return redirect(url_for('course_detail', course_id=course_id))

@app.route('/quiz/start/<int:quiz_id>', methods=['GET'])
@login_required
def start_quiz(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 1. ดึงข้อมูลแบบทดสอบ (Quiz)
    cursor.execute("SELECT quiz_id, quiz_name, lesson_id, passing_percentage FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        flash('ไม่พบแบบทดสอบที่ระบุ', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard')) # หรือกลับไปหน้า course list

    # 2. ดึงคำถามทั้งหมดของแบบทดสอบนี้
    cursor.execute("""
        SELECT 
            question_id, question_name, choice_a, choice_b, choice_c, choice_d,
            question_image, choice_a_image, choice_b_image, choice_c_image, choice_d_image,
            score, correct_answer
        FROM questions 
        WHERE quiz_id = %s
        ORDER BY question_id ASC
    """, (quiz_id,))
    questions = cursor.fetchall()

    if not questions:
        flash('ไม่พบคำถามสำหรับแบบทดสอบนี้', 'warning')
        cursor.close()
        # ถ้าไม่มีคำถาม อาจจะ redirect กลับไปหน้า course_detail หรือ user_dashboard
        return redirect(url_for('course_detail', course_id=quiz['lesson_id'])) # หากต้องการกลับไป course_detail ของบทเรียนนั้น

    cursor.close()
    # ✅ ส่งข้อมูลแบบทดสอบและคำถามทั้งหมดไปยังเทมเพลตใหม่
    return render_template('course/quiz_page.html', quiz=quiz, questions=questions)

@app.route('/quiz/submit/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT quiz_id, quiz_name, passing_percentage, lesson_id FROM quiz WHERE quiz_id = %s", (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        flash('แบบทดสอบไม่ถูกต้อง', 'danger')
        cursor.close()
        return redirect(url_for('user_dashboard'))

    # ✅ กำหนดค่าเริ่มต้นให้กับตัวแปรทั้งหมดตั้งแต่ต้น
    user_score = 0
    total_score_possible = 0
    percentage_score = 0.0
    passed = False
    
    # ดึงคำถามทั้งหมดของแบบทดสอบนี้ (พร้อมคำตอบที่ถูกต้อง)
    cursor.execute("SELECT question_id, correct_answer, score FROM questions WHERE quiz_id = %s", (quiz_id,))
    questions_data = cursor.fetchall()

    if questions_data: # ✅ ตรวจสอบว่ามีคำถามหรือไม่ ก่อนคำนวณ
        total_score_possible = sum(q['score'] for q in questions_data)
        
        for question in questions_data:
            question_id_str = str(question['question_id'])
            user_answer = request.form.get(f'question_{question_id_str}')
            
            if user_answer and user_answer.lower() == question['correct_answer'].lower():
                user_score += question['score']

        percentage_score = (user_score / total_score_possible) * 100 if total_score_possible > 0 else 0
        passed = percentage_score >= quiz['passing_percentage']
    else:
        # ถ้าไม่มีคำถามเลย ให้ถือว่าคะแนนเป็น 0 และไม่ผ่าน
        flash('แบบทดสอบนี้ไม่มีคำถาม', 'warning')
        # ไม่ต้องทำอะไรกับ user_score, passed เพราะค่าเริ่มต้นเป็น 0/False อยู่แล้ว

    # บันทึกผลการทำแบบทดสอบลงในตาราง user_quiz_attempts
    try:
        cursor.execute("""
            INSERT INTO user_quiz_attempts (user_id, quiz_id, score, passed, attempt_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_user.id, quiz_id, user_score, passed, datetime.now()))
        mysql.connection.commit()
        flash(f"คุณทำแบบทดสอบ '{quiz['quiz_name']}' เสร็จสิ้น! คะแนน: {user_score}/{total_score_possible} ({percentage_score:.2f}%)", 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f"เกิดข้อผิดพลาดในการบันทึกผลแบบทดสอบ: {str(e)}", 'danger')
        print(f"ERROR: Database insertion failed in submit_quiz: {e}")
    finally:
        cursor.close()

    redirect_lesson_id = quiz.get('lesson_id')
    if redirect_lesson_id is None:
        print(f"DEBUG: lesson_id for quiz {quiz_id} is None. Redirecting to /course.")
        return redirect(url_for('course'))
    else:
        print(f"DEBUG: Redirecting to course_detail for lesson_id: {redirect_lesson_id}.")
        return redirect(url_for('course_detail', course_id=redirect_lesson_id))

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
    form = QuizForm() # สร้างฟอร์มตั้งแต่ต้น

    # ✅ กำหนด choices สำหรับ select_quiz_id เสมอ
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


    # === Logic สำหรับหน้าเลือกแบบทดสอบ (ถ้า quiz_id เป็น 0 หรือไม่ได้ระบุ) ===
    if quiz_id == 0:
        if request.method == 'POST':
            selected_quiz_id = request.form.get('select_quiz_id')
            if selected_quiz_id and int(selected_quiz_id) != 0:
                return redirect(url_for('edit_quiz', quiz_id=selected_quiz_id))
            else:
                flash('กรุณาเลือกแบบทดสอบที่ต้องการแก้ไข', 'danger')
        
        cursor.close()
        return render_template('admin/edit_quiz.html', form=form, selection_mode=True)


    # === Logic สำหรับหน้าแก้ไขแบบทดสอบจริง (เมื่อ quiz_id ถูกส่งมา) ===
    
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

            if lesson_id_from_quiz is None:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('quiz_and_video', lesson_id=lesson_id_from_quiz))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึก: {str(e)}', 'danger')
            cursor.close()
            return render_template('admin/edit_quiz.html', quiz=quiz_data, questions=questions, lesson=lesson_obj_for_template, form=form, selection_mode=False)
    
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