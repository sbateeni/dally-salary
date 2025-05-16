from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///work_hours.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY', 'your-csrf-secret-key-here')

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# تعريف معدل الساعة
HOURLY_RATE = 14

class WorkEntry(db.Model):
    __tablename__ = 'work_entry'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    day = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    total_hours = db.Column(db.Float, nullable=False)
    pay = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    overtime_hours = db.Column(db.Float, default=0)

    def calculate_pay(self):
        return self.total_hours * HOURLY_RATE

    def __repr__(self):
        return f'<WorkEntry {self.date} {self.start_time}-{self.end_time}>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    entries = WorkEntry.query.order_by(WorkEntry.date.desc()).all()
    return jsonify([{
        'id': entry.id,
        'date': entry.date.strftime('%Y-%m-%d'),
        'day': entry.day,
        'start_time': entry.start_time.strftime('%H:%M'),
        'end_time': entry.end_time.strftime('%H:%M'),
        'total_hours': entry.total_hours,
        'pay': entry.pay,
        'note': entry.note
    } for entry in entries])

@app.route('/api/entries', methods=['POST'])
def add_entry():
    try:
        data = request.get_json()
        
        # تحويل النصوص إلى كائنات datetime
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start'], '%H:%M').time()
        end_time = datetime.strptime(data['end'], '%H:%M').time()
        
        # إنشاء سجل جديد
        entry = WorkEntry(
            date=date,
            day=data['day'],
            start_time=start_time,
            end_time=end_time,
            total_hours=float(data['totalHours']),
            pay=float(data['pay']),
            note=data.get('note', '')
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'id': entry.id,
            'date': entry.date.strftime('%Y-%m-%d'),
            'day': entry.day,
            'start_time': entry.start_time.strftime('%H:%M'),
            'end_time': entry.end_time.strftime('%H:%M'),
            'total_hours': entry.total_hours,
            'pay': entry.pay,
            'note': entry.note
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    try:
        entry = WorkEntry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        return jsonify({'message': 'تم الحذف بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 