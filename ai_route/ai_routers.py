import os
import joblib
import json
import logging
from flask import Blueprint, jsonify, request, render_template
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
@ai_bp.route('/')
def ai_index():
    """AI 서비스 기본 페이지 — GET /api/ai/"""
    return render_template('iris.html')


# --- 2. 🪻 [방식 A] 붓꽃(Iris) 예측 및 "각각 따로" DB 저장 ---
@ai_bp.route('/predict_iris', methods=['POST'])
def predict_iris():
    data = request.get_json() or {}

    try:
        sl = float(data.get('sepal_length', DEFAULT_VALUES['sepal_length']))
        sw = float(data.get('sepal_width', DEFAULT_VALUES['sepal_width']))
        pl = float(data.get('petal_length', DEFAULT_VALUES['petal_length']))
        pw = float(data.get('petal_width', DEFAULT_VALUES['petal_width']))
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': '입력값이 올바른 숫자가 아닙니다.',
            'status': 400,
            'data': None
        }), 400

    input_features = [[sl, sw, pl, pw]]
    pred_index = int(model.predict(input_features)[0])
    result_name = TARGET_NAMES[pred_index]

    db = None
    try:
        db = get_db()
        db.begin()
        with db.cursor() as cursor:
            json_input = json.dumps({
                'sepal_length': sl,
                'sepal_width': sw,
                'petal_length': pl,
                'petal_width': pw
            })

            cursor.execute('''
                INSERT INTO `iris_predict_logs`
                (model_name, input_data, result, created_at)
                VALUES (%s, %s, %s, %s)
            ''', ('iris_0610', json_input, result_name, datetime.now()))

            cursor.execute('''
                INSERT INTO `ai_iris_history`
                (sepal_length, sepal_width, petal_length, petal_width, prediction_result, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (sl, sw, pl, pw, result_name, datetime.now()))

        db.commit()
        return jsonify({
            'success': True,
            'message': '예측 및 DB 저장 완료',
            'status': 200,
            'data': {'result': result_name}
        })

    except Exception as e:
        if db is not None:
            db.rollback()
        logger.error(f"❌ [Iris DB 저장 에러] {e}")
        return jsonify({
            'success': True,
            'message': f'예측 완료 (DB 저장 실패: {e})',
            'status': 200,
            'data': {'result': result_name}
        })


# --- 3. 🚗 [방식 B] 자동차 연비 예측 및 "JSON 통째로" DB 저장 ---
@ai_bp.route('/predict_car', methods=['POST'])
def predict_car():
    data = request.get_json() or {}

    try:
        hp = float(data.get('horsepower', CAR_DEFAULT_VALUES['horsepower']))
        wt = float(data.get('weight', CAR_DEFAULT_VALUES['weight']))
        dp = float(data.get('displacement', CAR_DEFAULT_VALUES['displacement']))
        ac = float(data.get('acceleration', CAR_DEFAULT_VALUES['acceleration']))
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'message': '입력값이 올바른 숫자가 아닙니다.',
            'status': 400,
            'data': None
        }), 400

    car_features = [[hp, wt, dp, ac]]
    pred_mpg = float(car_model.predict(car_features)[0])
    result_mpg = f"{pred_mpg:.2f}"

    db = None
    try:
        db = get_db()
        db.begin()
        with db.cursor() as cursor:
            json_car_input = json.dumps({
                'horsepower': hp,
                'weight': wt,
                'displacement': dp,
                'acceleration': ac
            })

            cursor.execute('''
                INSERT INTO `ai_car_history`
                (model_name, input_data, prediction_result, created_at)
                VALUES (%s, %s, %s, %s)
            ''', ('car_oil_v1', json_car_input, result_mpg, datetime.now()))

        db.commit()
        return jsonify({
            'success': True,
            'message': '예측 및 DB 저장 완료',
            'status': 200,
            'data': {'mpg': float(result_mpg)}
        })

    except Exception as e:
        if db is not None:
            db.rollback()
        logger.error(f"❌ [Car DB 저장 에러] {e}")
        return jsonify({
            'success': True,
            'message': f'예측 완료 (DB 저장 실패: {e})',
            'status': 200,
            'data': {'mpg': float(result_mpg)}
        })