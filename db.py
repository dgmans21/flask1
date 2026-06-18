from dotenv import load_dotenv
load_dotenv()

import os
from flask import g
import pymysql

db_config = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}


def _validate_db_config():
    missing = [k for k in ('DB_USER', 'DB_NAME') if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f'.env에 {", ".join(missing)} 값이 없습니다. '
            '.env.example을 참고해 .env 파일을 작성하세요.'
        )


def get_db():
    if 'db' not in g:
        _validate_db_config()
        try:
            g.db = pymysql.connect(**db_config)
        except pymysql.err.OperationalError as e:
            err_msg = str(e)
            if 'auth_gssapi' in err_msg or '2059' in err_msg:
                raise RuntimeError(
                    'MariaDB 인증 방식(auth_gssapi_client)이 PyMySQL과 호환되지 않습니다. '
                    'MariaDB에서 아래 SQL을 실행한 뒤 .env의 DB_USER/DB_PASSWORD를 맞춰 주세요.\n'
                    "ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password "
                    "USING PASSWORD('비밀번호');\n"
                    "ALTER USER 'root'@'127.0.0.1' IDENTIFIED VIA mysql_native_password "
                    "USING PASSWORD('비밀번호');\n"
                    'FLUSH PRIVILEGES;'
                ) from e
            raise
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None and db.open:
        db.close()
