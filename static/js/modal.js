let deleteEntryDate = null;

function showDeleteModal(date) {
    deleteEntryDate = date;
    document.getElementById('deleteModal').classList.add('show');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('show');
    deleteEntryDate = null;
}

function confirmDelete() {
    if (!deleteEntryDate) return;
    
    const deleteButton = document.querySelector('.confirm-button');
    deleteButton.disabled = true;
    deleteButton.textContent = 'جاري الحذف...';
    
    fetch(`/api/entries/${deleteEntryDate}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        
        entries = entries.filter(e => e.date !== deleteEntryDate);
        renderEntries(entries);
        updateSummary();
        showToast('تم الحذف بنجاح');
        closeDeleteModal();
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('حدث خطأ أثناء الحذف', 'error');
    })
    .finally(() => {
        deleteButton.disabled = false;
        deleteButton.textContent = 'نعم، احذف';
    });
} 