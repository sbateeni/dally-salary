from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///work_hours.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Constants
HOURLY_RATE = 14
OVERTIME_MULTIPLIER = 1.5

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    entries = db.relationship('WorkEntry', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class WorkEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    day = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    total_hours = db.Column(db.Float, nullable=False)
    overtime_hours = db.Column(db.Float, nullable=False)
    pay = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/entries', methods=['GET'])
@login_required
def get_entries():
    entries = WorkEntry.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'date': entry.date.strftime('%Y-%m-%d'),
        'day': entry.day,
        'start': entry.start_time.strftime('%H:%M'),
        'end': entry.end_time.strftime('%H:%M'),
        'totalHours': entry.total_hours,
        'overtimeHours': entry.overtime_hours,
        'pay': entry.pay,
        'note': entry.note
    } for entry in entries])

@app.route('/api/entries', methods=['POST'])
@login_required
def add_entry():
    data = request.json
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    
    # Check if entry exists for this date
    existing_entry = WorkEntry.query.filter_by(
        user_id=current_user.id,
        date=date
    ).first()
    
    if existing_entry:
        return jsonify({'error': 'Date already exists'}), 400
    
    start_time = datetime.strptime(data['start'], '%H:%M').time()
    end_time = datetime.strptime(data['end'], '%H:%M').time()
    
    entry = WorkEntry(
        date=date,
        day=data['day'],
        start_time=start_time,
        end_time=end_time,
        total_hours=data['totalHours'],
        overtime_hours=data['overtimeHours'],
        pay=data['pay'],
        note=data['note'],
        user_id=current_user.id
    )
    
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({'message': 'Entry added successfully'})

@app.route('/api/entries/<date>', methods=['DELETE'])
@login_required
def delete_entry(date):
    entry = WorkEntry.query.filter_by(
        user_id=current_user.id,
        date=datetime.strptime(date, '%Y-%m-%d').date()
    ).first()
    
    if entry:
        db.session.delete(entry)
        db.session.commit()
        return jsonify({'message': 'Entry deleted successfully'})
    return jsonify({'error': 'Entry not found'}), 404

@app.route('/api/entries/search/<date>', methods=['GET'])
@login_required
def search_entries(date):
    entries = WorkEntry.query.filter_by(
        user_id=current_user.id,
        date=datetime.strptime(date, '%Y-%m-%d').date()
    ).all()
    
    return jsonify([{
        'date': entry.date.strftime('%Y-%m-%d'),
        'day': entry.day,
        'start': entry.start_time.strftime('%H:%M'),
        'end': entry.end_time.strftime('%H:%M'),
        'totalHours': entry.total_hours,
        'overtimeHours': entry.overtime_hours,
        'pay': entry.pay,
        'note': entry.note
    } for entry in entries])

@app.route('/api/export', methods=['GET'])
@login_required
def export_csv():
    entries = WorkEntry.query.filter_by(user_id=current_user.id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['التاريخ', 'اليوم', 'وقت البدء', 'وقت الانتهاء', 'عدد الساعات', 
                    'الساعات الإضافية', 'قيمة الساعة الإضافية', 'الدفع الكلي', 
                    'مجموع الراتب', 'ملاحظات'])
    
    for entry in entries:
        writer.writerow([
            entry.date.strftime('%Y-%m-%d'),
            entry.day,
            entry.start_time.strftime('%H:%M'),
            entry.end_time.strftime('%H:%M'),
            f"{entry.total_hours:.2f}",
            f"{entry.overtime_hours:.2f}",
            f"{(HOURLY_RATE * OVERTIME_MULTIPLIER):.2f}",
            f"{entry.pay:.2f}",
            f"{entry.pay:.2f}",
            entry.note
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='ساعات_العمل.csv'
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود مسبقاً')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('تم إنشاء الحساب بنجاح')
        return redirect(url_for('login'))
    return render_template('register.html')

# Create tables
with app.app_context():
    db.create_all()
    
    # Create default admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True) 