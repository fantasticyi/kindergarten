import os

from flask import request, jsonify, make_response, send_file, current_app
from datetime import datetime, date, timedelta
from . import teacher
from ..models import db, Child, Dq, QuizInfo, TestDetail, TeacherClass, Teacher, Class, Parent, Admin, Game

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from ..auth import verify_token_and_get_user

@teacher.route("/changeRole", methods=["POST"])
def changeRole():
    # 获取请求参数
    data = request.get_json()
    teacher_id = data.get("teacher_id")
    manager_id = data.get("manager_id")
    is_set = data.get("is_set")
    uniquetoken = data.get('uniquetoken')  # 新增：获取uniquetoken

    # 参数校验
    if not all([teacher_id, manager_id, is_set is not None]):
        return jsonify({"code": 400, "message": "参数不完整", "data": []})

    try:
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
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

        # 检查是否尝试修改自己的角色
        if teacher_id == manager_id:
            return jsonify({"code": 400, "message": "没有操作权限", "data": []})

        # 获取要修改的教师
        t = Teacher.query.get(teacher_id)
        if not t:
            return jsonify({"code": 400, "message": "教师不存在", "data": []})

        # 根据is_set值修改角色
        if is_set == 1:
            t.role = "管理级教师"
        elif is_set == 0:
            t.role = ""
        else:
            return jsonify({"code": 400, "message": "参数is_set值无效", "data": []})

        # 提交到数据库
        db.session.commit()

        return jsonify({"code": 200, "message": "角色修改成功", "data": []})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 400, "message": f"服务器错误: {str(e)}", "data": []})


@teacher.route("/changeChildClass", methods=["POST"])
def changeChildClass():
    # 获取请求参数
    data = request.get_json()
    child_id = data.get("child_id")
    class_id = data.get("class_id")
    manager_id = data.get("manager_id")
    uniquetoken = data.get('uniquetoken')  # 新增：获取uniquetoken
    # 验证必要参数是否存在
    if not all([child_id, class_id, manager_id]):
        return jsonify({"code": 400, "message": "缺少必要参数", "data": []})

    try:

        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # 1. 检查园长权限，再检查管理员权限
        manager_teacher = Teacher.query.get(manager_id)
        manager_admin = Admin.query.get(manager_id)
        has_permission = False
        if manager_teacher and manager_teacher.role == "园长":
            has_permission = True
        elif manager_admin:
            has_permission = True

        if not has_permission:
            return jsonify({"code": 400, "message": "没有操作权限", "data": []})

        # 2. 检查孩子是否存在
        child = Child.query.get(child_id)
        if not child:
            return jsonify({"code": 400, "message": "孩子不存在", "data": []})

        # 3. 检查班级是否存在
        new_class = Class.query.get(class_id)
        if not new_class:
            return jsonify({"code": 400, "message": "班级不存在", "data": []})

        # 4. 检查孩子是否已经在目标班级
        if child.class_id == class_id:
            return jsonify({"code": 400, "message": "孩子已在目标班级", "data": []})

        # 5. 执行班级变更
        child.class_id = class_id
        db.session.commit()

        return jsonify({"code": 200, "message": "success", "data": []})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 400, "message": f"服务器错误: {str(e)}", "data": []})


@teacher.route("/changeTeacherClass", methods=["POST"])
def changeTeacherClass():
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    class_info = data.get('class_id', [])  # [[class_id, is_headTeacher], ...]
    manager_id = data.get('manager_id')
    uniquetoken = data.get('uniquetoken')

    # 1. 参数验证
    if not all([teacher_id, class_info, manager_id is not None]):
        return jsonify({"code": 400, "message": "缺少必要参数", "data": []})

    try:

        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # 2. 检查园长权限，再检查管理员权限
        manager_teacher = Teacher.query.get(manager_id)
        manager_admin = Admin.query.get(manager_id)
        has_permission = False
        if manager_teacher and manager_teacher.role == "园长":
            has_permission = True
        elif manager_admin:
            has_permission = True

        if not has_permission:
            return jsonify({"code": 400, "message": "没有操作权限", "data": []})

        # 3. 检查老师和班级是否存在
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return jsonify({"code": 400, "message": "老师不存在", "data": []})

        # 检查所有班级是否存在
        class_ids = [item[0] for item in class_info]
        existing_classes = Class.query.filter(Class.class_id.in_(class_ids)).all()
        if len(existing_classes) != len(class_ids):
            return jsonify({"code": 400, "message": "部分班级不存在", "data": []})

        # 4. 删除老师原有的班级关联
        TeacherClass.query.filter_by(teacher_id=teacher_id).delete()

        # 5. 添加新的班级关联
        new_relations = [
            TeacherClass(
                teacher_id=teacher_id,
                class_id=item[0],
                is_headTeacher=item[1]
            )
            for item in class_info
        ]
        db.session.bulk_save_objects(new_relations)

        db.session.commit()
        return jsonify({"code": 200, "message": "success", "data": []})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 400, "message": f"服务器错误: {str(e)}", "data": []})


