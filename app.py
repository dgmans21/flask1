from flask import Flask

app = Flask(__name__)
app.json.ensure_ascii = False
from routes.view_routers import view_bp
from routes.test_router import test_bp  
from ai_route.ai_routers import ai_bp
from routes.user_router import dbmng_bp
from routes.item_route import item_bp   
from routes.user_router2 import user_bp
from routes.payment import payment_bp
app.register_blueprint(view_bp)
app.register_blueprint(test_bp)
app.register_blueprint(ai_bp)   
app.register_blueprint(dbmng_bp)
app.register_blueprint(item_bp)
app.register_blueprint(user_bp)
app.register_blueprint(payment_bp)
#서버의 활성화체크

# 1. db.py에서 close_db 함수를 불러옵니다.
from db import close_db  

# 2. [★ 핵심] Flask에게 요청이 끝날 때 이 함수를 실행하라고 등록합니다.
app.teardown_appcontext(close_db)
@app.route('/health',methods=['GET'])
def health():
    return {'status':'ok','message':'서버가 정상적으로 실행되었습니다.'}
if __name__ == '__main__':
    app.run(debug=True)
