from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config_map
from app import teacher, user, admin
from .models import db
# import pymysql

# 实例化一个我们需要的redis对象存储缓存数据


def create_app(dev_name):
    """
    返回一个实例化并且配置好数据的一个app
    dev_name：选择环境的参数
    :return:
    """
    app = Flask(__name__)
    config_class = config_map.get(dev_name)
    app.config.from_object(config_class)  # 从类中读取需要的信息

    db.init_app(app)  # 实例化的数据库 配置信息

    # 绑定包里面的蓝图对象
    app.register_blueprint(teacher.teacher, url_prefix="/teacher")
    app.register_blueprint(user.user, url_prefix="/user")
    app.register_blueprint(admin.admin, url_prefix="/admin")

    return app