@teacher.route("/changeClassName", methods=["POST"])
def changeClassName():
    # 获取请求参数
    data = request.get_json()
    class_id = data.get('class_id')
    new_class_name = data.get('class_name')
    manager_id = data.get('manager_id')
    uniquetoken = data.get('uniquetoken')

    # 参数校验
    if not all([class_id, new_class_name, manager_id]):
        return jsonify({"code": 400, "message": "缺少必要参数", "data": []})

    try:
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(manager_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # 1. 检查班级是否存在
        class_to_update = Class.query.get(class_id)
        if not class_to_update:
            return jsonify({"code": 400, "message": "班级不存在", "data": []})



        # 2. 检查园长权限，再检查管理员权限
        manager_teacher = Teacher.query.get(manager_id)
        manager_admin = Admin.query.get(manager_id)
        has_permission = False
        if manager_teacher and manager_teacher.role == "园长":
            has_permission = True
        elif manager_admin:
            has_permission = True

        if not has_permission:
            return jsonify({"code": 400, "message": "没有操作权限", "data": []})

        # 3. 更新班级名称
        class_to_update.class_name = new_class_name
        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "success",
            "data": []
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"服务器错误: {str(e)}",
            "data": []
        })


@teacher.route("/getClass", methods=["GET"])
def getClass():
    # 获取前端发送的JSON数据
    teacher_id = request.args.get('teacher_id')
    uniquetoken = request.args.get('uniquetoken')
    try:
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # 查询Teacher_Class表中该teacher_id对应的所有记录
        teacher_classes = TeacherClass.query.filter_by(teacher_id=teacher_id).all()

        # 获取所有关联班级的详细信息
        class_list = []
        for tc in teacher_classes:
            class_info = Class.query.get(tc.class_id)
            if class_info:
                class_list.append({
                    "class_id": class_info.class_id,
                    "class_name": class_info.class_name
                })

        # 加入体验班，因为每个老师都能测试体验班(class_id=1)
        experience_class = Class.query.get(1)
        if experience_class:
            class_list.append({
                "class_id": experience_class.class_id,
                "class_name": experience_class.class_name
            })

        return jsonify({
            "code": 200,
            "message": "成功获取班级信息",
            "data": class_list
        })
    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"获取班级信息失败: {str(e)}",
            "data": []
        })


@teacher.route("/getClassChild", methods=["GET"])
def getChild():
    class_id = request.args.get('class_id')
    teacher_id = request.args.get('teacher_id')
    uniquetoken = request.args.get('uniquetoken')
    try:
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # Query to get all students in the specified class
        students = Child.query.filter_by(class_id=class_id).all()

        # Create a list of student dictionaries with id and name
        student_list = [{"id": student.child_id, "name": student.child_name} for student in students]

        return jsonify({
            "code": 200,
            "message": "成功获取班级内学生信息",
            "data": student_list
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"获取班级内学生信息失败: {str(e)}",
            "data": []
        })


@teacher.route("/test", methods=["POST"])
def test():
    try:
        teacher_id = request.args.get('teacher_id')
        uniquetoken = request.args.get('uniquetoken')
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---

        # 获取前端发送的JSON数据
        data = request.get_json()
        child_id = data["child_id"]
        # child_id = request.args.get('child_id')

        # 获取该学生对象
        child = Child.query.get(child_id)
        if not child:
            raise ValueError("Child not found")

        # 计算当前月龄（精确到1位小数）
        birth_date = child.birth_date
        today = date.today()
        
        # 计算年、月、日差值
        years = today.year - birth_date.year
        months = today.month - birth_date.month
        days = today.day - birth_date.day
        
        # 处理日期不够减
        if days < 0:
            months -= 1
            # 获取上个月的天数
            last_month = today.month - 1 if today.month > 1 else 12
            last_month_year = today.year if today.month > 1 else today.year - 1
            last_month_days = (date(last_month_year, last_month + 1, 1) - date(last_month_year, last_month, 1)).days
            days += last_month_days
        
        # 处理月份不够减
        if months < 0:
            years -= 1
            months += 12
        
        # 总月龄 = 年×12 + 月 + 日/30（按30天折算为月）
        total_months = years * 12 + months + days / 30.0
        month_age = round(max(total_months, 0.1), 1)  # 最小0.1月龄，避免0或负数

        if not Dq.query.filter_by(child_id=child_id).all():
            score = [0, 0, 0, 0, 0]
        else:
            # 查询该学生最近一次测试（按日期降序排列取第一条）
            latest_test = Dq.query.filter_by(child_id=child_id).order_by(Dq.date.desc()).first()
            score = [
                latest_test.gross_motor_score,
                latest_test.fine_motor_score,
                latest_test.language_score,
                latest_test.adaptability_score,
                latest_test.social_score
            ]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "score": score,
                "month_age": month_age
            }
        }

    except Exception as e:
        db.session.rollback()
        return {
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": []
        }


