import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import arabic_reshaper
from bidi.algorithm import get_display
import json
import os

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام تسجيل ساعات العمل",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# الثوابت
HOURLY_RATE = 14
OVERTIME_MULTIPLIER = 1.5
DAYS = {
    0: "الأحد",
    1: "الإثنين",
    2: "الثلاثاء",
    3: "الأربعاء",
    4: "الخميس",
    5: "الجمعة",
    6: "السبت"
}

# دالة لتنسيق النصوص العربية
def format_arabic(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

# دالة لحساب الساعات
def calculate_hours(start_hour, start_minute, end_hour, end_minute):
    start_total_minutes = start_hour * 60 + start_minute
    end_total_minutes = end_hour * 60 + end_minute
    
    if end_total_minutes < start_total_minutes:
        total_hours = (24 * 60 - start_total_minutes + end_total_minutes) / 60
    else:
        total_hours = (end_total_minutes - start_total_minutes) / 60
        
    return total_hours

# دالة لحساب الراتب
def calculate_pay(total_hours):
    overtime_hours = max(0, total_hours - 8)
    overtime_rate = HOURLY_RATE * OVERTIME_MULTIPLIER
    pay = (min(total_hours, 8) * HOURLY_RATE) + (overtime_hours * overtime_rate)
    return pay, overtime_hours

# دالة لتحميل البيانات من قاعدة البيانات
def load_data():
    try:
        conn = sqlite3.connect('work_hours.db')
        df = pd.read_sql_query("SELECT * FROM entries", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {str(e)}")
        return pd.DataFrame()

# دالة لحفظ البيانات في قاعدة البيانات
def save_entry(date, day, start, end, total_hours, overtime_hours, pay, note):
    try:
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entries (date, day, start, end, total_hours, overtime_hours, pay, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (date, day, start, end, total_hours, overtime_hours, pay, note))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"خطأ في حفظ البيانات: {str(e)}")
        return False

# دالة لحذف سجل
def delete_entry(date):
    try:
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entries WHERE date = ?", (date,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"خطأ في حذف السجل: {str(e)}")
        return False

# دالة لتحديث سجل
def update_entry(date, day, start, end, total_hours, overtime_hours, pay, note):
    try:
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entries 
            SET day = ?, start = ?, end = ?, total_hours = ?, overtime_hours = ?, pay = ?, note = ?
            WHERE date = ?
        """, (day, start, end, total_hours, overtime_hours, pay, note, date))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"خطأ في تحديث السجل: {str(e)}")
        return False

# إنشاء قاعدة البيانات إذا لم تكن موجودة
def init_db():
    try:
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                date TEXT PRIMARY KEY,
                day TEXT,
                start TEXT,
                end TEXT,
                total_hours REAL,
                overtime_hours REAL,
                pay REAL,
                note TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {str(e)}")

# تهيئة قاعدة البيانات
init_db()

# العنوان الرئيسي
st.title(format_arabic("نظام تسجيل ساعات العمل"))

# القائمة الجانبية
with st.sidebar:
    st.header(format_arabic("إضافة ساعات عمل جديدة"))
    
    # نموذج إضافة ساعات العمل
    work_date = st.date_input(format_arabic("التاريخ"), datetime.now())
    col1, col2 = st.columns(2)
    
    with col1:
        start_hour = st.selectbox(format_arabic("ساعة البدء"), range(24), format_func=lambda x: f"{x:02d}")
        start_minute = st.selectbox(format_arabic("دقيقة البدء"), range(0, 60, 5), format_func=lambda x: f"{x:02d}")
    
    with col2:
        end_hour = st.selectbox(format_arabic("ساعة الانتهاء"), range(24), format_func=lambda x: f"{x:02d}")
        end_minute = st.selectbox(format_arabic("دقيقة الانتهاء"), range(0, 60, 5), format_func=lambda x: f"{x:02d}")
    
    note = st.text_input(format_arabic("ملاحظات"))
    
    if st.button(format_arabic("إضافة")):
        # حساب الساعات والراتب
        total_hours = calculate_hours(start_hour, start_minute, end_hour, end_minute)
        pay, overtime_hours = calculate_pay(total_hours)
        
        # الحصول على اسم اليوم
        day_name = DAYS[work_date.weekday()]
        
        # تنسيق الأوقات
        start_time = f"{start_hour:02d}:{start_minute:02d}"
        end_time = f"{end_hour:02d}:{end_minute:02d}"
        
        # حفظ البيانات
        if save_entry(
            work_date.strftime('%Y-%m-%d'),
            day_name,
            start_time,
            end_time,
            total_hours,
            overtime_hours,
            pay,
            note
        ):
            st.success(format_arabic("تمت إضافة الساعات بنجاح"))
            st.experimental_rerun()

# عرض البيانات
df = load_data()

if not df.empty:
    # تحويل البيانات
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    # عرض ملخص
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_hours = df['total_hours'].sum()
        st.metric(format_arabic("إجمالي الساعات"), f"{total_hours:.2f}")
    
    with col2:
        overtime_hours = df['overtime_hours'].sum()
        st.metric(format_arabic("الساعات الإضافية"), f"{overtime_hours:.2f}")
    
    with col3:
        total_pay = df['pay'].sum()
        st.metric(format_arabic("إجمالي الراتب"), f"{total_pay:.2f} ₪")
    
    # رسم بياني للساعات
    fig = px.line(df, x='date', y='total_hours', 
                  title=format_arabic("الساعات اليومية"),
                  labels={'date': format_arabic("التاريخ"), 
                         'total_hours': format_arabic("عدد الساعات")})
    st.plotly_chart(fig, use_container_width=True)
    
    # رسم بياني للرواتب
    fig2 = px.bar(df, x='date', y='pay',
                  title=format_arabic("الرواتب اليومية"),
                  labels={'date': format_arabic("التاريخ"),
                         'pay': format_arabic("الراتب")})
    st.plotly_chart(fig2, use_container_width=True)
    
    # عرض الجدول
    st.subheader(format_arabic("سجل الساعات"))
    
    # إضافة أزرار التعديل والحذف
    for idx, row in df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"{row['date'].strftime('%Y-%m-%d')} - {row['day']}")
            st.write(f"{format_arabic('وقت البدء')}: {row['start']} | {format_arabic('وقت الانتهاء')}: {row['end']}")
            st.write(f"{format_arabic('عدد الساعات')}: {row['total_hours']:.2f} | {format_arabic('الساعات الإضافية')}: {row['overtime_hours']:.2f}")
            st.write(f"{format_arabic('الراتب')}: {row['pay']:.2f} ₪")
            if row['note']:
                st.write(f"{format_arabic('ملاحظات')}: {row['note']}")
        
        with col2:
            if st.button(format_arabic("تعديل"), key=f"edit_{idx}"):
                st.session_state['editing'] = row['date'].strftime('%Y-%m-%d')
        
        with col3:
            if st.button(format_arabic("حذف"), key=f"delete_{idx}"):
                if delete_entry(row['date'].strftime('%Y-%m-%d')):
                    st.experimental_rerun()
        
        st.divider()

# نموذج التعديل
if 'editing' in st.session_state:
    st.subheader(format_arabic("تعديل السجل"))
    entry = df[df['date'] == st.session_state['editing']].iloc[0]
    
    edit_date = st.date_input(format_arabic("التاريخ"), entry['date'])
    col1, col2 = st.columns(2)
    
    with col1:
        start_hour, start_minute = map(int, entry['start'].split(':'))
        edit_start_hour = st.selectbox(format_arabic("ساعة البدء"), range(24), start_hour)
        edit_start_minute = st.selectbox(format_arabic("دقيقة البدء"), range(0, 60, 5), start_minute)
    
    with col2:
        end_hour, end_minute = map(int, entry['end'].split(':'))
        edit_end_hour = st.selectbox(format_arabic("ساعة الانتهاء"), range(24), end_hour)
        edit_end_minute = st.selectbox(format_arabic("دقيقة الانتهاء"), range(0, 60, 5), end_minute)
    
    edit_note = st.text_input(format_arabic("ملاحظات"), entry['note'])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(format_arabic("حفظ التعديلات")):
            # حساب الساعات والراتب
            total_hours = calculate_hours(edit_start_hour, edit_start_minute, edit_end_hour, edit_end_minute)
            pay, overtime_hours = calculate_pay(total_hours)
            
            # الحصول على اسم اليوم
            day_name = DAYS[edit_date.weekday()]
            
            # تنسيق الأوقات
            start_time = f"{edit_start_hour:02d}:{edit_start_minute:02d}"
            end_time = f"{edit_end_hour:02d}:{edit_end_minute:02d}"
            
            # تحديث البيانات
            if update_entry(
                edit_date.strftime('%Y-%m-%d'),
                day_name,
                start_time,
                end_time,
                total_hours,
                overtime_hours,
                pay,
                edit_note
            ):
                del st.session_state['editing']
                st.experimental_rerun()
    
    with col2:
        if st.button(format_arabic("إلغاء")):
            del st.session_state['editing']
            st.experimental_rerun()

# إضافة زر لتصدير البيانات
if not df.empty:
    if st.button(format_arabic("تصدير البيانات")):
        csv = df.to_csv(index=False)
        st.download_button(
            label=format_arabic("تحميل ملف CSV"),
            data=csv,
            file_name=f"work_hours_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        ) 