# SmartGPA - Midterm Progress Slide Plan

Use this file as the content checklist for the 10-12 slide PDF required by the course.

## Slide 1 - Title
- Topic: SmartGPA - Academic analytics, GPA simulation, and early academic warning system.
- Course: Service-Oriented Architecture and Cloud Computing.
- Cloud platform: Databricks.
- GitHub: https://github.com/mangcutxinh/Smart-GPA

## Slide 2 - Group Information
- Members: add 1-5 student names and student IDs.
- Roles:
  - Backend/SOA: FastAPI API gateway, auth, simulation engine.
  - Data/Cloud: Databricks workspace, Delta Lake pipeline, SQL Warehouse.
  - Frontend: React role-based portal.
  - QA/Data Analyst: tests, demo data, screenshots.

## Slide 3 - System Goal
- Support students in simulating target letter grades and required final/practical scores.
- Support lecturers in uploading raw score CSV files.
- Support admins in monitoring at-risk students.
- Centralize academic score processing through Databricks Delta Lake.

## Slide 4 - Finalized SOA Architecture
- Client UI: React portals for Student, Lecturer, Admin.
- API Gateway: FastAPI with JWT authentication and role-based access.
- Services:
  - Auth Gateway.
  - Upload Hub.
  - Simulation Engine.
  - Academic Warning / ML Risk Service.
  - Admin Management.
- Cloud/Data: Databricks SQL Warehouse, Delta Lake Bronze/Silver/Gold tables.

## Slide 5 - Overall Data Flow
- Lecturer uploads CSV score file through `/upload/file`.
- Backend validates file format, headers, score ranges, and course type.
- Raw file is stored under `storage_mock/raw/diem` for local demo and maps to cloud path `s3://smartgpa-bucket/raw/diem`.
- Databricks Auto Loader ingests raw files into Bronze.
- Spark ETL cleans and standardizes data into Silver.
- Gold Delta table serves simulation, warning, and reporting queries.
- Student calls `/simulation/calc` to query Gold data and run inverse grade calculation.

## Slide 6 - Databricks Deployment Progress
- Workspace/cluster: prepared for SmartGPA notebooks and SQL Warehouse connection.
- Notebook/job template: `databricks-code-template.md`.
- Pipeline design: Bronze -> Silver -> Gold medallion architecture.
- Backend connector: `backend/app/db/databricks_db.py`.
- Environment variables: `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_TOKEN`, `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`.

## Slide 7 - Implemented Backend Evidence
- FastAPI app: `backend/app/main.py`.
- Auth/JWT and role protection: `backend/app/routers/auth.py`, `backend/app/core/dependencies.py`.
- Upload validation and raw ingestion endpoint: `backend/app/routers/upload.py`.
- Simulation endpoint integrated with Gold table query: `backend/app/routers/simulation.py`.
- Databricks/Delta fallback database for demo: `backend/app/db/databricks_db.py`.

## Slide 8 - Implemented Frontend Evidence
- React app: `frontend/src/App.tsx`.
- Student portal: target grade simulation and Databricks/Gold query mode.
- Lecturer portal: score upload and grade edit workflow.
- Admin portal: warning list, ML risk lookup, warning email simulation.
- Admin portal: semester, course, unit, assignment, and lecturer management.

## Slide 9 - Testing and Current Progress
- Automated tests: `pytest tests -q`.
- Current result: 57 passed.
- Covered flows:
  - Login and role authorization.
  - Upload validation with fail-fast errors.
  - Upload -> mock Delta Gold sync -> simulation.
  - Inverse score calculation for theory, practice, and integrated courses.
  - Warning/risk support logic.

## Slide 10 - Required Screenshots
Add actual screenshots before exporting to PDF:
- Databricks workspace and cluster.
- Databricks notebook output for Bronze/Silver/Gold processing.
- Databricks SQL table preview for `gold_diem_sinh_vien`.
- Databricks job or pipeline run status.
- Swagger UI for `/upload/file` and `/simulation/calc`.
- React UI showing upload, simulation result, and warning monitor.
- GitHub repository link shown directly on the slide.

## Slide 11 - Difficulties and Open Issues
- Real cloud storage integration still needs final Databricks credential setup.
- Local demo currently uses `storage_mock` and in-memory Delta-like fallback when Databricks credentials are absent.
- Need collect real Databricks UI screenshots for the submitted PDF.
- Need confirm final member list and GitHub link placement on title/evidence slides.

## Slide 12 - Plan to Final Submission
- Week 1: finalize Databricks workspace, cluster, SQL Warehouse, and secrets.
- Week 2: run Auto Loader and ETL notebook against real uploaded files.
- Week 3: connect FastAPI to real Gold Delta table and verify end-to-end demo.
- Week 4: improve MLflow risk endpoint and Databricks SQL dashboard.
- Week 5: final testing, screenshots, report demo script, and PDF export.

## Architecture Lock Note
The midterm architecture should be treated as the finalized baseline:
React UI -> FastAPI API Gateway -> Auth/Upload/Simulation/Warning/Admin services -> Databricks SQL Warehouse -> Delta Lake Bronze/Silver/Gold.

If this changes before the final report, explain the reason and impact in the final slides.