@teacher.route("/getQuiz", methods=["GET"])
def getQuiz():
    try:
        # 请求参数
        project = request.args.get('project')
        month_age = int(request.args.get('month_age'))
        is_forward = int(request.args.get('is_forward'))
        teacher_id = request.args.get('teacher_id')
        uniquetoken = request.args.get('uniquetoken')
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---
        # 更新月份
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 18, 21, 24, 27, 30, 33, 36, 42, 48, 54, 60, 66, 72, 78, 84]
        new_month_age = month_age
        for index, month in enumerate(months):
            if month_age == month:
                if is_forward == 1:
                    if month_age == 84:
                        new_month_age = 84
                    else:
                        new_month_age = months[index + 1]
                elif is_forward == -1:
                    if month_age == 1:
                        new_month_age = 1
                    else:
                        new_month_age = months[index - 1]
                break
            elif month < month_age < months[index + 1]:
                new_month_age = month
                break

        # 查询题目
        projectToNum = {'gross_motor': 1, 'fine_motor': 2, 'language': 3, 'adaptability': 4, 'social': 5}
        quizzes = QuizInfo.query.filter_by(
            month_age=new_month_age,
            sort=projectToNum[project]
        ).order_by(QuizInfo.quiz_id).all()  # 按 quiz_id 排序确保顺序一致

        # 构建返回数据
        result = [
            {
                "quiz_id": quiz.quiz_id,
                "quiz_name": quiz.quiz_name,
                "quiz_method": quiz.quiz_method,
                "pass_need": quiz.pass_need
            }
            for quiz in quizzes
        ]

        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "month_age": new_month_age,
                "quiz": result
            }
        })

    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": []
        })


def generate_report(base_info, dq_id, dqs, dq, grade):
    # 注册中文字体（确保系统有该字体或提供字体文件路径）
    try:
        pdfmetrics.registerFont(TTFont('SimSun', 'font/SimSun.ttf'))  # 宋体
        pdfmetrics.registerFont(TTFont('SimHei', 'font/SimHei.ttf'))  # 黑体
    except:
        print("警告：未找到中文字体，可能显示异常")

    # 创建PDF文档
    doc = SimpleDocTemplate(f"pdf/report_{dq_id}.pdf", pagesize=A4)
    url = f"https://kindergarten-177863-9-1372785009.sh.run.tcloudbase.com/teacher/getPdf?dq_id={dq_id}"
    teacher_id = request.args.get('teacher_id')
    uniquetoken = request.args.get('uniquetoken')
    # --- 新增的Token验证逻辑 ---
    user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
    if not user:
        return jsonify({
            "code": 403,
            "message": "Token mismatch, potential new device login.",
            "data": None
        })
    # --- Token验证结束 ---
    # 自定义样式
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName='SimHei',
        fontSize=18,
        leading=24,
        alignment=1,  # 居中
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='ReportHeading2',
        fontName='SimHei',
        fontSize=14,
        leading=18,
        alignment=0,  # 左对齐
        spaceBefore=20,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='ReportBodyText',
        fontName='SimSun',
        fontSize=12,
        leading=16,
        alignment=0,
        firstLineIndent=24,
        spaceAfter=6
    ))

    # 准备内容元素
    elements = []

    # 1. 一级标题
    elements.append(Paragraph("儿童发育行为测评报告", styles['ReportTitle']))

    # 2. 一、基本信息 - 二级标题
    elements.append(Paragraph("一、基本信息", styles['ReportHeading2']))

    # 3. 基本信息表格
    basic_info_data = [
        ["项目", "内容"],
        ["姓名", base_info['child_name']],
        ["性别", base_info['child_gender']],
        ["出生日期", base_info['birth_date']],
        ["测评日期", base_info['test_date']],
        ["实际月龄", base_info['month_age']],
        ["主测月龄", base_info['test_age']],
        ["测评工具", "《0～6岁儿童发育行为评估量表（WS/T 580—2017）》"],
        ["测评人员", base_info['teacher_name']]
    ]

    basic_info_table = Table(basic_info_data, colWidths=[3 * cm, 12 * cm])
    basic_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'SimSun'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOLD', (0, 0), (-1, 0), True),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(basic_info_table)

    # 4. 二、测评结果汇总 - 二级标题
    elements.append(Paragraph("二、测评结果汇总", styles['ReportHeading2']))

    # 5. 测评结果表格
    child_month_age = base_info['month_age']
    result_data = [
        ["能区", "智龄", "实际月龄", "发育商（DQ）"],
        ["大运动", dqs[0], child_month_age, round(dqs[0] / child_month_age * 100, 1)],
        ["精细动作", dqs[1], child_month_age, round(dqs[1] / child_month_age * 100, 1)],
        ["适应能力", dqs[2], child_month_age, round(dqs[2] / child_month_age * 100, 1)],
        ["语言", dqs[3], child_month_age, round(dqs[3] / child_month_age * 100, 1)],
        ["社会行为", dqs[4], child_month_age, round(dqs[4] / child_month_age * 100, 1)],
        ["总计", round(sum(dqs) / 5, 1), child_month_age, dq]
    ]

    result_table = Table(result_data, colWidths=[4 * cm, 3 * cm, 3 * cm, 4 * cm])
    result_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'SimSun'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOLD', (0, 0), (-1, 0), True),
        ('BOLD', (0, -1), (-1, -1), True),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(result_table)

    # 6. 三、发育等级判定 - 二级标题
    elements.append(Paragraph("三、发育等级判定", styles['ReportHeading2']))

    # 7. 发育等级表格
    level_data = [
        ["等级", "发育商范围"],
        ["优秀", "＞130"],
        ["良好", "110～129"],
        ["中等", "80～109"],
        ["临界偏低", "70～79"],
        ["发育障碍（低）", "＜70"]
    ]

    level_table = Table(level_data, colWidths=[5 * cm, 5 * cm])
    level_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'SimSun'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOLD', (0, 0), (-1, 0), True),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(level_table)
    elements.append(Spacer(width=0, height=20))
    elements.append(Paragraph(f"孩子的评级为: {grade}", styles['ReportBodyText']))

    # 8. 四、分析与建议 - 二级标题
    elements.append(Paragraph("四、分析与建议", styles['ReportHeading2']))
    # 具体内容待完成

    # 构建PDF文档
    doc.build(elements)
    print("PDF生成完成.")
    return url


