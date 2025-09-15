from datetime import datetime
from flask import request, jsonify
from . import admin
from ..models import db, Teacher, Class, Child, Parent, TeacherClass, Admin
from sqlalchemy import select
from ..auth import verify_token_and_get_user # 导入验证函数


@admin.route("/getChildInfo", methods=["GET"])
def getChildInfo():
    """
    查询所有学生列表
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        stmt = select(
            Child.child_id,
            Child.child_name,
            Child.gender,
            Child.class_id,
            Class.class_name
        ).join(Class, Child.class_id == Class.class_id)

        # Execute the query
        result = db.session.execute(stmt).all()

        # Convert result to list of dictionaries
        children = []
        for row in result:
            children.append({
                "child_id": row.child_id,
                "child_name": row.child_name,
                "gender": row.gender,
                "class_id": row.class_id,
                "class_name": row.class_name
            })

        return jsonify({
            "code": 200,
            "message": "success",
            "data": children
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": []
        })


@admin.route("/teacherList", methods=["GET"])
def getTeacherList():
    """
    查询所有教师列表
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        # 查询所有教师
        stmt = select(
            Teacher.teacher_id,
            Teacher.teacher_name,
            Teacher.role  # 用于判断是否拥有高级权限
        )

        result = db.session.execute(stmt).all()

        # 转换结果为所需格式
        teachers = []
        for row in result:
            # 判断是否拥有高级权限
            is_set = 1 if row.role in ["园长", "管理级教师"] else 0

            teachers.append({
                "teacher_id": row.teacher_id,
                "name": row.teacher_name,
                "is_set": is_set
            })

        return jsonify({
            "code": 200,
            "message": "success",
            "data": teachers
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": []
        })


@admin.route("/classList", methods=["GET"])
def getClassList():
    """
    查询所有班级列表
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        # 查询所有班级
        stmt = select(
            Class.class_id,
            Class.class_name
        )

        result = db.session.execute(stmt).all()

        # 转换结果为所需格式
        classes = []
        for row in result:
            classes.append({
                "class_id": row.class_id,
                "class_name": row.class_name
            })

        return jsonify({
            "code": 200,
            "message": "success",
            "data": classes
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": []
        })


@admin.route("/classDetail", methods=["GET"])
def getClassDetail():
    """
    查询班级详情
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({
                "code": 400,
                "message": "缺少班级ID",
                "data": None
            })

        # 查询班级信息
        class_info = Class.query.get(class_id)
        if not class_info:
            return jsonify({
                "code": 400,
                "message": "班级不存在",
                "data": None
            })

        # 查询班级教师
        teacher_stmt = select(
            Teacher.teacher_id,
            Teacher.teacher_name
        ).join(TeacherClass, Teacher.teacher_id == TeacherClass.teacher_id
               ).where(TeacherClass.class_id == class_id)

        teachers = []
        for row in db.session.execute(teacher_stmt).all():
            teachers.append({
                "teacher_id": row.teacher_id,
                "name": row.teacher_name
            })

        # 查询班级学生
        student_stmt = select(
            Child.child_id,
            Child.child_name
        ).where(Child.class_id == class_id)

        students = []
        for row in db.session.execute(student_stmt).all():
            students.append({
                "student_id": row.child_id,
                "name": row.child_name
            })

        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "class_id": class_info.class_id,
                "class_name": class_info.class_name,
                "teachers": teachers,
                "students": students
            }
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })


@admin.route("/teacherDetail", methods=["GET"])
def getTeacherDetail():
    """
    查询教师详情
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        teacher_id = request.args.get('teacher_id')
        if not teacher_id:
            return jsonify({
                "code": 400,
                "message": "缺少教师ID",
                "data": None
            })

        # 查询教师信息
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return jsonify({
                "code": 400,
                "message": "教师不存在",
                "data": None
            })

        # 查询教师所授班级
        class_stmt = select(
            Class.class_id,
            Class.class_name
        ).join(TeacherClass, Class.class_id == TeacherClass.class_id
               ).where(TeacherClass.teacher_id == teacher_id)

        classes = []
        for row in db.session.execute(class_stmt).all():
            classes.append({
                "class_id": row.class_id,
                "class_name": row.class_name
            })

        # 判断是否拥有高级权限
        is_set = 1 if teacher.role in ["园长", "管理级教师"] else 0

        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "teacher_id": teacher.teacher_id,
                "name": teacher.teacher_name,
                "contact": teacher.phone,
                "classes": classes,
                "is_set": is_set
            }
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })


@admin.route("/childDetail", methods=["GET"])
def getChildDetail():
    """
    查询儿童详情
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        child_id = request.args.get('child_id')
        if not child_id:
            return jsonify({
                "code": 400,
                "message": "缺少儿童ID",
                "data": None
            })

        # 查询儿童信息
        child = Child.query.get(child_id)
        if not child:
            return jsonify({
                "code": 400,
                "message": "儿童不存在",
                "data": None
            })

        # 查询家长联系方式
        parent_contact = ""
        if child.guardian_id:
            parent = Parent.query.get(child.guardian_id)
            if parent:
                parent_contact = parent.phone

        # 计算入学年份
        enroll_year = child.created_time.year

        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "child_id": child.child_id,
                "name": child.child_name,
                "birthday": child.birth_date,
                "enroll_year": enroll_year,
                "parent_contact": parent_contact
            }
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })


@admin.route("/createClass", methods=["POST"])
def createClass():
    """
    创建班级
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "请求数据格式错误",
                "data": None
            })

        class_name = data.get('class_name')
        teacher_ids = data.get('teacher_ids', [])

        # 参数校验
        if not all([class_name, teacher_ids]):
            return jsonify({
                "code": 400,
                "message": "缺少班级名称或教师ID列表",
                "data": None
            })

        # 校验teacher_ids是否为非空数组
        if not isinstance(teacher_ids, list) or len(teacher_ids) == 0:
            return jsonify({
                "code": 400,
                "message": "教师ID列表必须为非空数组",
                "data": None
            })

        # 检查班级是否已存在
        existing_class = Class.query.filter_by(class_name=class_name).first()
        if existing_class:
            return jsonify({
                "code": 400,
                "message": "班级已存在",
                "data": None
            })

        # 检查教师ID是否存在
        invalid_ids = []
        for tid in teacher_ids:
            teacher = Teacher.query.get(tid)
            if not teacher:
                invalid_ids.append(tid)
        if invalid_ids:
            return jsonify({
                "code": 400,
                "message": f"教师ID不存在: {invalid_ids}",
                "data": None
            })

        # 创建新班级
        new_class = Class(
            class_name=class_name,
            grade='小班',  # 默认值
            student_count=0,
            notes=data.get('notes', ''),
            created_at=datetime.now()
        )
        db.session.add(new_class)
        db.session.flush()  # 获取新班级的ID

        # 关联教师
        for tid in teacher_ids:
            relation = TeacherClass(
                teacher_id=tid,
                class_id=new_class.class_id,
                is_headTeacher=0  # 默认值
            )
            db.session.add(relation)

        db.session.commit()

        return jsonify({
            "code": 0,
            "message": "班级创建成功",
            "data": {
                "class_id": new_class.class_id,
                "class_name": new_class.class_name,
                "teacher_ids": teacher_ids
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })

@admin.route("/deleteClass", methods=["POST"])
def deleteClass():
    """
    删除班级
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求数据格式错误", "data": None})

        # 检查必要参数
        if 'manager_id' not in data or 'class_id' not in data:
            return jsonify({"code": 400, "message": "缺少必要参数", "data": None})

        manager_id = data['manager_id']
        class_id = data['class_id']

        # 检查是否为管理员或园长
        manager_admin = Admin.query.get(manager_id)
        manager_teacher = Teacher.query.get(manager_id)
        has_permission = False
        if manager_admin:
            has_permission = True
        elif manager_teacher and manager_teacher.role in ["园长", "管理级教师"]:
            has_permission = True

        if not has_permission:
            return jsonify({"code": 400, "message": "没有操作权限", "data": None})

        # 查找班级
        class_info = Class.query.get(class_id)
        if not class_info:
            return jsonify({"code": 400, "message": "班级不存在", "data": None})

        # 删除班级内的学生
        Child.query.filter_by(class_id=class_id).delete()

        # 删除班级与教师的关联
        TeacherClass.query.filter_by(class_id=class_id).delete()

        # 删除班级
        db.session.delete(class_info)
        db.session.commit()

        return jsonify({"code": 200, "message": "班级删除成功", "data": {"class_id": class_id}})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 400, "message": f"服务器错误: {str(e)}", "data": None})

@admin.route("/addTeacherToClass", methods=["POST"])
def addTeacherToClass():
    """
    为班级添加教师
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        data = request.get_json()
        if not data or not data.get('class_id') or not data.get('teacher_id'):
            return jsonify({
                "code": 400,
                "message": "缺少班级ID或教师ID",
                "data": None
            })

        class_id = data.get('class_id')
        teacher_id = data.get('teacher_id')
        is_headTeacher = data.get('is_headTeacher', 0)

        # 检查班级和教师是否存在
        class_info = Class.query.get(class_id)
        teacher = Teacher.query.get(teacher_id)

        if not class_info:
            return jsonify({
                "code": 400,
                "message": "班级不存在",
                "data": None
            })

        if not teacher:
            return jsonify({
                "code": 400,
                "message": "教师不存在",
                "data": None
            })

        # 检查关联是否已存在
        existing_relation = TeacherClass.query.filter_by(
            teacher_id=teacher_id,
            class_id=class_id
        ).first()

        if existing_relation:
            return jsonify({
                "code": 400,
                "message": "教师已在该班级",
                "data": None
            })

        # 创建新关联
        new_relation = TeacherClass(
            teacher_id=teacher_id,
            class_id=class_id,
            is_headTeacher=is_headTeacher
        )

        db.session.add(new_relation)
        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "教师添加成功",
            "data": {
                "class_id": class_id,
                "teacher_id": teacher_id
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })


@admin.route("/removeTeacherFromClass", methods=["POST"])
def removeTeacherFromClass():
    """
    为班级删除教师
    """
    try:
        # --- Token验证逻辑 ---
        manager_id = request.args.get('manager_id')
        uniquetoken = request.args.get('uniquetoken')

        if not all([manager_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数"})

        user, role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user or role != 'admin':
            return jsonify({"code": 403, "message": "Token无效或权限不足"})
        # --- 验证结束 ---
        data = request.get_json()
        if not data or not data.get('class_id') or not data.get('teacher_id'):
            return jsonify({
                "code": 400,
                "message": "缺少班级ID或教师ID",
                "data": None
            })

        class_id = data.get('class_id')
        teacher_id = data.get('teacher_id')

        # 检查关联是否存在
        relation = TeacherClass.query.filter_by(
            teacher_id=teacher_id,
            class_id=class_id
        ).first()

        if not relation:
            return jsonify({
                "code": 400,
                "message": "教师不在该班级",
                "data": None
            })

        # 删除关联
        db.session.delete(relation)
        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "教师移除成功",
            "data": {
                "class_id": class_id,
                "teacher_id": teacher_id
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": None
        })
