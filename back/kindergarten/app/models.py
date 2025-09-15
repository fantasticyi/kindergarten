from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()  # 没有参数的实例化数据库对象


class Admin(db.Model):
    __tablename__ = 'Admin'

    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pwd = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    token = db.Column(db.String(512), nullable=True)
    def set_password(self, password):
        self.pwd = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwd, password)


class Parent(db.Model):
    __tablename__ = 'Parent'

    guardian_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    pwd = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(512), nullable=True)
    children = db.relationship('Child', backref='guardian', foreign_keys='Child.guardian_id')

    def set_password(self, password):
        self.pwd = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwd, password)


class Class(db.Model):
    __tablename__ = 'Class'

    class_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.Enum('小班', '中班', '大班', '体验班'), nullable=False)
    student_count = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    students = db.relationship('Child', backref='class_info')
    teachers = db.relationship('Teacher', secondary='Teacher_Class', backref='classes')


class Teacher(db.Model):
    __tablename__ = 'Teacher'

    teacher_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    pwd = db.Column(db.String(255), nullable=False)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    role = db.Column(db.String(20))
    token = db.Column(db.String(512), nullable=True)
    assessments = db.relationship('Dq', backref='teacher')

    def set_password(self, password):
        self.pwd = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwd, password)


class TeacherClass(db.Model):
    __tablename__ = 'Teacher_Class'

    teacher_id = db.Column(db.Integer, db.ForeignKey('Teacher.teacher_id'), primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('Class.class_id'), primary_key=True)
    is_headTeacher = db.Column(db.Boolean, nullable=False, default=False)


class Child(db.Model):
    __tablename__ = 'Child'

    child_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    child_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.Enum('男', '女'), nullable=False)
    nation = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text)
    created_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    class_id = db.Column(db.Integer, db.ForeignKey('Class.class_id'))
    guardian_id = db.Column(db.Integer, db.ForeignKey('Parent.guardian_id'))

    assessments = db.relationship('Dq', backref='child')


class QuizInfo(db.Model):
    __tablename__ = 'QuizInfo'

    quiz_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quiz_name = db.Column(db.String(100), nullable=False)
    quiz_method = db.Column(db.String(255), nullable=False)
    pass_need = db.Column(db.String(255), nullable=False)
    sort = db.Column(db.Integer, nullable=False)  # 1-5 as per your schema
    month_age = db.Column(db.Integer, nullable=False)

    test_details = db.relationship('TestDetail', backref='quiz')


class Dq(db.Model):
    __tablename__ = 'Dq'

    dq_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    month_age = db.Column(db.Integer, nullable=False)
    gross_motor_score = db.Column(db.Float, default=0)
    fine_motor_score = db.Column(db.Float, default=0)
    language_score = db.Column(db.Float, default=0)
    adaptability_score = db.Column(db.Float, default=0)
    social_score = db.Column(db.Float, default=0)
    dq = db.Column(db.Float, default=0)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pdf_path = db.Column(db.String(255), default='')
    teacher_id = db.Column(db.Integer, db.ForeignKey('Teacher.teacher_id'))
    child_id = db.Column(db.Integer, db.ForeignKey('Child.child_id'))

    test_details = db.relationship('TestDetail', backref='assessment')


class TestDetail(db.Model):
    __tablename__ = 'TestDetail'

    dq_id = db.Column(db.Integer, db.ForeignKey('Dq.dq_id'), primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('QuizInfo.quiz_id'), primary_key=True)
    is_pass = db.Column(db.Boolean, default=False)


class Game(db.Model):
    __tablename__ = 'Game'

    game_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_name = db.Column(db.String(255), nullable=False)
    game_sort = db.Column(db.Integer, nullable=False)
    game_beginTime = db.Column(db.Integer, nullable=False)  # Storing as timestamp
    game_endTime = db.Column(db.Integer, nullable=False)  # Storing as timestamp
    game_bg = db.Column(db.Text, default='')
    game_prepare = db.Column(db.Text, nullable=False)
    game_purpose = db.Column(db.Text, nullable=False)
    game_process = db.Column(db.Text, nullable=False)
    cautions = db.Column(db.Text, nullable=False)


if __name__ == '__main__':
    db.create_all()
    # db.drop_all()
