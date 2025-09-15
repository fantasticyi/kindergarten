import jwt
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, current_app
from . import user
from ..models import db, Parent, Teacher, Admin, Child, TeacherClass, Class
from ..auth import verify_token_and_get_user

def generate_token(user_id, role):
    """
    生成JWT token
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)  # 7天过期
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token


@user.route("/login", methods=["POST"])
def login():
    """
    用户登录接口
    支持家长、教师、管理员登录
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "请求数据格式错误",
                "data": None
            })

        username = data.get('username')
        password = data.get('password')
        # username = request.args.get('username')
        # password = request.args.get('password')

        # 尝试在不同用户表中查找用户
        user_info = None
        user_obj = None  # 用于存储找到的用户对象
        role = None  # 用于存储角色

        # 1. 家长（使用手机号作为用户名）
        parent = Parent.query.filter(Parent.phone == username).first()

        if parent and parent.check_password(password):
            # 查找该家长的孩子信息
            user_obj = parent
            role = "parent"
            child = Child.query.filter(
                (Child.guardian1_id == parent.guardian_id) |
                (Child.guardian2_id == parent.guardian_id)
            ).all()

            child2 = [{"child_id": c.child_id, "child_name": c.child_name} for c in child]

            user_info = {
                "user_id": parent.guardian_id,
                "username": parent.guardian_name,
                "role": "parent",
                "child": child2,
                "token": generate_token(parent.guardian_id, "parent")
            }

        # 2. 教师
        if not user_info:
            print(1)
            t = Teacher.query.filter_by(phone=username).first()
            if t:
                print(f"教师ID: {t.teacher_id}")
            else:
                print("该用户不是教师，准备尝试管理员登录")

            if t and t.check_password(password):
                user_obj = t
                role = "teacher"
                user_info = {
                    "user_id": t.teacher_id,
                    "username": t.teacher_name,
                    "role": "teacher",
                    "teacher_role": t.role,
                    "token": generate_token(t.teacher_id, "teacher")
                }

        # 3. 管理员
        if not user_info:
            admin = Admin.query.filter(Admin.phone == username).first()

            if admin and admin.check_password(password):
                user_obj = admin
                role = "admin"
                user_info = {
                    "user_id": admin.admin_id,
                    "username": "管理员",
                    "role": "admin",
                    "token": generate_token(admin.admin_id, "admin")
                }

                # 如果用户验证成功
        if user_info and user_obj and role:
            old_token_from_db = user_obj.token
            new_token = generate_token(user_info['user_id'], role)
            user_info["uniquetoken"] = new_token
            # 写入数据库
            user_obj.token = new_token
            db.session.commit()

            code = 200
            message = "success" if old_token_from_db == new_token else "Token mismatch, potential new device login."

            return jsonify({
                        "code": code,
                        "message": message,
                        "data": user_info
                    })

                    # 用户名或密码错误
        return jsonify({
                    "code": 400,
                    "message": "用户名或密码错误",
                    "data": None
                })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })


def verify_token(token):
    """
    验证JWT token
    """
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@user.route("/getAllClasses", methods=["GET"])
def getAllClasses():
    try:
        # 获取请求参数
        manager_id = request.args.get('manager_id')
        if not manager_id:
            return jsonify({"code": 400, "message": "缺少必要参数: manager_id", "data": []})


        # 检查是否为管理员
        manager_admin = Admin.query.get(manager_id)
        if manager_admin:
            pass
        else:
            # 检查是否为园长
            manager = Teacher.query.get(manager_id)
            if not manager or manager.role != "园长":
                return jsonify({"code": 400, "message": "没有操作权限", "data": []})

        # 查询所有班级信息
        all_classes = Class.query.all()
        class_list = [
            {
                "class_id": class_info.class_id,
                "class_name": class_info.class_name
            }
            for class_info in all_classes
        ]

        return jsonify({
            "code": 200,
            "message": "成功获取所有班级信息",
            "data": class_list
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"获取班级信息失败: {str(e)}",
            "data": []
        })

@user.route("/registerChild", methods=["POST"])
def registerChild():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据格式错误", "data": None})

        # 检查角色
        is_manager = 1   # 是否为园长
        manager_id = int(data.get("manager_id"))
        uniquetoken = request.args.get('uniquetoken')  # 新增：获取uniquetoken

        # --- 新增的Token验证逻辑 ---
        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # 检查是否为管理员
        manager_admin = Admin.query.get(manager_id)
        if manager_admin:
            pass
        else:
            manager = Teacher.query.get(manager_id)
            if not manager or manager.role != "园长":
                if manager.role != "管理级教师":
                    return jsonify({"code": 400, "message": "没有操作权限", "data": []})
                else:
                    is_manager = 0

        # 如果是管理级教师，则必须满足学生注册为自己管理的班级
        if not manager_admin and is_manager == 0:
            # 查询Teacher_Class表中该teacher_id对应的所有记录
            teacher_classes = TeacherClass.query.filter_by(teacher_id=manager_id).all()
            # 获取所有关联班级的详细信息
            class_list = []
            for tc in teacher_classes:
                class_list.append(tc.class_id)

            # 加入体验班，因为每个老师都能测试体验班(class_id=1)
            class_list.append(1)

            if int(data['class_id']) not in class_list:
                return jsonify({"code": 400, "message": "该学生必须加入该老师所管理的班级！", "data": []})

        # 是否为体验班
        is_experience = int(data['is_experience'])

        child_data = {
            'child_name': data['child_name'],
            'gender': data['gender'],
            'nation': data['nation'],
            'birth_date': datetime.strptime(data['birth_date'], "%Y-%m-%d"),
            'class_id': data['class_id'],
            'created_time': datetime.now(),
        }

        if is_experience == 1:
            child_data['class_id'] = 1

        new_child = Child(**child_data)
        db.session.add(new_child)
        db.session.flush()  # 获取新插入记录的ID

        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "child_id": new_child.child_id,  # 返回新增儿童的ID
                "child_name": new_child.child_name  # 返回新增儿童的姓名
            }
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })


