from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
import os
import uuid
from werkzeug.utils import secure_filename
from reportlab.lib.utils import ImageReader
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "change-this-secret-before-real-use"
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024
DATABASE = 'school.db'
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_student_photo(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        flash("Photo not uploaded. Choose a JPG, JPEG, PNG, or WEBP image.", "error")
        return None
    extension = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    filename = uuid.uuid4().hex + "." + extension
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return "uploads/" + filename


@app.errorhandler(413)
def file_too_large(error):
    flash("That photo is too large. Please choose an image under 3 MB.", "error")
    return redirect(request.referrer or url_for("students_page"))


def connect_database():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def create_database():
    db = connect_database()
    db.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        father_name TEXT, student_class TEXT, roll_number TEXT,
        date_of_birth TEXT, address TEXT, admission_date TEXT)''')
    columns = [row["name"] for row in db.execute("PRAGMA table_info(students)").fetchall()]
    if "photo" not in columns:
        db.execute("ALTER TABLE students ADD COLUMN photo TEXT")
    db.execute('''CREATE TABLE IF NOT EXISTS school (
        id INTEGER PRIMARY KEY CHECK(id=1), name TEXT, address TEXT,
        phone TEXT, email TEXT, principal TEXT, logo TEXT, classes TEXT)''')
    school_columns = [row["name"] for row in db.execute("PRAGMA table_info(school)").fetchall()]
    if "logo" not in school_columns:
        db.execute("ALTER TABLE school ADD COLUMN logo TEXT")
    if "classes" not in school_columns:
        db.execute("ALTER TABLE school ADD COLUMN classes TEXT DEFAULT '8,9,10'")
    db.execute("INSERT OR IGNORE INTO school (id, name, address, phone, email, principal, logo, classes) VALUES (1, 'Your School Name', 'School Address', '', '', '', NULL, '8,9,10')")
    db.execute("UPDATE school SET classes='8,9,10' WHERE classes IS NULL OR TRIM(classes)=''")
    db.commit()
    db.close()


def get_school():
    db = connect_database()
    school = db.execute('SELECT * FROM school WHERE id=1').fetchone()
    db.close()
    return school


def get_classes():
    school = get_school()
    raw = school['classes'] if school and 'classes' in school.keys() else '8,9,10'
    return [item.strip() for item in (raw or '8,9,10').split(',') if item.strip()]


@app.route('/')
def home():
    db = connect_database()
    students = db.execute('SELECT * FROM students ORDER BY id DESC LIMIT 5').fetchall()
    total = db.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    db.close()
    return render_template('index.html', students=students, total_students=total, school=get_school())


@app.route('/students')
def students_page():
    db = connect_database()
    students = db.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    db.close()
    return render_template('students.html', students=students, school=get_school())


@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            photo = save_student_photo(request.files.get("photo"))
            db = connect_database()
            db.execute('''INSERT INTO students
                (name, father_name, student_class, roll_number, date_of_birth, address, admission_date, photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                name, request.form.get('father_name', '').strip(), request.form.get('student_class', ''),
                request.form.get('roll_number', '').strip(), request.form.get('date_of_birth', ''),
                request.form.get('address', '').strip(), request.form.get('admission_date', ''), photo))
            db.commit()
            db.close()
        return redirect(url_for('students_page'))
    return render_template('add_student.html', school=get_school(), student=None, classes=get_classes())


