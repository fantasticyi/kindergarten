from flask import jsonify
from .models import Admin, Parent, Teacher

def verify_token_and_get_user(user_id, token):
    """
    通过 user_id 和 token 验证用户，并返回用户对象和角色

    :param user_id: 用户ID
    :param token: 前端发来的 uniquetoken
    :return: (user, role) 元组，如果验证失败则返回 (None, None)
    """
    # 尝试在 Admin 表中查找
    user = Admin.query.get(user_id)
    if user and hasattr(user, 'token') and user.token == token:
        return user, 'admin'

    # 尝试在 Teacher 表中查找
    user = Teacher.query.get(user_id)
    if user and hasattr(user, 'token') and user.token == token:
        return user, 'teacher'

    # 尝试在 Parent 表中查找
    user = Parent.query.get(user_id)
    if user and hasattr(user, 'token') and user.token == token:
        return user, 'parent'

    return None, None