# Django Exam Engine & Web Interface

**Project:** Core module for the "Driving School Exam" Group Project.
**Role:** Data Storage and Handling, User Interface
**Tech Stack:** Python, Django, PostgreSQL, SQLite, Pandas, HTML/CSS.

## 📂 Project Context
This repository contains the **Data Handling, Exam Logic, and User Interface** I developed for a driving test application.

While the wider project involved user authentication and external dashboards, this module represents my end-to-end contribution: ingestion of raw data, processing the exam logic, and rendering the frontend interface for the student.

## 🛠 Key Features I Built

### 1. Custom ETL Pipeline (Backend)
I engineered a custom Django Management Command (`load_exam_data.py`) to automate data ingestion.
- **Problem:** Source data was split between disconnected CSVs with non-standard delimiters.
- **Solution:** utilized **Pandas** to clean and merge data, implementing a dictionary-mapping algorithm to link Answers to Questions in O(n) time.
- **Integrity:** Includes automated database cleaning to prevent duplication during re-runs.

### 2. Exam Logic Engine (Backend)
Implemented the core session logic in `views.py`.
- **Randomization:** Generates a unique 20-question test session using random sampling.
- **Scoring System:** Processes POST requests, calculates scores against an 80% pass threshold, and commits results to the database.

### 3. User Interface (Frontend)
Developed the functional HTML/CSS templates for the exam interaction.
- **Exam Page (`exam.html`):** Designed the form interface to handle multiple-choice inputs, ensuring data is passed correctly to the backend via POST.
- **Results Page (`result.html`):** Built the feedback view to dynamically display the user's score and pass/fail status based on the backend calculation.

### 4. Database Architecture (`models.py`)
- Architected the relational schema (Questions linked to Choices) using Django's ORM.
- Originally designed for **PostgreSQL** to ensure data strictness, adapted to SQLite for local development flexibility.

## 📄 Code Structure
- `management/commands/`: Data pipeline scripts.
- `templates/`: The HTML/CSS frontend views.
- `views.py`: Request handling and template rendering.
- `models.py`: Database schema.
