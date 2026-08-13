import os

# Detecta o diretório base do projeto
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'valifood-secret-key-2026'

    # Caminho do banco: cria na pasta instance/ dentro do projeto
    # Funciona no Windows, Linux e PythonAnywhere
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(INSTANCE_PATH, 'food_control.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
