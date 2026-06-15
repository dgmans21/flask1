import os
import joblib
import json
import logging
from flask import Blueprint, jsonify, request
from db import get_db 
from datetime import datetime

ai_bp = Blueprint('ai_bp', __name__, url_prefix='/api/ai')
logger = logging.getLogger(__name__)

# --- 1. AI 모델 로드 ---
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'iris_model_0610.pkl')
model = joblib.load(MODEL_PATH)
TARGET_NAMES = ['setosa', 'versicolor', 'virginica']

car_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'car_oil_model.pkl')
car_model = joblib.load(car_model_path)

DEFAULT_VALUES = {
    'sepal_length': 5.8,
    'sepal_width': 3.0,
    'petal_length': 3.8,
    'petal_width': 1.2
}

CAR_DEFAULT_VALUES = {
    'horsepower': 100.0,
    'weight': 3000.0,
    'displacement': 200.0,
    'acceleration': 15.0
}


# --- 2. 🪻 [방식 A] 붓꽃(Iris) 예측 및 "각각 따로" DB 저장 ---
@ai_bp.route('/predict_iris', methods=['POST'])
@ai_bp.route('/predict_iris', methods=['POST'])
def predict_iris():
    data = request.get_json() or {}
    
    # 1. 입력값 가져오기 (없으면 기본값)
    sl = float(data.get('sepal_length', DEFAULT_VALUES['sepal_length']))
    sw = float(data.get('sepal_width', DEFAULT_VALUES['sepal_width']))
    pl = float(data.get('petal_length', DEFAULT_VALUES['petal_length']))
    pw = float(data.get('petal_width', DEFAULT_VALUES['petal_width']))
    
    # 2. AI 모델 예측
    input_features = [[sl, sw, pl, pw]]
    pred_index = int(model.predict(input_features)[0])
    result_name = TARGET_NAMES[pred_index]
    
    db = get_db()
    try:
        db.begin()
        with db.cursor() as cursor:
            # --------------------------------------------------------
            # 🌟 [구조 1] iris_predict_logs -> JSON 통짜 구조 (컬럼명: result)
            # --------------------------------------------------------
            json_input = json.dumps({
                'sepal_length': sl,
                'sepal_width': sw,
                'petal_length': pl,
                'petal_width': pw
            })
            
            # 질문자님 명세에 맞춰 컬럼명을 prediction_result -> result로 전면 수정했습니다.
            query_json = '''
                INSERT INTO `iris_predict_logs` 
                (model_name, input_data, result, created_at)
                VALUES (%s, %s, %s, %s)
            '''
            cursor.execute(query_json, ('iris_0610', json_input, result_name, datetime.now()))

            # --------------------------------------------------------
            # 🌟 [구조 2] ai_iris_history -> 일반 컬럼 구조 (컬럼명: prediction_result)
            # --------------------------------------------------------
            query_separate = '''
                INSERT INTO `ai_iris_history` 
                (sepal_length, sepal_width, petal_length, petal_width, prediction_result, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query_separate, (sl, sw, pl, pw, result_name, datetime.now()))
            
            db.commit()
            
            return jsonify({
                'success': True, 
                'message': '처리완료! JSON 테이s블과 일반 테이블에 완벽하게 동시 저장되었습니다.', 
                'status': 200, 
                'data': {'result': result_name}
            })
            
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Iris 동시 적재 에러] {e}")
        return jsonify({'success': False, 'message': f'저장 실패: {str(e)}', 'status': 500, 'data': None})


# --- 3. 🚗 [방식 B] 자동차 연비 예측 및 "JSON 통째로" DB 저장 ---
@ai_bp.route('/predict_car', methods=['POST'])
def predict_car():
    data = request.get_json() or {}
    
    hp = float(data.get('horsepower', CAR_DEFAULT_VALUES['horsepower']))
    wt = float(data.get('weight', CAR_DEFAULT_VALUES['weight']))
    dp = float(data.get('displacement', CAR_DEFAULT_VALUES['displacement']))
    ac = float(data.get('acceleration', CAR_DEFAULT_VALUES['acceleration']))
    
    car_features = [[hp, wt, dp, ac]]
    pred_mpg = float(car_model.predict(car_features)[0])
    result_mpg = f"{pred_mpg:.2f}"
    
    db = get_db()
    try:
        db.begin()
        with db.cursor() as cursor:
            # ⭐️ 자동차는 유연한 구조 테스트를 위해 JSON으로 통째로 묶어줍니다.
            json_car_input = json.dumps({
                'horsepower': hp,
                'weight': wt,
                'displacement': dp,
                'acceleration': ac
            })
            
            query = '''
                INSERT INTO `ai_car_history` 
                (model_name, input_data, prediction_result, created_at)
                VALUES (%s, %s, %s, %s)
            '''
            cursor.execute(query, ('car_oil_v1', json_car_input, result_mpg, datetime.now()))
            db.commit()
            
            return jsonify({
                'success': True, 
                'message': '자동차 통합 JSON 로그 테이블에 이력이 저장되었습니다.', 
                'status': 200, 
                'data': {'mpg': float(result_mpg)}
            })
    except Exception as e:
        db.rollback()
        logger.error(f"❌ [Car DB 저장 에러] {e}")
        return jsonify({'success': False, 'message': '저장 실패', 'status': 500, 'data': None})