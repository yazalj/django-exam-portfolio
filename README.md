# Django Exam Engine & Web Interface

**Status:** Completed Academic Group Project (University of Göttingen)
**Role:** Full Stack Developer (Data Engineering, Backend Logic, & UI)
**Tech Stack:** Python, Django, PostgreSQL, SQLite, Pandas, HTML/CSS.

## 📂 Repository Context
This repository isolates my specific, completed contributions to the **"Driving School Exam"** application. 

While the overarching project (which includes user authentication and external dashboards developed by teammates) is maintained in a private collaborative repository, this portfolio snippet is made public to demonstrate my end-to-end development capabilities. It highlights my work in: **Raw Data Ingestion, Database Architecture, Backend Exam Logic, and Frontend Rendering.**

## 🛠 Core Contributions & Features Built

### 1. Automated ETL Pipeline (`load_exam_data.py`)
- **Challenge:** Source driving test data was fragmented across multiple disconnected CSV files with non-standard delimiters.
- **Implementation:** Engineered a robust data ingestion pipeline using **Pandas** and custom **Django Management Commands**. 
- **Result:** Automated the cleaning, merging, and dictionary-mapping (O(n) time complexity) of answers to questions, ensuring clean data insertion with automated duplication prevention.

### 2. Database Architecture (`models.py`)
- Designed and implemented the relational database schema using Django's ORM.
- Architected the `Question` and `Choice` models with `ForeignKey` relationships and `CASCADE` deletion to strictly enforce data integrity.
- Designed initially for **PostgreSQL** compatibility for production readiness, while utilizing SQLite for agile local development within the team.

### 3. Core Exam Engine (`views.py`)
- **Algorithmic Randomization:** Developed the session logic to dynamically generate a unique, randomized 20-question exam subset for each user attempt.
- **Real-Time Scoring:** Implemented the backend POST request handling to evaluate user submissions against the database, calculate scores, and enforce an 80% passing threshold.

### 4. Interactive User Interface (`templates/exam_app/`)
- Translated backend data structures into a responsive frontend experience.
- Developed the **Exam Interface (`exam.html`)** to handle dynamic form generation and submissions.
- Built the **Results Dashboard (`result.html`)** to provide users with immediate, dynamically rendered feedback on their performance and pass/fail status.

## 📄 Code Structure
- `management/commands/load_exam_data.py`: The custom ETL pipeline script.
- `models.py`: The relational database schema.
- `views.py`: Request handling, exam logic, and context rendering.
- `templates/exam_app/`: The HTML/CSS frontend views.