@teacher.route("/recordScore", methods=["POST"])
def record():
    try:
        # 获取前端发送的JSON数据
        data = request.get_json()
        child_id = int(data["child_id"])
        teacher_id = int(data["teacher_id"])
        maxPass_month = data["maxPass_month"]
        answer_set = data["answer_set"]

        uniquetoken = request.args.get('uniquetoken')
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---
        # 获取该学生对象
        child = Child.query.get(child_id)
        if not child:
            raise ValueError("Child not found")
        # 获取老师对象
        t = Teacher.query.get(teacher_id)
        if not t:
            raise ValueError("Teacher not found")

        # 计算实际月龄
        birth_date = child.birth_date
        today = datetime.now()
        child_month_age = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
        if today.day < birth_date.day:
            child_month_age -= 1
        child_month_age = max(child_month_age, 1)  # 确保月龄 >= 1

        # 计算主测月龄（找一个最接近但不大于实际月龄的月龄）
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 18, 21, 24, 27, 30, 33, 36, 42, 48, 54, 60, 66, 72, 78, 84]
        test_age = child_month_age
        if child_month_age >= months[-1]:
            test_age = months[-1]
        else:
            for index, month in enumerate(months):
                if child_month_age == month:
                    break
                elif month < child_month_age < months[index + 1]:
                    test_age = month
                    break

        # 测评报告的基本信息
        base_info = {
            "child_name": child.child_name,
            "child_gender": child.gender,
            "birth_date": child.birth_date.strftime("%Y-%m-%d"),
            "test_date": datetime.now().strftime("%Y-%m-%d"),
            "month_age": child_month_age,
            "test_age": test_age,
            "teacher_name": t.teacher_name,
        }

        # 存储五种项目各自的智龄，初始值为 最大连续通过月份
        dqs = maxPass_month

        # 五个项目所有的测试月龄的题目数量：1道/2道
        test_num = [[2, 2, 2, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 2, 1, 1, 2,
                     1, 2, 1, 1, 1,
                     2, 2, 2, 2, 2,
                     2, 2, 2],
                    [2, 2, 2, 2, 2,
                     2, 2, 2, 2, 1,
                     1, 2, 2, 1, 2,
                     1, 2, 2, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 2, 2],
                    [2, 2, 2, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 1, 2, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 2, 2],
                    [2, 2, 1, 2, 1,
                     2, 1, 2, 2, 1,
                     2, 2, 2, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 2, 2],
                    [2, 2, 2, 2, 2,
                     2, 2, 1, 1, 2,
                     2, 2, 1, 2, 2,
                     2, 2, 2, 2, 2,
                     2, 2, 2, 1, 2,
                     2, 2, 2]]

        # 计算五种项目的分数
        for index, project in enumerate(answer_set):
            for answer in project:
                is_pass = int(answer["is_pass"])
                month = int(answer["month"])
                index2 = months.index(month)
                if 1 <= month <= 12:
                    ratio = 1
                elif 15 <= month <= 36:
                    ratio = 3
                elif 42 <= month <= 84:
                    ratio = 6
                else:
                    raise ValueError("月龄越界")
                dqs[index] += is_pass * ratio * (1 / test_num[index][index2])

        # 计算dq
        dq = round(sum(dqs) / 5, 1) / child_month_age * 100

        # 发育等级
        grade = "智力发育障碍"
        if dq > 130:
            grade = "优秀"
        elif dq >= 110:
            grade = "良好"
        elif dq >= 80:
            grade = "中等"
        elif dq >= 70:
            grade = "临界偏低"

        # 插入Dq表，获取dq_id
        new_dq = Dq(
            teacher_id=teacher_id,
            child_id=child_id,
            month_age=child_month_age,
            gross_motor_score=dqs[0],
            fine_motor_score=dqs[1],
            language_score=dqs[2],
            adaptability_score=dqs[3],
            social_score=dqs[4],
            dq=dq,
            date=datetime.now() + timedelta(hours=8)
        )
        db.session.add(new_dq)
        db.session.flush()
        dq_id = new_dq.dq_id

        # 插入TestDetail
        for index, project in enumerate(answer_set):
            for answer in project:
                quiz_id = int(answer["quiz_id"])
                is_pass = int(answer["is_pass"])
                test_detail = TestDetail(dq_id=dq_id, quiz_id=quiz_id, is_pass=is_pass)
                db.session.add(test_detail)
        db.session.commit()

        # 生成测评报告, 并将url存入Dq表
        pdf_url = generate_report(base_info, dq_id, dqs, dq, grade)
        dq_report = Dq.query.get(dq_id)
        if dq_report:
            dq_report.pdf_path = pdf_url
            db.session.commit()
        else:
            return {"code": 400, "message": "未找到测试记录", "data": []}

        # 返回成功响应
        return {
            "code": 200,
            "message": "success",
            "data": {
                "dq_id": dq_id
            }
        }

    except Exception as e:
        db.session.rollback()
        return {"code": 400, "message": f"错误: {str(e)}", "data": []}


