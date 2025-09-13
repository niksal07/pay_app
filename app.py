import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bills.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Allowed file types
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ------------------------
# MODELS
# ------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default="user")  # 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(20), nullable=False)
    invoice_no = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    payment_status = db.Column(db.String(50), default="Pending")
    image_filename = db.Column(db.String(100), nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    bill_name = db.Column(db.String(100))   
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('bills', lazy=True))
# ------------------------
# LOGIN MANAGER
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------
# HELPER FUNCTIONS
# ------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------
# ROUTES
# ------------------------
#home page
@app.route('/', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.role == "user":
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials or role.")
    return render_template('login.html')

# registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')  # default user
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for('client_login'))  # <-- fixed here

    return render_template('register.html')






@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.role == "admin":
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash("Invalid admin credentials.")
    return render_template('admin_login.html')

from datetime import datetime

from datetime import date

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != "admin":
        return redirect(url_for('client_login'))

    users = User.query.all()

    if request.method == "POST":
        bill_id = request.form.get("bill_id")

        # If editing existing bill
        if bill_id:
            bill = Bill.query.get_or_404(bill_id)
            bill.month = request.form['month']
            bill.invoice_no = request.form['invoice_no']
            bill.amount = float(request.form['amount'])
            bill.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
            bill.payment_status = request.form.get('payment_status', bill.payment_status)
            bill.bill_name = request.form.get('bill_name', bill.bill_name)
            bill.user_id = int(request.form['user_id'])
            db.session.commit()
            flash("Bill updated successfully!", "success")
        
        # If adding new bill
        else:
            new_bill = Bill(
                month=request.form['month'],
                invoice_no=request.form['invoice_no'],
                amount=float(request.form['amount']),
                due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d'),
                payment_status=request.form.get('payment_status', 'Pending'),
                bill_name=request.form.get('bill_name'),
                user_id=int(request.form['user_id'])
            )
            db.session.add(new_bill)
            db.session.commit()
            flash("Bill added successfully!", "success")

        return redirect(url_for('admin'))

    bills = Bill.query.order_by(Bill.due_date.asc()).all()
    return render_template('admin.html', users=users, bills=bills, date=date)


@app.route('/admin-logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin_login'))


@app.route('/bills')
@login_required
def index():
    bills = Bill.query.filter_by(user_id=current_user.id).order_by(Bill.id).all()
    return render_template('index.html', bills=bills)
@app.route('/upload/<int:bill_id>', methods=['GET', 'POST'])
def upload(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    if request.method == 'POST':
        file = request.files['payment_image']
        if file:
            filename = f"{bill_id}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            bill.payment_status = "Submitted for review"
            bill.image_filename = filename
            db.session.commit()
            flash("Payment uploaded successfully.")
            return redirect(url_for('index'))
    return render_template('upload.html', bill=bill)
# ------------------------
# PAY BILL (Upload Proof)
# ------------------------
@app.route('/pay/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def pay_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)

    if request.method == 'POST':
        if 'payment_proof' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)

        file = request.files['payment_proof']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            bill.image_filename = filename
            bill.payment_status = 'Submitted for review'
            db.session.commit()

            flash('Payment proof submitted successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type!', 'danger')
            return redirect(request.url)

    return render_template('pay.html', bill=bill)

# ------------------------
# CLI COMMANDS
# ------------------------
@app.cli.command("create-admin")
def create_admin():
    if not User.query.filter_by(username="admin").first():
        admin_user = User(username="admin", role="admin")
        admin_user.set_password("admin123")  # You can change this
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin already exists.")

# ------------------------
# EDIT BILL (Admin only)
# ------------------------
@app.route('/admin/edit-bill/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_bill(bill_id):
    if current_user.role != "admin":
        abort(403)

    bill = Bill.query.get_or_404(bill_id)

    if request.method == 'POST':
        bill.month = request.form['month']
        bill.invoice_no = request.form['invoice_no']
        bill.amount = float(request.form['amount'])
        bill.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')

        db.session.commit()
        flash('Bill updated successfully!', 'success')
        return redirect(url_for('admin'))

    return render_template('edit_bill.html', bill=bill)
@app.route('/admin/delete_bill/<int:bill_id>', methods=['POST'])
def delete_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)  # Fetch bill or return 404 if not found
    db.session.delete(bill)
    db.session.commit()
    flash('Bill deleted successfully!', 'success')
    return redirect(url_for('admin'))
@app.cli.command("reset-db")
def reset_db():
    db.drop_all()
    db.create_all()
    print("Database has been reset.")

# ------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True) 
