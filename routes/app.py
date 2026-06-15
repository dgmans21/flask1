import os
from flask import Flask
from view_routers import view_bp
from test_router import test_bp

app = Flask(
    __name__,
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates')),
)
app.json.ensure_ascii = False
app.register_blueprint(view_bp)
app.register_blueprint(test_bp)
#서버의 활성화체크
@app.route('/health',methods=['GET'])
def health():
    return {'status':'ok','message':'서버가 정상적으로 실행되었습니다.'}

if __name__ == '__main__':
    app.run(debug=True)