@teacher.route('/getPdf', methods=['GET'])
def getPdf():
    try:
        teacher_id = request.args.get('teacher_id')
        uniquetoken = request.args.get('uniquetoken')
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"服务器错误: {str(e)}",
            "data": None
        })
    dq_id = request.args.get('dq_id')

    project_root = os.path.dirname(current_app.root_path)
    filename = f"report_{dq_id}.pdf"
    filepath = os.path.join(project_root, "pdf", filename)

    if not os.path.exists(filepath):
        return {"code": 400, "message": "file not found", "data": []}

    response = make_response(send_file(filepath))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={filename}'
    return response


@teacher.route("/getChildTestRecord", methods=["GET"])
def getChildTestRecord():
    try:
        child_id = request.args.get('child_id')
        tests = Dq.query.filter_by(child_id=child_id).all()
        testRecord = []
        if tests:
            testRecord = [{"dq_id": t.dq_id, "date": t.date, "dq": t.dq} for t in tests]
        return jsonify({
            "code": 200,
            "message": "success",
            "data": testRecord
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 400,
            "message": f"错误: {str(e)}",
            "data": []
        })


@teacher.route("/getTestDetail", methods=["GET"])
def getTestDetail():
    try:
        dq_id = request.args.get('dq_id')
        teacher_id = request.args.get('teacher_id')
        uniquetoken = request.args.get('uniquetoken')
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---
        dq = Dq.query.get(dq_id)
        if not dq:
            raise ValueError("Dq not found")

        # 重复代码
        teacher_id = dq.teacher_id
        child_id = dq.child_id

        # 获取该学生对象
        child = Child.query.get(child_id)
        if not child:
            raise ValueError("Child not found")
        # 获取老师对象
        t = Teacher.query.get(teacher_id)
        if not teacher:
            raise ValueError("Child not found")

        # 计算当前月龄（精确到1位小数）
        birth_date = child.birth_date
        today = date.today()
        
        # 计算年、月、日差值
        years = today.year - birth_date.year
        months = today.month - birth_date.month
        days = today.day - birth_date.day
        
        # 处理日期不够减
        if days < 0:
            months -= 1
            # 获取上个月的天数
            last_month = today.month - 1 if today.month > 1 else 12
            last_month_year = today.year if today.month > 1 else today.year - 1
            last_month_days = (date(last_month_year, last_month + 1, 1) - date(last_month_year, last_month, 1)).days
            days += last_month_days
        
        # 处理月份不够减
        if months < 0:
            years -= 1
            months += 12
        
        # 总月龄 = 年×12 + 月 + 日/30（按30天折算为月）
        total_months = years * 12 + months + days / 30.0
        child_month_age = round(max(total_months, 0.1), 1)  # 最小0.1月龄，避免0或负数

        # 计算主测月龄（找一个最接近但不大于实际月龄的月龄）
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 18, 21, 24, 27, 30, 33, 36, 42, 48, 54, 60, 66, 72, 78, 84]
        test_age = child_month_age
        if child_month_age > months[-1]:
            test_age = months[-1]
        else:
            for index, month in enumerate(months):
                if child_month_age == month:
                    break
                elif month < child_month_age < months[index + 1]:
                    test_age = month
                    break

        # 测评报告的基本信息
        base_info = {
            "child_name": child.child_name,
            "child_gender": child.gender,
            "birth_date": child.birth_date.strftime("%Y-%m-%d"),
            "test_date": datetime.now().strftime("%Y-%m-%d"),
            "month_age": child_month_age,
            "test_age": test_age,
            "test_tool": "《0～6岁儿童发育行为评估量表（WS/T 580—2017）》",
            "teacher_name": t.teacher_name,
        }

        # 智龄
        dqs = [dq.gross_motor_score, dq.fine_motor_score, dq.language_score, dq.adaptability_score,
               dq.social_score]
        intelligence_age = [dqs[0], dqs[1], dqs[2], dqs[3], dqs[4], round(sum(dqs) / 5, 1)]

        # 发育商
        dq2 = [round(item / child_month_age * 100, 1) for item in dqs]
        dq2.append(dq.dq)

        # 发育等级
        grade = "智力发育障碍"
        if dq.dq > 130:
            grade = "优秀"
        elif dq.dq >= 110:
            grade = "良好"
        elif dq.dq >= 80:
            grade = "中等"
        elif dq.dq >= 70:
            grade = "临界偏低"

        projects = [
            {
                "project": "gross_motor",
                "score_field": "gross_motor_score"
            },
            {
                "project": "fine_motor",
                "score_field": "fine_motor_score"
            },
            {
                "project": "language",
                "score_field": "language_score"
            },
            {
                "project": "adaptability",
                "score_field": "adaptability_score"
            },
            {
                "project": "social",
                "score_field": "social_score"
            }
        ]

        result = []

        for project in projects:
            quiz_items = (
                db.session.query(QuizInfo, TestDetail.is_pass)
                .join(TestDetail, QuizInfo.quiz_id == TestDetail.quiz_id)
                .filter(
                    TestDetail.dq_id == dq_id,
                    QuizInfo.sort == projects.index(project) + 1  # sort starts at 1
                )
                .all()
            )

            quiz_list = []
            for quiz_info, is_pass in quiz_items:
                quiz_list.append({
                    "quiz_id": quiz_info.quiz_id,
                    "quiz_name": quiz_info.quiz_name,
                    "quiz_method": quiz_info.quiz_method,
                    "pass_need": quiz_info.pass_need,
                    "is_pass": is_pass
                })

            # Add to result
            result.append({
                "project": project["project"],
                "score": getattr(dq, project["score_field"]),
                "quiz_list": quiz_list
            })
        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "baseInfo": base_info,
                "score": {
                    "intelligence_age": intelligence_age,
                    "full": [child_month_age] * 5,
                    "dq": dq2,
                    "grade": grade,
                    "pdf_url": dq.pdf_path
                },
                "detail": result
            }
        })

    except Exception as e:
        return jsonify({"code": 400, "message": f"错误: {str(e)}", "data": []})


