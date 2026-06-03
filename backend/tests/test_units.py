"""
SmartGPA Tests – Faculty, Institute, and Major CRUD operations & constraints
"""
import pytest
from app.db.fake_db import DEPARTMENTS_DB, INSTITUTES_DB, MAJORS_DB

def test_get_departments_unauthorized(client):
    # Test getting departments without auth token -> 403
    resp = client.get("/admin/departments")
    assert resp.status_code == 403


def test_get_departments_forbidden(client, student_token):
    # Test getting departments with student token -> 403
    resp = client.get("/admin/departments", headers={"Authorization": f"Bearer {student_token}"})
    assert resp.status_code == 403


def test_get_departments_success(client, admin_token):
    # Test getting departments with admin token -> 200
    resp = client.get("/admin/departments", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # CNCK or CNTT should be in there
    ids = [d["id"] for d in data]
    assert "CNTT" in ids
    assert "CNCK" in ids


def test_crud_department(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Create department
    new_dept = {"id": "TEST_DEPT", "name": "Khoa Kiểm thử tự động", "type": "khoa"}
    resp = client.post("/admin/departments", json=new_dept, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == "TEST_DEPT"
    
    # Verify duplicates check
    resp_dup = client.post("/admin/departments", json=new_dept, headers=headers)
    assert resp_dup.status_code == 400
    
    # 2. Update department name
    updated_dept = {"id": "TEST_DEPT", "name": "Khoa Kiểm thử nâng cao", "type": "khoa"}
    resp_put = client.put("/admin/departments/TEST_DEPT", json=updated_dept, headers=headers)
    assert resp_put.status_code == 200
    assert resp_put.json()["name"] == "Khoa Kiểm thử nâng cao"
    
    # 3. Delete department
    resp_del = client.delete("/admin/departments/TEST_DEPT", headers=headers)
    assert resp_del.status_code == 200
    
    # Verify gone
    resp_get = client.get("/admin/departments", headers=headers)
    ids = [d["id"] for d in resp_get.json()]
    assert "TEST_DEPT" not in ids


def test_crud_institute(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Create institute
    new_inst = {"id": "TEST_INST", "name": "Viện Công nghệ vũ trụ", "type": "vien"}
    resp = client.post("/admin/institutes", json=new_inst, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == "TEST_INST"
    
    # 2. Update institute name
    updated_inst = {"id": "TEST_INST", "name": "Viện Kỹ thuật hàng không", "type": "vien"}
    resp_put = client.put("/admin/institutes/TEST_INST", json=updated_inst, headers=headers)
    assert resp_put.status_code == 200
    assert resp_put.json()["name"] == "Viện Kỹ thuật hàng không"
    
    # 3. Delete institute
    resp_del = client.delete("/admin/institutes/TEST_INST", headers=headers)
    assert resp_del.status_code == 200


def test_crud_major(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Create major linked to existing faculty (CNTT)
    new_major = {"id": "TEST_MAJ", "name": "Ngành Lập trình nhúng", "faculty_id": "CNTT"}
    resp = client.post("/admin/majors", json=new_major, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == "TEST_MAJ"
    
    # Create major with non-existent faculty -> 400 Bad Request
    bad_major = {"id": "BAD_MAJ", "name": "Ngành Không tồn tại", "faculty_id": "NON_EXIST"}
    resp_bad = client.post("/admin/majors", json=bad_major, headers=headers)
    assert resp_bad.status_code == 400
    
    # 2. Update major
    updated_major = {"id": "TEST_MAJ", "name": "Ngành Thiết kế vi mạch thông minh", "faculty_id": "CNTT"}
    resp_put = client.put("/admin/majors/TEST_MAJ", json=updated_major, headers=headers)
    assert resp_put.status_code == 200
    assert resp_put.json()["name"] == "Ngành Thiết kế vi mạch thông minh"
    
    # 3. Delete major
    resp_del = client.delete("/admin/majors/TEST_MAJ", headers=headers)
    assert resp_del.status_code == 200
    
    # Verify gone
    resp_get = client.get("/admin/majors", headers=headers)
    ids = [m["id"] for m in resp_get.json()]
    assert "TEST_MAJ" not in ids


def test_crud_lecturer(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create lecturer
    new_lec = {
        "email": "test_lec@smartgpa.edu",
        "password": "password123",
        "full_name": "TS. Giảng Viên Test",
        "role": "lecturer",
        "lecturer_id": "GV_TEST",
        "faculty_id": "CNTT"
    }
    resp = client.post("/admin/lecturers", json=new_lec, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["lecturer_id"] == "GV_TEST"
    assert resp.json()["faculty_id"] == "CNTT"

    # Duplicates check (by email)
    resp_dup = client.post("/admin/lecturers", json=new_lec, headers=headers)
    assert resp_dup.status_code == 400

    # Duplicates check (by lecturer_id)
    dup_id = new_lec.copy()
    dup_id["email"] = "another@smartgpa.edu"
    resp_dup_id = client.post("/admin/lecturers", json=dup_id, headers=headers)
    assert resp_dup_id.status_code == 400

    # Non-existent faculty check
    bad_fac = new_lec.copy()
    bad_fac["email"] = "bad_fac@smartgpa.edu"
    bad_fac["lecturer_id"] = "GV_BAD_FAC"
    bad_fac["faculty_id"] = "NON_EXIST"
    resp_bad = client.post("/admin/lecturers", json=bad_fac, headers=headers)
    assert resp_bad.status_code == 400

    # 2. Update lecturer
    update_data = {
        "full_name": "TS. Giảng Viên Test Đã Sửa",
        "email": "test_lec_edited@smartgpa.edu",
        "faculty_id": "CNTT"
    }
    resp_put = client.put("/admin/lecturers/GV_TEST", json=update_data, headers=headers)
    assert resp_put.status_code == 200
    assert resp_put.json()["full_name"] == "TS. Giảng Viên Test Đã Sửa"
    assert resp_put.json()["email"] == "test_lec_edited@smartgpa.edu"

    # 3. Delete lecturer
    resp_del = client.delete("/admin/lecturers/GV_TEST", headers=headers)
    assert resp_del.status_code == 200

    # Verify gone from list
    resp_get = client.get("/admin/lecturers", headers=headers)
    ids = [l["lecturer_id"] for l in resp_get.json()]
    assert "GV_TEST" not in ids
