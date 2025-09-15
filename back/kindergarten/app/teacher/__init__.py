from flask import Blueprint

# 创建蓝图对象
teacher = Blueprint("teacher", __name__)

from . import api