@teacher.route("/recommendGame", methods=["GET"])
def recommendGame():
    try:
        teacher_id = request.args.get('teacher_id')
        uniquetoken = request.args.get('uniquetoken')
        # --- 新增的Token验证逻辑 ---
        user, user_role = verify_token_and_get_user(teacher_id, uniquetoken)
        if not user:
            return jsonify({
                "code": 403,
                "message": "Token mismatch, potential new device login.",
                "data": None
            })
        # --- Token验证结束 ---
        game_sort = int(request.args.get('sort'))
        month_age = int(request.args.get('month_age'))

        if game_sort not in (1, 2, 3, 4, 5):
            return jsonify({'code': 400, 'message': 'Invalid game sort value. Must be between 1 and 5.'})

        games = Game.query.filter(
            Game.game_sort == game_sort,
            Game.game_beginTime <= month_age,
            Game.game_endTime >= month_age
        ).all()

        game_list = [{
            'game_name': game.game_name,
            'game_sort': game.game_sort,
            'game_beginTime': game.game_beginTime,
            'game_endTime': game.game_endTime,
            'game_bg': game.game_bg,
            'game_prepare': game.game_prepare,
            'game_purpose': game.game_purpose,
            'game_process': game.game_process,
            'cautions': game.cautions
        } for game in games]

        return jsonify({'code': 200, 'message': 'success', 'data': game_list})

    except Exception as e:
        return jsonify({"code": 400, "message": f"错误: {str(e)}", "data": []})


@teacher.route("/addAdmin", methods=["GET"])
def addAdmin():
    try:
        # 从URL查询参数中获取操作者的ID和token
        teacher_id = request.args.get('teacher_id')
        uniquetoken = request.args.get('uniquetoken')

        # 检查必要参数是否存在
        if not all([teacher_id, uniquetoken]):
            return jsonify({"code": 400, "message": "缺少必要参数: teacher_id 和 uniquetoken"})

        # --- Token验证逻辑 ---
        # 调用验证函数，验证操作者身份和token
        user, role = verify_token_and_get_user(teacher_id, uniquetoken)

        # 验证失败或权限不足（必须是 'admin' 角色）
        if not user or role != 'admin':
            return jsonify({
                "code": 403,
                "message": "Token无效或权限不足",
                "data": None
            })
        # --- Token验证结束 ---

        # 验证通过，继续执行原始的数据插入逻辑
    except Exception as e:
        db.session.rollback()
        print(f"插入数据时出错: {e}")
    """创建指定数量的伪造教师数据"""
    admin_data = [
        ('admin123', '13800000000')
    ]

    admins = []
    for password, phone in admin_data:
        a = Admin(phone=phone)
        a.set_password(password)
        admins.append(a)

    db.session.add_all(admins)
    try:
        db.session.commit()
        print(f"成功插入 {len(admins)} 条管理员数据")
    except Exception as e:
        db.session.rollback()
        print(f"插入数据时出错: {e}")


