import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    CONFIG_NAME = ''
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_NAME = os.environ.get('ADMIN_NAME')
    ADMIN_KEY = os.environ.get('ADMIN_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
        'DLYItYU3V*ZacM2Ewm#Ny6oAPtv@p79g'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    POSTS_PER_PAGE = 10

    @classmethod
    def init_app(cls, app):
        pass


class DevelopmentConfig(Config):
    CONFIG_NAME = 'development'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    CONFIG_NAME = 'testing'
    TESTING = True
    DEBUG = True
    ADMIN_EMAIL = ''
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    CONFIG_NAME = 'production'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        super(ProductionConfig, cls).init_app(app)


class UnixConfig(ProductionConfig):
    CONFIG_NAME = 'unix'

    @classmethod
    def init_app(cls, app):
        super(UnixConfig, cls).init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'unix': UnixConfig,

    'default': DevelopmentConfig,
}