@user.route("/deleteChild", methods=["POST"])
def deleteChild():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据格式错误", "data": None})

        # 检查必要参数
        if 'manager_id' not in data or 'child_id' not in data:
            return jsonify({"code": 400, "message": "缺少必要参数", "data": None})

        uniquetoken = data['uniquetoken']
        manager_id = data['manager_id']
        child_id = data['child_id']

        # --- 新增的Token验证逻辑 ---
        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---


        # 新增：检查是否为管理员
        manager_admin = Admin.query.get(manager_id)
        if not manager_admin:
            # 检查操作者是否为园长
            manager = Teacher.query.filter_by(teacher_id=manager_id).first()
            if not manager or manager.role not in ["园长", "管理级教师"]:
                return jsonify({"code": 400, "message": "没有操作权限", "data": None})

        # 查找要删除的孩子
        child = Child.query.filter_by(child_id=child_id).first()
        if not child:
            return jsonify({"code": 400, "message": "未找到该孩子信息", "data": None})

        # 执行删除操作
        db.session.delete(child)
        db.session.commit()

        return jsonify({"code": 200, "message": "删除成功", "data": []})

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"服务器错误: {str(e)}",
            "data": None
        })


@user.route("/registerTeacher", methods=["POST"])
def registerTeacher():
    # 获取请求数据
    data = request.get_json()
    teacher_name = data.get("teacher_name")
    phone = data.get("phone")
    pwd = data.get("pwd")
    role = data.get("role", "")
    manager_id = data.get("manager_id")
    uniquetoken = data.get("uniquetoken")  # 新增：获取uniquetoken

    # 验证必要字段
    if not all([teacher_name, phone, pwd]):
        return jsonify({"code": 400, "message": "缺少必要参数", "data": None})

        # --- 新增的Token验证逻辑 ---
    user, user_role = verify_token_and_get_user(manager_id, uniquetoken)
    if not user:
        return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---


    # 检查园长权限，再检查管理员权限
    manager_teacher = Teacher.query.get(manager_id)
    manager_admin = Admin.query.get(manager_id)
    has_permission = False
    if manager_teacher and manager_teacher.role == "园长":
        has_permission = True
    elif manager_admin:
        has_permission = True

    if not has_permission:
        return jsonify({"code": 400, "message": "没有操作权限", "data": []})

    # 检查手机号是否已存在
    if Teacher.query.filter_by(phone=phone).first():
        return jsonify({"code": 400, "message": "手机号已存在", "data": None})

    try:
        # 创建新老师
        new_teacher = Teacher(
            teacher_name=teacher_name,
            phone=phone,
            created_time=datetime.now(),
            role=role if role else None  # 如果role为空字符串，则设为None
        )
        new_teacher.set_password(pwd)

        db.session.add(new_teacher)
        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "注册成功",
            "data": []
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 400, "message": f"注册失败: {str(e)}", "data": None})


@user.route("/deleteTeacher", methods=["POST"])
def deleteTeacher():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据格式错误", "data": None})

        # 检查必要参数
        if 'manager_id' not in data or 'teacher_id' not in data:
            return jsonify({"code": 400, "message": "缺少必要参数", "data": None})

        manager_id = data['manager_id']
        teacher_id = data['teacher_id']
        uniquetoken = data.get('uniquetoken')  # 新增：获取uniquetoken

        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # 检查园长权限，再检查管理员权限
        manager_teacher = Teacher.query.get(manager_id)
        manager_admin = Admin.query.get(manager_id)
        has_permission = False
        if manager_teacher and manager_teacher.role == "园长":
            has_permission = True
        elif manager_admin:
            has_permission = True
        if not has_permission:
            return jsonify({"code": 400, "message": "没有操作权限", "data": []})

        # 查找要删除的老师
        t = Teacher.query.filter_by(teacher_id=teacher_id).first()
        if not t:
            return jsonify({"code": 400, "message": "未找到该老师信息", "data": None})

        # 执行删除操作
        db.session.delete(t)
        db.session.commit()

        return jsonify({"code": 200, "message": "删除成功", "data": []})

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"服务器错误: {str(e)}",
            "data": None
        })