@teacher.route("/addTeacher", methods=["GET"])
def addTeacher():
    # 从URL查询参数中获取操作者的ID和token
    teacher_id = request.args.get('teacher_id')
    uniquetoken = request.args.get('uniquetoken')

    # 检查必要参数是否存在
    if not all([teacher_id, uniquetoken]):
        return jsonify({"code": 400, "message": "缺少必要参数: teacher_id 和 uniquetoken"})

    # --- Token验证逻辑 ---
    # 调用验证函数，验证操作者身份和token
    user, role = verify_token_and_get_user(teacher_id, uniquetoken)

    # 验证失败或权限不足（必须是 'admin' 角色）
    if not user or role != 'admin':
        return jsonify({
            "code": 403,
            "message": "Token无效或权限不足",
            "data": None
        })
    # --- Token验证结束 ---
    """创建指定数量的伪造教师数据"""
    teacher_data = [
        ('刘园长', '13900000000', 'teacher123', '园长'),
        ('张老师', '13900000001', 'teacher123', ''),
        ('李老师', '13900000002', 'teacher123', ''),
        ('王老师', '13900000003', 'teacher123', ''),
        ('赵老师', '13900000004', 'teacher123', ''),
        ('刘老师', '13900000005', 'teacher123', ''),
        ('陈老师', '13900000006', 'teacher123', '')
    ]

    teachers = []
    for name, phone, password, role in teacher_data:
        t = Teacher(
            teacher_name=name,
            phone=phone,
            created_time=datetime.utcnow(),
            role=role
        )
        t.set_password(password)
        teachers.append(t)

    db.session.add_all(teachers)
    try:
        db.session.commit()
        print(f"成功插入 {len(teachers)} 条教师数据")
    except Exception as e:
        db.session.rollback()
        print(f"插入数据时出错: {e}")


@teacher.route("/addTeacherClass", methods=["GET"])
def addTeacherClass():
    # 从URL查询参数中获取操作者的ID和token
    teacher_id = request.args.get('teacher_id')
    uniquetoken = request.args.get('uniquetoken')

    # 检查必要参数是否存在
    if not all([teacher_id, uniquetoken]):
        return jsonify({"code": 400, "message": "缺少必要参数: teacher_id 和 uniquetoken"})

    # --- Token验证逻辑 ---
    # 调用验证函数，验证操作者身份和token
    user, role = verify_token_and_get_user(teacher_id, uniquetoken)

    # 验证失败或权限不足（必须是 'admin' 角色）
    if not user or role != 'admin':
        return jsonify({
            "code": 403,
            "message": "Token无效或权限不足",
            "data": None
        })
    # --- Token验证结束 ---
    """创建指定数量的伪造教师-班级数据"""
    teacher_class_data = [
        (1, 2, 1),
        (2, 2, 0),
        (3, 3, 1),
        (4, 3, 0),
        (5, 4, 1),
        (6, 4, 0)
    ]

    teacher_class = []
    for teacher_id, class_id, is_headTeacher in teacher_class_data:
        tc = TeacherClass(
            teacher_id=teacher_id,
            class_id=class_id,
            is_headTeacher=is_headTeacher
        )
        teacher_class.append(tc)

    db.session.add_all(teacher_class)
    try:
        db.session.commit()
        print(f"成功插入 {len(teacher_class)} 条教师-班级数据")
    except Exception as e:
        db.session.rollback()
        print(f"插入数据时出错: {e}")


@teacher.route("/addParent", methods=["GET"])
def addParent():
    # 从URL查询参数中获取操作者的ID和token
    teacher_id = request.args.get('teacher_id')
    uniquetoken = request.args.get('uniquetoken')

    # 检查必要参数是否存在
    if not all([teacher_id, uniquetoken]):
        return jsonify({"code": 400, "message": "缺少必要参数: teacher_id 和 uniquetoken"})

    # --- Token验证逻辑 ---
    # 调用验证函数，验证操作者身份和token
    user, role = verify_token_and_get_user(teacher_id, uniquetoken)

    # 验证失败或权限不足（必须是 'admin' 角色）
    if not user or role != 'admin':
        return jsonify({
            "code": 403,
            "message": "Token无效或权限不足",
            "data": None
        })
    # --- Token验证结束 ---
    """创建指定数量的伪造家长数据"""
    parent_data = [
        ('13800000001', 'parent123'),
        ('13800000002', 'parent123'),
        ('13800000003', 'parent123'),
        ('13800000004', 'parent123'),
        ('13800000005', 'parent123'),
        ('13800000006', 'parent123'),
        ('13800000007', 'parent123'),
        ('13800000008', 'parent123'),
        ('13800000009', 'parent123'),
        ('13800000010', 'parent123'),
        ('13800000011', 'parent123'),
        ('13800000012', 'parent123'),
        ('13800000013', 'parent123'),
        ('13800000014', 'parent123'),
        ('13800000015', 'parent123'),
        ('13800000016', 'parent123'),
        ('13800000017', 'parent123'),
        ('13800000018', 'parent123'),
        ('13800000019', 'parent123'),
        ('13800000020', 'parent123'),
        ('13800000021', 'parent123'),
        ('13800000022', 'parent123'),
        ('13800000023', 'parent123'),
        ('13800000024', 'parent123'),
        ('13800000025', 'parent123'),
        ('13800000026', 'parent123'),
        ('13800000027', 'parent123'),
        ('13800000028', 'parent123'),
        ('13800000029', 'parent123'),
        ('13800000030', 'parent123')
    ]

    parents = []
    for phone, password in parent_data:
        p = Parent(
            phone=phone
        )
        p.set_password(password)
        parents.append(p)

    db.session.add_all(parents)
    try:
        db.session.commit()
        print(f"成功插入 {len(parents)} 条家长数据")
    except Exception as e:
        db.session.rollback()
        print(f"插入数据时出错: {e}")


