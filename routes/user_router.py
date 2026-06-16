import logging
from flask import Blueprint, jsonify, request
from db import get_db 
import traceback

dbmng_bp = Blueprint('dbmng_bp', __name__, url_prefix='/api/user')
logger = logging.getLogger(__name__)

# [기존 기능] 상품 목록 조회 (/api/dbmng/items)
from datetime import datetime  # 🌟 created_date를 위해 파일 최상단에 import 필수!

@dbmng_bp.route('/create_user', methods=['POST'])
def create_user():
    # 1. 포스트맨이나 프론트엔드에서 보낸 JSON 데이터를 꺼냅니다.
    data = request.get_json()
    
    # 2. 데이터 유효성 검사 (필수 값 체크)
    user_id = data.get('user_id')
    pw = data.get('pw')
    nick_name = data.get('nick_name')
    address = data.get('address') # NULL 허용이지만 받아옵니다.

    if not user_id or not pw or not nick_name:
        return jsonify({"error": "user_id, pw, nick_name은 필수 입력 항목입니다."}), 400

    try:
        connection = get_db()
        with connection.cursor() as cursor:

            #u_id중복검사
            cursor.execute("SELECT * FROM user WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if result:
                return jsonify({"error": "이미 존재하는 아이디입니다."}), 400
            #NICK_NAME중복검사
            cursor.execute("SELECT * FROM user WHERE nick_name = %s", (nick_name,))
            result = cursor.fetchone()
            if result:
                return jsonify({"error": "이미 존재하는 닉네임입니다."}), 400

            # 3. 테이블 스키마에 맞춘 완벽한 INSERT 쿼리문
            # - id: AUTO_INCREMENT이므로 제외
            # - point: 기본값 0이 채워지므로 제외
            # - created_date: NOT NULL이므로 현재 시간(NOW())을 넣어줍니다.
            # - status: NOT NULL이므로 기본 가입 상태인 'Y'를 명시합니다.
            sql = """
                INSERT INTO user (user_id, pw, nick_name, address, created_date, status) 
                VALUES (%s, md5(%s), %s, %s, NOW(), 'Y');
            """
            
            # 4. 안전하게 파라미터 바인딩하여 실행
            cursor.execute(sql, (user_id, pw, nick_name, address))
            
            # 5. [★ 중요] INSERT, UPDATE, DELETE 후에는 무조건 commit을 해야 DB에 진짜 저장이 됩니다.
            connection.commit()
            
            return jsonify({"message": "회원 등록이 완료되었습니다."}), 201
            
    except Exception as e:
        # 혹시 ID나 닉네임 중복(UNIQUE INDEX)으로 터지면 이쪽에서 에러 메시지를 잡아줍니다.
        logger.error(f"❌ 회원 생성 중 에러 발생: {e}")
        return jsonify({"error": "DB 에러 발생", "details": str(e)}), 500
@dbmng_bp.route('/update_address', methods=['PUT']) 
def update_address():
    data = request.get_json()
    user_id = data.get('user_id')
    address = data.get('address')
    
    if not user_id or not address:
        return jsonify({"error": "user_id, address는 필수 입력 항목입니다."}), 400
        
    try:
        connection = get_db()
        with connection.cursor() as cursor:
            # -----------------------------------------------------------
            # 🌟 [추가] 유효성 검사: 실제 존재하는 회원인지 체크
            # -----------------------------------------------------------
            check_sql = "SELECT id FROM user WHERE user_id = %s;"
            cursor.execute(check_sql, (user_id,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                # 회원이 없으면 여기서 바로 함수를 종료하고 404를 내려줍니다.
                return jsonify({"error": "존재하지 않는 회원입니다. user_id를 확인해주세요."}), 404
            
            # -----------------------------------------------------------
            # 회원이 존재한다면 안전하게 주소 업데이트 진행
            # -----------------------------------------------------------
            sql = "UPDATE user SET address = %s WHERE user_id = %s;"
            cursor.execute(sql, (address, user_id))
            connection.commit()
            
            return jsonify({"message": "회원 정보 수정이 완료되었습니다."}), 200
            
    except Exception as e:
        logger.error(f"❌ 회원 정보 수정 중 에러 발생: {e}")
        return jsonify({"error": "DB 에러 발생", "details": str(e)}), 500
@dbmng_bp.route('/increase_point', methods=['PUT'])
def increase_point():
    data = request.get_json()
    user_id = data.get('user_id')
    point = data.get('point')
    if not user_id or not point:
        return jsonify({"error": "user_id, point는 필수 입력 항목입니다."}), 400
    try:
        connection = get_db()
        with connection.cursor() as cursor:
            sql = "UPDATE user SET point = point + %s WHERE user_id = %s;"
            cursor.execute(sql, (point, user_id))
            connection.commit()
            return jsonify({"message": "회원 포인트 증가가 완료되었습니다."}), 200
    except Exception as e:
        logger.error(f"❌ 회원 포인트 증가 중 에러 발생: {e}")
        return jsonify({"error": "DB 에러 발생", "details": str(e)}), 500

@dbmng_bp.route('/delete_user', methods=['DELETE'])
def delete_user():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id는 필수 입력 항목입니다."}), 400
    try:
        connection = get_db()
        with connection.cursor() as cursor:
            sql = "DELETE FROM user WHERE user_id = %s;"
            cursor.execute(sql, (user_id,))
            connection.commit()
            return jsonify({"message": "회원 삭제가 완료되었습니다."}), 200
    except Exception as e:
        logger.error(f"❌ 회원 삭제 중 에러 발생: {e}")
        return jsonify({"error": "DB 에러 발생", "details": str(e)}), 500

@dbmng_bp.route('/login', methods=['POST'])
def user_login():
    data = request.get_json()
    user_id = data.get('user_id')
    pw = data.get('pw')
    
    # 1. 아예 필수 데이터 자체를 누락해서 보낸 것은 구조적 오류이므로 400을 줍니다.
    if not user_id or not pw:
        return jsonify({"error": "user_id, pw는 필수 입력 항목입니다."}), 400
        
    try:
        connection = get_db()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM user WHERE user_id = %s AND pw = md5(%s);"
            cursor.execute(sql, (user_id, pw))
            result = cursor.fetchone()
            
            # 2. 아이디가 없든 비번이 틀렸든 인증 실패이므로 메시지는 뭉뚱그리고 401을 줍니다.
            if not result:
                return jsonify({"error": "아이디 또는 비밀번호가 일치하지 않습니다."}), 401
                
            return jsonify({"message": "로그인 성공"}), 200
            
    except Exception as e:
        logger.error(f"❌ 회원 로그인 중 에러 발생: {e}")
        return jsonify({"error": "DB 에러 발생", "details": str(e)}), 500
@dbmng_bp.route('/all_user', methods=['GET'])
def get_all_user():
    try:
        connection = get_db()
        with connection.cursor() as cursor:
            sql = "SELECT user_id, nick_name, address FROM user LIMIT 10;"
            cursor.execute(sql)
            result = cursor.fetchall()
            print("--- 쿼리 실행 성공 ---")
            return jsonify(result)
    except Exception as e:
      # 파이썬이 잡은 에러의 상세 내용을 문자열로 만듭니다.
        error_message = traceback.format_exc()
        
        # 화면에 500 에러와 함께 진짜 원인을 리턴해버립니다!
        return jsonify({
            "error": "DB 에러 발생",
            "real_reason": error_message  # <--- 화면에서 이걸 확인하세요!
        }), 500

@dbmng_bp.route('/search_id', methods=['GET'])
def get_user_by_id():   
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id 파라미터가 필요합니다."}), 400

    try:
        connection = get_db()
        
        with connection.cursor() as cursor:
            # 💡 1. 띄어쓰기 수정 및 필요한 안전한 컬럼만 명시! (비밀번호 등 제외)
            sql = "SELECT user_id, nick_name, address FROM user WHERE user_id = %s;"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({"message": "존재하지 않는 회원입니다."}), 404
                
            # db.py에서 DictCursor를 설정해두셨기 때문에 
            # result는 {'id': 1, 'username': 'test1234', 'email': '...'} 형태의 딕셔너리입니다.
            # jsonify가 이를 받아 깔끔한 JSON 포맷으로 브라우저에 찍어줍니다.
            return jsonify(result)
            
    except Exception as e:
        # 💡 터미널 창에 어떤 정확한 에러가 났는지 찍어주므로 버그 잡기가 쉬워집니다.
        logger.error(f"❌ 회원 조회 중 진짜 에러 발생: {e}")
        return jsonify({"error": "DB 에러 발생", "details": str(e)}), 500