@app.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    db = connect_database()
    student = db.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchone()
    if student is None:
        db.close()
        return redirect(url_for('students_page'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            new_photo = save_student_photo(request.files.get("photo"))
            photo = new_photo or student["photo"]
            db.execute('''UPDATE students SET name=?, father_name=?, student_class=?, roll_number=?,
                date_of_birth=?, address=?, admission_date=?, photo=? WHERE id=?''', (
                name, request.form.get('father_name', '').strip(), request.form.get('student_class', ''),
                request.form.get('roll_number', '').strip(), request.form.get('date_of_birth', ''),
                request.form.get('address', '').strip(), request.form.get('admission_date', ''), photo, student_id))
            db.commit()
        db.close()
        return redirect(url_for('students_page'))
    db.close()
    return render_template('add_student.html', school=get_school(), student=student, classes=get_classes())


@app.route('/delete-student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    db = connect_database()
    student = db.execute("SELECT photo FROM students WHERE id=?", (student_id,)).fetchone()
    if student and student["photo"]:
        photo_path = os.path.join("static", student["photo"])
        if os.path.isfile(photo_path):
            os.remove(photo_path)
    db.execute('DELETE FROM students WHERE id=?', (student_id,))
    db.commit()
    db.close()
    return redirect(url_for('students_page'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        db = connect_database()
        school = db.execute('SELECT * FROM school WHERE id=1').fetchone()
        logo = school['logo']
        uploaded_logo = request.files.get('logo')
        if uploaded_logo and uploaded_logo.filename:
            if allowed_file(uploaded_logo.filename):
                ext = secure_filename(uploaded_logo.filename).rsplit('.', 1)[1].lower()
                logo_name = 'school_logo_' + uuid.uuid4().hex + '.' + ext
                uploaded_logo.save(os.path.join(UPLOAD_FOLDER, logo_name))
                if logo:
                    old_path = os.path.join('static', logo)
                    if os.path.isfile(old_path):
                        try: os.remove(old_path)
                        except OSError: pass
                logo = 'uploads/' + logo_name
            else:
                flash('Logo not updated. Choose a JPG, JPEG, PNG, or WEBP image.', 'error')
        classes = request.form.get('classes', '8,9,10').strip() or '8,9,10'
        classes = ','.join(dict.fromkeys(c.strip() for c in classes.split(',') if c.strip())) or '8,9,10'
        db.execute('UPDATE school SET name=?, address=?, phone=?, email=?, principal=?, logo=?, classes=? WHERE id=1', (
            request.form.get('name', '').strip(), request.form.get('address', '').strip(),
            request.form.get('phone', '').strip(), request.form.get('email', '').strip(),
            request.form.get('principal', '').strip(), logo, classes))
        db.commit()
        db.close()
        return redirect(url_for('settings'))
    return render_template('settings.html', school=get_school())


@app.route('/id-card/<int:student_id>')
def id_card(student_id):
    db = connect_database()
    student = db.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchone()
    db.close()
    if student is None:
        return redirect(url_for('students_page'))
    return render_template('id_card.html', student=student, school=get_school())


@app.route('/id-card-pdf/<int:student_id>')
def id_card_pdf(student_id):
    db = connect_database()
    student = db.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchone()
    db.close()
    if student is None:
        return redirect(url_for('students_page'))
    school = get_school()
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=landscape((340, 215)))
    pdf.setFillColorRGB(.08, .16, .28)
    pdf.rect(0, 165, 340, 50, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    if school['logo']:
        logo_path = os.path.join('static', school['logo'])
        if os.path.isfile(logo_path):
            try: pdf.drawImage(ImageReader(logo_path), 8, 173, width=30, height=30, preserveAspectRatio=True, anchor='c', mask='auto')
            except Exception: pass
    pdf.setFont('Helvetica-Bold', 13)
    pdf.drawString(43 if school['logo'] else 15, 190, (school['name'] or 'Your School Name')[:34])
    pdf.setFont('Helvetica', 8)
    pdf.drawString(15, 176, (school['address'] or '')[:60])
    pdf.setFillColorRGB(.1, .2, .35)
    pdf.setFont('Helvetica-Bold', 11)
    pdf.drawString(15, 145, 'STUDENT ID CARD')
    pdf.setFont('Helvetica', 9)
    pdf.drawString(15, 125, 'Student ID: STU-%04d' % student['id'])
    pdf.drawString(15, 108, 'Name: ' + (student['name'] or '')[:38])
    pdf.drawString(15, 91, 'Class: ' + (student['student_class'] or ''))
    pdf.drawString(15, 74, 'Roll No: ' + (student['roll_number'] or ''))
    pdf.drawString(15, 57, 'Date of Birth: ' + (student['date_of_birth'] or ''))
    if student["photo"]:
        photo_path = os.path.join("static", student["photo"])
        if os.path.isfile(photo_path):
            try:
                pdf.drawImage(ImageReader(photo_path), 270, 48, width=53, height=76,
                              preserveAspectRatio=True, anchor="c", mask="auto")
            except Exception:
                pass
    pdf.roundRect(5, 5, 330, 205, 8, stroke=1, fill=0)
    pdf.save()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='student_id_card_%s.pdf' % student['id'], mimetype='application/pdf')


@app.route('/transfer-certificate/<int:student_id>')
def transfer_certificate(student_id):
    db = connect_database()
    student = db.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchone()
    db.close()
    if student is None:
        return redirect(url_for('students_page'))
    return render_template('tc_form.html', student=student, school=get_school())


@app.route('/transfer-certificate-pdf/<int:student_id>', methods=['POST'])
def transfer_certificate_pdf(student_id):
    db = connect_database()
    student = db.execute('SELECT * FROM students WHERE id=?', (student_id,)).fetchone()
    db.close()
    if student is None:
        return redirect(url_for('students_page'))
    school = get_school()
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    pdf.setStrokeColorRGB(.1, .2, .35)
    pdf.setLineWidth(2)
    pdf.rect(35, 35, width - 70, height - 70)
    if school['logo']:
        logo_path = os.path.join('static', school['logo'])
        if os.path.isfile(logo_path):
            try: pdf.drawImage(ImageReader(logo_path), 52, height - 105, width=42, height=42, preserveAspectRatio=True, anchor='c', mask='auto')
            except Exception: pass
    pdf.setFont('Helvetica-Bold', 17)
    pdf.drawCentredString(width / 2, height - 80, (school['name'] or 'Your School Name')[:60])
    pdf.setFont('Helvetica', 9)
    pdf.drawCentredString(width / 2, height - 100, (school['address'] or '')[:90])
    pdf.setFont('Helvetica-Bold', 15)
    pdf.drawCentredString(width / 2, height - 145, 'TRANSFER CERTIFICATE')
    pdf.setFont('Helvetica', 10)
    pdf.drawString(60, height - 185, 'Certificate No.: TC-%04d' % student['id'])
    pdf.drawString(60, height - 205, 'Student ID: STU-%04d' % student['id'])
    details = [
        'Student name: ' + (student['name'] or ''),
        "Father's / Guardian's name: " + (student['father_name'] or ''),
        'Class: ' + (student['student_class'] or ''),
        'Roll number: ' + (student['roll_number'] or ''),
        'Date of birth: ' + (student['date_of_birth'] or ''),
        'Address: ' + (student['address'] or ''),
        'Conduct: ' + request.form.get('conduct', 'Good'),
        'Reason for leaving: ' + request.form.get('reason', ''),
        'Last date of attendance: ' + request.form.get('last_date', ''),
        'Remarks: ' + request.form.get('remarks', '')]
    y = height - 250
    for line in details:
        pdf.drawString(60, y, line[:100])
        y -= 27
    pdf.drawString(60, 125, 'Date of Issue: ____________________')
    pdf.drawString(60, 90, "Principal's Signature: ____________________")
    pdf.save()
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='transfer_certificate_%s.pdf' % student['id'], mimetype='application/pdf')


if __name__ == '__main__':
    create_database()
    app.run(debug=True)
