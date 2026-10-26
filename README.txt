SCHOOL MANAGEMENT SYSTEM — FINAL PACKAGE

FEATURES
- Dashboard and student count
- Add, view, search, edit, and delete student records
- Student ID numbers generated automatically (STU-0001, etc.)
- Optional student photo upload (JPG/JPEG/PNG/WEBP, up to 3 MB)
- Student photos shown in the directory and ID-card preview/PDF
- Downloadable Student ID Card PDF
- Transfer Certificate form and downloadable PDF
- School name, address, phone, email, principal, and logo settings
- Configure available classes in School Settings (default 8,9,10; enter 8,9,10,11,12 to add more)
- SQLite database and automatic migration for earlier project databases
- Search by name, ID, class, or roll number

RUN IN VS CODE
1. Extract this ZIP to a folder.
2. Open that folder in VS Code.
3. Open Terminal > New Terminal.
4. Run: python -m pip install -r requirements.txt
5. Run: python app.py (on some Windows systems: py app.py)
6. Open http://127.0.0.1:5000 in your browser.

DATABASE / EXISTING RECORDS
- The app creates school.db automatically on first run.
- To keep records from your previous project, close the app and copy your old school.db into this project folder BEFORE running it. Back up the database first. The app adds missing photo/classes/logo fields automatically.
- Keep static/uploads with the project so saved student photos and school logos remain available.

IMPORTANT
- Use fictional test records until login, access controls, backup procedures, and privacy requirements have been reviewed. This local starter app has no administrator login and should not be exposed to the public internet.
- The ID card and TC layouts are sample layouts. Have the school verify its official format before issuing official documents.
