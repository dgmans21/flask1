# 1. 다른 무엇보다 무조건 1등으로 .env를 로드합니다!
from dotenv import load_dotenv
load_dotenv()

# 2. 그 다음 필요한 라이브러리들을 import 합니다.
import os
from flask import Flask, jsonify, g
import pymysql

# 3. 블루프린트 등 다른 파일 import는 반드시 load_dotenv() 아래에 위치해야 합니다.
# 예: from routes.user_router import dbmng_bp 

app = Flask(__name__)

db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'), # 이제 정상적으로 .env 값을 읽어옵니다!
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(**db_config)
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None and db.open:
        db.close()
        #print("🔄 [Flask 시스템] 사용이 끝난 DB 커넥션이 자동으로 반납되었습니다.")