// Search student records while typing in the search box.
const searchBox = document.getElementById('studentSearch');

if (searchBox) {
    searchBox.addEventListener('input', function () {
        const searchText = searchBox.value.toLowerCase();
        const rows = document.querySelectorAll('#studentTable tbody tr');

        rows.forEach(function (row) {
            const studentDetails = row.textContent.toLowerCase();
            if (studentDetails.includes(searchText)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}
