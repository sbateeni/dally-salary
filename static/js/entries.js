function renderEntries(list) {
    // تحديث جدول السجل الكامل
    tableBody.innerHTML = '';
    
    // تحديث جدول سجل اليوم
    const todayTableBody = document.querySelector('#todayEntriesTable tbody');
    todayTableBody.innerHTML = '';
    
    const today = getTodayDate();
    
    list.forEach(e => {
        const row = document.createElement('tr');
        const isToday = e.date === today;
        
        // إنشاء صف مشترك
        const commonColumns = `
            <td>${e.start_time}</td>
            <td>${e.end_time}</td>
            <td>${e.total_hours ? e.total_hours.toFixed(2) : '0.00'}</td>
            <td>${e.pay ? e.pay.toFixed(2) : '0.00'} ₪</td>
            <td>${e.note || ''}</td>
            <td>
                <i class="fas fa-edit action-icon edit-icon" title="تعديل" onclick="editEntry('${e.date}')"></i>
                <i class="fas fa-trash-alt action-icon delete-icon" title="حذف" onclick="showDeleteModal('${e.date}')"></i>
            </td>
        `;

        // إضافة السجل إلى جدول اليوم إذا كان اليوم الحالي
        if (isToday) {
            const todayRow = document.createElement('tr');
            todayRow.innerHTML = commonColumns;
            todayTableBody.appendChild(todayRow);
        }

        // إضافة السجل إلى السجل الكامل
        row.innerHTML = `
            <td>${e.date}</td>
            <td>${e.day}</td>
            ${commonColumns}
        `;
        tableBody.appendChild(row);
    });
}

// إضافة دالة لتنسيق الوقت بنظام 24 ساعة
function formatTime(time) {
    if (!time) return '';
    return time;
}

function updateSummary() {
    const totalSalary = entries.reduce((sum, e) => sum + (e.pay || 0), 0);
    totalSalarySummary.textContent = `مجموع الراتب: ${totalSalary.toFixed(2)} ₪`;
}

function searchEntries() {
    const date = document.getElementById('searchDate').value;
    fetch(`/api/entries/search/${date}`)
        .then(response => response.json())
        .then(filtered => {
            if (filtered.length === 0) {
                showToast("لا توجد نتائج.", 'error');
                return;
            }
            renderEntries(filtered);
            showToast('تم عرض النتائج بنجاح');
        });
}

function editEntry(date) {
    const entry = entries.find(e => e.date === date);
    if (!entry) {
        showToast('لم يتم العثور على السجل', 'error');
        return;
    }

    // تحديث حقول النموذج بالقيم الحالية
    const [startHour, startMinute] = entry.start_time.split(':');
    const [endHour, endMinute] = entry.end_time.split(':');
    
    document.getElementById('startHour').value = startHour;
    document.getElementById('startMinute').value = startMinute;
    document.getElementById('endHour').value = endHour;
    document.getElementById('endMinute').value = endMinute;
    document.getElementById('notes').value = entry.note;

    // تعطيل زر الإضافة مؤقتاً
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = 'جاري التحديث...';

    // إرسال طلب التحديث
    fetch(`/api/entries/${entry.id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify(entry)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        
        // تحديث القائمة المحلية
        const index = entries.findIndex(e => e.id === entry.id);
        if (index !== -1) {
            entries[index] = entry;
        }
        
        renderEntries(entries);
        updateSummary();
        form.reset();
        showToast('تم التحديث بنجاح');
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('حدث خطأ أثناء التحديث', 'error');
    })
    .finally(() => {
        // إعادة تفعيل زر الإضافة
        submitButton.disabled = false;
        submitButton.textContent = 'إضافة';
    });
} 