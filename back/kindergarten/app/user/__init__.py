from flask import Blueprint

# 创建蓝图对象
user = Blueprint("user", __name__)

from . import api