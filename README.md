# QuizPress (QTI-to-HTML Test Creation Manager)

A Django-powered web application to import/export Canvas QTI test banks, manage in-class test questions, and generate hardcopy exams and answer keys in HTML (Word-friendly) format.

---

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Features](#features)  
3. [Tech Stack](#tech-stack)  
4. [Requirements](#requirements)  

---

## Project Overview

Instructors spend hours copying and formatting questions from Canvas into paper exams. **QuizPress** solves this by:

- **Importing** Canvas QTI files (question banks & tests).  
- **Managing** question metadata for in-class use.  
- **Editing** and **tracking** question attributes.  
- **Generating** neatly formatted HTML exams and red/blue answer keys for Word.  
- **Exporting** back to QTI or Excel for interoperability.  
- **Multi-user** roles (Webmaster, Publisher, Teacher) with access control.

---

## Features

- **QTI ↔ Canvas**:  
  - Import valid QTI ZIP/XML into course banks  
  - Export QTI packages compatible with Canvas  
- **Question Bank Management**:  
  - Add/Edit/Delete questions (TF, MC, Matching, Fill-in, Essay, Short Answer, Dynamic)  
  - Track embedded graphics, references, default points, estimated answer time, test usage  
  - Instructor comments & per-question feedback  
- **Test Assembly**:  
  - Pick questions from bank or template  
  - Randomize question order (with matching answers aligned)  
  - Draft vs. final tests, with warnings for editing published items  
- **Templates & Cover Pages**:  
  - Create multiple templates (fonts, headers/footers, section order, bonus section)  
  - Define cover page fields (course number, test number, date, filename, student name blank, key instructions)  
- **Attachments**:  
  - Append reference materials (PDFs, images) to exam end  
- **Output**:  
  - HTML test and key (answers in red, grading tips in blue) ready for Word  
  - Excel import/export of question banks  
- **Access Control**:  
  - **Webmaster**: site & user management  
  - **Publisher**: create textbook-linked question banks, respond to feedback  
  - **Teacher**: manage personal course banks, share & rate publisher questions  

---

## Tech Stack

- **Python**: 3.8+  
- **Django**: 4.x  
- **Django REST Framework**  
- **BeautifulSoup4** & **lxml** (QTI XML parsing)  
- **MySQL** (via `mysqlclient` or `PyMySQL`)  
- **openpyxl** (Excel import/export)  
- **requests** (HTTP)  
- **Pillow** (image handling)
- **pandas**
