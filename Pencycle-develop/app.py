from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import qrcode
import io

app = Flask(__name__)

# ---------------- Database ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pencyle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- Models ----------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    class_name = db.Column(db.String(50))
    points = db.Column(db.Integer, default=0)

class PenCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.Integer, db.ForeignKey('student.id'))
    used_on = db.Column(db.DateTime)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    pen_code = db.Column(db.String(50))
    bin_id = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------- Routes ----------------

# Home Page
@app.route('/')
def home():
    return "<h2>Pencyle Backend Running 🚀</h2>"


# ✅ Add Pen Codes
@app.route("/addcodes")
def addcodes():
    codes = ["PEN001", "PEN002", "PEN003", "PEN004", "PEN005","PEN006", "PEN007", "PEN008", "PEN009", "PEN010"]

    for c in codes:
        existing = PenCode.query.filter_by(code=c).first()
        if not existing:
            db.session.add(PenCode(code=c))

    db.session.commit()
    return "✅ Pen codes added successfully!"


# ✅ QR Code Generator
@app.route("/generate_qr/<bin_id>")
def generate_qr(bin_id):

    # URL opened after scanning QR
    url = f"http://172.16.11.27:5000/recycle/{bin_id}"

    qr = qrcode.make(url)

    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


# ✅ Recycle Page
@app.route('/recycle/<bin_id>', methods=['GET', 'POST'])
def recycle(bin_id):

    message = ""

    if request.method == 'POST':
        name = request.form['name']
        class_name = request.form['class']
        pen_code = request.form['pen_code']

        # Find or create student
        student = Student.query.filter_by(
            name=name,
            class_name=class_name
        ).first()

        if not student:
            student = Student(name=name, class_name=class_name)
            db.session.add(student)
            db.session.commit()

        # Validate pen code
        pen = PenCode.query.filter_by(code=pen_code).first()

        if not pen:
            message = "⚠️ Invalid pen code!"
        elif pen.used:
            message = "❌ Pen already recycled!"
        else:
            pen.used = True
            pen.used_by = student.id
            pen.used_on = datetime.now()
            student.points += 10

            db.session.add(
                Submission(
                    student_id=student.id,
                    pen_code=pen_code,
                    bin_id=bin_id
                )
            )

            db.session.commit()
            message = f"✅ +10 points for {student.name}"

    return render_template(
        "recycle.html",
        bin_id=bin_id,
        message=message
    )


# ---------------- Run App ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5000)