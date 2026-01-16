import os

from dotenv import load_dotenv

load_dotenv()

class Config(object):
    TESTING = False
    DEBUG = True
    DATABASE_URI = 'postgresql+psycopg2://postgres:example@postgres:5432/ark'
    SECRET_KEY = 'no secret'

class ProductionConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY')
    MINTER_API_KEY = os.getenv('MINTER_API_KEY')

class DevelopmentConfig(Config):
    DEBUG = True
    MINTER_API_KEY = os.getenv('MINTER_API_KEY', 'dev-api-key')

class TestingConfig(Config):
    TESTING = True

