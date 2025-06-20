from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'patient')

        if User.query.filter_by(username=username).first():
            flash('Tên người dùng đã tồn tại', 'error')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng', 'error')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username,
            email=email,
            role=role
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Đăng ký thành công! Vui lòng đăng nhập', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('main.index'))
            
        flash('Tên đăng nhập hoặc mật khẩu không đúng', 'error')
        
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('Email đã được sử dụng', 'error')
            else:
                current_user.email = email
                
        if current_password and new_password:
            if current_user.check_password(current_password):
                current_user.set_password(new_password)
                flash('Đã cập nhật mật khẩu', 'success')
            else:
                flash('Mật khẩu hiện tại không đúng', 'error')
                
        db.session.commit()
        flash('Đã cập nhật thông tin tài khoản', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html')