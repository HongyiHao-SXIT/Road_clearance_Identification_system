from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from database.db import db
from database.models import User

auth_bp = Blueprint("auth_bp", __name__)

login_manager = LoginManager()
login_manager.login_view = "auth_bp.login_page"


class LoginUser(UserMixin):
    
    def __init__(self, user: User):
        self._user = user
        self.id = str(user.id)

    @property
    def username(self):
        return self._user.username

    @property
    def role(self):
        return self._user.role


@login_manager.user_loader
def load_user(user_id: str):
    u = User.query.get(int(user_id))
    return LoginUser(u) if u else None


@auth_bp.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""
    security_code = request.form.get("security_code") or ""

    if not username or not password:
        flash("用户名和密码不能为空")
        return redirect(url_for("auth_bp.register_page"))
    if password != password2:
        flash("两次密码不一致")
        return redirect(url_for("auth_bp.register_page"))
    if len(password) < 6:
        flash("密码至少 6 位")
        return redirect(url_for("auth_bp.register_page"))

    if User.query.filter_by(username=username).first():
        flash("用户名已存在")
        return redirect(url_for("auth_bp.register_page"))
    
    if not security_code:
        flash("请设置安全码")
        return redirect(url_for("auth_bp.register_page"))

    u = User(username=username, role="user", security_code=security_code)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()

    flash("注册成功，请登录")
    return redirect(url_for("auth_bp.login_page"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    u = User.query.filter_by(username=username).first()
    if not u or not u.check_password(password):
        flash("用户名或密码错误")
        return redirect(url_for("auth_bp.login_page"))

    login_user(LoginUser(u), remember=True)
    return redirect(url_for("main_bp.index"))

@auth_bp.route("/forget", methods=["GET", "POST"])
def forget():
    if request.method == "GET":
        return render_template("forget.html")
    
    username = (request.form.get("username") or "").strip()
    newpassword = (request.form.get("newpassword") or "").strip()
    security_code = (request.form.get("security_code") or "").strip()

    u = User.query.filter_by(username=username).first()
    if not u or not u.check_securitycode(security_code):
        flash("用户名或安全码错误")
        return redirect(url_for("auth_bp.forget")) 
    
    u.set_password(newpassword)
    db.session.commit()
    
    flash("修改成功")
    return redirect(url_for("auth_bp.login_page"))

@auth_bp.route("/logout", methods=["GET"])
@login_required
def logout_page():
    logout_user()
    flash("已退出登录")
    return redirect(url_for("auth_bp.login_page"))
