const HOURLY_RATE = 14;  // قيمة الساعة الواحدة
let entries = [];
const form = document.getElementById('workForm');
const tableBody = document.querySelector('#entriesTable tbody');
const totalSalarySummary = document.getElementById('totalSalarySummary');

// دالة لتحديث وقت الانتهاء تلقائياً
function updateEndTime() {
    const startHour = parseInt(document.getElementById('startHour').value) || 0;
    const startMinute = parseInt(document.getElementById('startMinute').value) || 0;
    
    // حساب وقت الانتهاء (8 ساعات بعد وقت البدء)
    let endHour = startHour + 8;
    let endMinute = startMinute;
    
    // تصحيح الساعات إذا تجاوزت 24
    if (endHour >= 24) {
        endHour = endHour - 24;
    }
    
    // تعبئة حقول وقت الانتهاء
    document.getElementById('endHour').value = endHour.toString().padStart(2, '0');
    document.getElementById('endMinute').value = endMinute.toString().padStart(2, '0');
}

// دالة لتعبئة الوقت الحالي
function setCurrentTime() {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = Math.floor(now.getMinutes() / 5) * 5; // تقريب الدقائق لأقرب 5
    
    // تعبئة وقت البدء بالوقت الحالي
    document.getElementById('startHour').value = currentHour.toString().padStart(2, '0');
    document.getElementById('startMinute').value = currentMinute.toString().padStart(2, '0');
    
    // تحديث وقت الانتهاء تلقائياً
    updateEndTime();
}

// تعبئة الوقت الحالي عند تحميل الصفحة
window.addEventListener('load', () => {
    setCurrentTime();
    // تعبئة التاريخ الحالي
    document.getElementById('workDate').value = getTodayDate();
});

// تحديث وقت الانتهاء عند تغيير وقت البدء
document.getElementById('startHour').addEventListener('change', updateEndTime);
document.getElementById('startMinute').addEventListener('change', updateEndTime);

// Add CSRF token to all fetch requests
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Load entries when page loads
fetch('/api/entries', {
    headers: {
        'X-CSRFToken': getCSRFToken()
    }
})
    .then(response => response.json())
    .then(data => {
        entries = data;
        renderEntries(entries);
        updateSummary();
    });

const getTodayDate = () => {
    const today = new Date();
    return today.toISOString().split("T")[0];
};

const getDayName = () => {
    const days = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"];
    return days[new Date().getDay()];
};

// Add toast notification function
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

// Update form submission to use toast
form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // الحصول على قيم النموذج
    const date = document.getElementById('workDate').value;
    const day = getDayName();
    const start = document.getElementById('startHour').value + ':' + document.getElementById('startMinute').value;
    const end = document.getElementById('endHour').value + ':' + document.getElementById('endMinute').value;
    const note = document.getElementById('notes').value;
    
    // التحقق من صحة البيانات
    if (!date || !day || !start || !end) {
        showToast('يرجى ملء جميع الحقول المطلوبة', 'error');
        return;
    }
    
    // حساب الساعات والراتب
    const startTime = new Date(`2000-01-01T${start}`);
    const endTime = new Date(`2000-01-01T${end}`);
    const totalHours = (endTime - startTime) / (1000 * 60 * 60);
    const pay = totalHours * HOURLY_RATE;
    
    // التحقق من صحة الساعات
    if (totalHours <= 0) {
        showToast('وقت الانتهاء يجب أن يكون بعد وقت البدء', 'error');
        return;
    }
    
    // إرسال البيانات
    fetch('/api/entries', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            date,
            day,
            start,
            end,
            totalHours: totalHours.toFixed(2),
            pay: pay.toFixed(2),
            note
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'حدث خطأ أثناء الإضافة');
            });
        }
        return response.json();
    })
    .then(data => {
        showToast('تمت الإضافة بنجاح');
        document.getElementById('workForm').reset();
        loadEntries();
    })
    .catch(error => {
        console.error('Error:', error);
        showToast(error.message || 'حدث خطأ أثناء الإضافة', 'error');
    });
});

// Function to load entries from the server
function loadEntries() {
    fetch('/api/entries', {
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        entries = data;
        renderEntries(entries);
        updateSummary();
    })
    .catch(error => {
        console.error('Error loading entries:', error);
    });
} 