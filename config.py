import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_NAME = os.environ.get('ADMIN_NAME')
    ADMIN_KEY = os.environ.get('ADMIN_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
        'DLYItYU3V*ZacM2Ewm#Ny6oAPtv@p79g'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    POSTS_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ADMIN_EMAIL = ''
    SERVER_NAME = 'test.test'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,

    'default': DevelopmentConfig,
}