@teacher.route("/addChild", methods=["GET"])
def addChild():
    # 从URL查询参数中获取操作者的ID和token
    teacher_id = request.args.get('teacher_id')
    uniquetoken = request.args.get('uniquetoken')

    # 检查必要参数是否存在
    if not all([teacher_id, uniquetoken]):
        return jsonify({"code": 400, "message": "缺少必要参数: teacher_id 和 uniquetoken"})

    # --- Token验证逻辑 ---
    # 调用验证函数，验证操作者身份和token
    user, role = verify_token_and_get_user(teacher_id, uniquetoken)

    # 验证失败或权限不足（必须是 'admin' 角色）
    if not user or role != 'admin':
        return jsonify({
            "code": 403,
            "message": "Token无效或权限不足",
            "data": None
        })
    # --- Token验证结束 ---
    """创建指定数量的伪造学生数据"""
    child_data = [
        # 小一班学生 (1-10)
        ('张小明', '男', '汉族', '2025-06-01', '活泼好动', 2, 1),
        ('李小红', '女', '汉族', '2025-05-01', '安静乖巧', 2, 2),
        ('王小华', '男', '汉族', '2025-04-01', '喜欢画画', 2, 3),
        ('赵小丽', '女', '汉族', '2025-03-01', '爱唱歌', 2, 4),
        ('刘小强', '男', '汉族', '2025-02-01', '运动能力强', 2, 5),
        ('陈小美', '女', '汉族', '2025-01-01', '喜欢跳舞', 2, 6),
        ('杨小刚', '男', '汉族', '2024-12-01', '爱搭积木', 2, 7),
        ('周小芳', '女', '汉族', '2024-11-01', '爱看书', 2, 8),
        ('吴小勇', '男', '汉族', '2024-10-01', '喜欢恐龙', 2, 9),
        ('郑小燕', '女', '汉族', '2024-09-01', '爱交朋友', 2, 10),
        # 中一班学生(11 - 20)
        ('孙小杰', '男', '汉族', '2024-08-01', '喜欢科学', 3, 11),
        ('朱小婷', '女', '汉族', '2024-07-01', '爱讲故事', 3, 12),
        ('胡小军', '男', '汉族', '2024-06-01', '运动健将', 3, 13),
        ('林小玉', '女', '汉族', '2024-05-01', '喜欢跳舞', 3, 14),
        ('梁小波', '男', '汉族', '2024-04-01', '爱搭积木', 3, 15),
        ('黄小梅', '女', '汉族', '2024-03-01', '安静乖巧', 3, 16),
        ('谢小东', '男', '汉族', '2024-02-01', '喜欢恐龙', 3, 17),
        ('徐小兰', '女', '汉族', '2024-01-01', '爱画画', 3, 18),
        ('高小勇', '男', '汉族', '2023-12-01', '活泼好动', 3, 19),
        ('马小丽', '女', '汉族', '2023-11-01', '爱唱歌', 3, 20),
        # 大一班学生(21 - 30)
        ('罗小强', '男', '汉族', '2023-05-01', '运动能力强', 4, 21),
        ('韩小美', '女', '汉族', '2022-12-01', '喜欢跳舞', 4, 22),
        ('唐小刚', '男', '汉族', '2022-06-01', '爱搭积木', 4, 23),
        ('冯小芳', '女', '汉族', '2021-12-01', '爱看书', 4, 24),
        ('董小勇', '男', '汉族', '2021-06-01', '喜欢恐龙', 4, 25),
        ('萧小燕', '女', '汉族', '2020-12-01', '爱交朋友', 4, 26),
        ('程小杰', '男', '汉族', '2020-06-01', '喜欢科学', 4, 27),
        ('曹小婷', '女', '汉族', '2019-12-01', '爱讲故事', 4, 28),
        ('袁小军', '男', '汉族', '2019-06-01', '运动健将', 4, 29),
        ('邓小玉', '女', '汉族', '2018-12-01', '喜欢跳舞', 4, 30)
    ]

    children = []
    for name, gender, nation, birth_date, note, class_id, guardian_id in child_data:
        # 将字符串日期转换为date对象
        year, month, day = map(int, birth_date.split('-'))
        birth_date = date(year, month, day)

        c = Child(
            child_name=name,
            gender=gender,
            nation=nation,
            birth_date=birth_date,
            note=note,
            created_time=datetime.utcnow(),
            class_id=class_id,
            guardian_id=guardian_id
        )
        children.append(c)

    db.session.add_all(children)
    try:
        db.session.commit()
        print(f"成功插入 {len(children)} 条学生数据")
    except Exception as e:
        db.session.rollback()
        print(f"插入数据时出错: {e}")
