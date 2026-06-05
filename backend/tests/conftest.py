"""
SmartGPA Tests – Shared fixtures
"""
import sys
import os

# Đảm bảo pytest tìm được package `app` khi chạy từ thư mục backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient – dùng chung cho toàn module"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def student_token(client):
    resp = client.post("/auth/login", json={
        "email": "student@smartgpa.edu", "password": "Sv@123"
    })
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def lecturer_token(client):
    resp = client.post("/auth/login", json={
        "email": "thibinh.gv1001@smartgpa.edu", "password": "Gv@123"
    })
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token(client):
    resp = client.post("/auth/login", json={
        "email": "admin@smartgpa.edu", "password": "Admin@123"
    })
    return resp.json()["access_token"]
