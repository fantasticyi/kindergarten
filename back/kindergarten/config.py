import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "sdfsdfsdf"


# 开发环境
class DevelopmentConfig(Config):
    """开发模式的配置信息"""
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:0206@127.0.0.1:3306/kindergarten?charset=utf8mb4'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db/kindergarten.db')
    DEBUG = True


# 线上环境
class ProductionConfig(Config):
    """生产环境配置信息 jamkung环境"""
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@127.0.0.1:3306/flash_card?charset=utf8mb4'


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}
