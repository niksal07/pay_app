import os
import tempfile
import pytest
from app import app, db, User, Bill
from werkzeug.security import generate_password_hash
from datetime import datetime

# --------------------------
# FIXTURE: Isolated Test Client + DB
# --------------------------
@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = 'test_uploads'

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

    os.close(db_fd)
    os.unlink(db_path)

# --------------------------
# HELPERS
# --------------------------
def create_user(username, password, role="user"):
    """Helper to create test users in DB."""
    user = User(username=username, role=role)
    user.password_hash = generate_password_hash(password)
    db.session.add(user)
    db.session.commit()
    return user

def login(client, username, password, url="/"):
    return client.post(url, data={"username": username, "password": password}, follow_redirects=True)

# --------------------------
# TEST CASES
# --------------------------

def test_register_and_login_user(client):
    """Test user registration and login flow"""
    # Register
    resp = client.post("/register", data={
        "username": "testuser",
        "password": "secret"
    }, follow_redirects=True)
    assert b"Registration successful" in resp.data

    # Login
    resp = login(client, "testuser", "secret", "/")
    assert resp.status_code == 200
    assert b"Invalid credentials" not in resp.data

def test_admin_login_and_add_bill(client):
    """Test admin can login and add a bill"""
    # Create admin + normal user
    admin = create_user("admin", "adminpass", role="admin")
    normal_user = create_user("john", "johnpass", role="user")

    # Admin login
    resp = login(client, "admin", "adminpass", "/admin-login")
    assert resp.status_code == 200

    # Admin adds a bill for john
    resp = client.post("/admin", data={
        "month": "August",
        "invoice_no": "INV1001",
        "amount": "2500",
        "due_date": "2025-08-30",
        "bill_name": "Electricity",
        "user_id": normal_user.id
    }, follow_redirects=True)

    assert b"Bill added successfully" in resp.data
    bill = Bill.query.first()
    assert bill.invoice_no == "INV1001"
    assert bill.user_id == normal_user.id

def test_file_upload_payment(client, tmp_path):
    """Test user uploads payment proof for bill"""
    # Setup user + bill
    user = create_user("alice", "alicepass", role="user")
    bill = Bill(month="Sept", invoice_no="INV2002", amount=3000,
                due_date=datetime(2025, 9, 20), user_id=user.id)
    db.session.add(bill)
    db.session.commit()

    # Login
    login(client, "alice", "alicepass", "/")

    # Fake file to upload
    fake_file = tmp_path / "receipt.png"
    fake_file.write_bytes(b"fake-image-data")

    # Upload
    with open(fake_file, "rb") as f:
        resp = client.post(f"/pay/{bill.id}", 
                           data={"payment_proof": (f, "receipt.png")},
                           content_type="multipart/form-data",
                           follow_redirects=True)

    bill = Bill.query.get(bill.id)
    assert resp.status_code == 200
    assert b"Payment proof submitted successfully" in resp.data
    assert bill.payment_status == "Submitted for review"
    assert bill.image_filename is not None

def test_allowed_file_function():
    """Unit test for helper allowed_file()"""
    from app import allowed_file
    assert allowed_file("test.png") is True
    assert allowed_file("doc.pdf") is True
    assert allowed_file("script.exe") is False
