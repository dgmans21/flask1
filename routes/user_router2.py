# user_route.py
from flask import Blueprint, request, jsonify
from db import get_db  # close_db는 이제 여기서 직접 호출하지 않으므로 import 안 해도 됨

user_bp = Blueprint('user', __name__, url_prefix='/api/users')

# 1. 로그인 요청
@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        u_id = data.get('u_id')
        pw = data.get('pw')

        if not u_id or not pw:
            return jsonify({'success': False, 'message': 'u_id, pw 는 필수입니다.', 'status': 400, 'data': None})
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM `user` WHERE u_id = %s AND pw = md5(%s)", (u_id, pw))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'message': '회원 조회 실패, 회원이 존재하지 않습니다.', 'status': 401, 'data': None})
            
            return jsonify({
                'success': True,
                'message': '로그인 성공',
                'status': 200,
                'data': {
                    'id': user['id'],
                    'u_id': user['u_id'],
                    'nick': user['nick'],
                    'address': user['address']
                }
            })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': '로그인 실패, 내부 서버 에러', 'status': 500, 'data': None})


# 2. point 증가
@user_bp.route('/increase-point', methods=['PUT'])
def increase_point():
    try:
        data = request.get_json()
        id = data.get('id')
        point = data.get('amount')

        if not id or not point:
            return jsonify({'success': False, 'message': 'id, point 는 필수입니다.', 'status': 400, 'data': None})
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM `user` WHERE id = %s", (id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'message': '회원 조회 실패, 회원이 존재하지 않습니다.', 'status': 400, 'data': None})
            
            cursor.execute("UPDATE `user` SET point = point + %s WHERE id = %s", (point, id))
            db.commit()
            return jsonify({'success': True, 'message': 'point 증가 완료', 'status': 200, 'data': {'id': id, 'point': point}})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'point 증가 실패, 내부 서버 에러', 'status': 500, 'data': None})


# 3. 회원 address 수정
@user_bp.route('/update-address', methods=['PUT'])
def update_address():
    try:
        data = request.get_json()
        id = data.get('id')
        address = data.get('new_address')

        if not id or not address:
            return jsonify({'success': False, 'message': 'id, new_address 는 필수입니다.', 'status': 400, 'data': None})

        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM `user` WHERE id = %s", (id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'message': '회원 조회 실패, 회원이 존재하지 않습니다.', 'status': 400, 'data': None})
        
            cursor.execute("UPDATE `user` SET address = %s WHERE id = %s", (address, id))
            db.commit()
            return jsonify({'success': True, 'message': '회원 address 수정 완료', 'status': 200, 'data': {'id': id, 'address': address}})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': '회원 address 수정 실패, 내부 서버 에러', 'status': 500, 'data': None})


# 4. 회원 생성
@user_bp.route('/create', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        u_id = data.get('user_id')
        pw = data.get('pw')
        nick = data.get('nick_name')
        address = data.get('address')

        db = get_db()
        with db.cursor() as cursor:
            # u_id 중복 검사
            cursor.execute("SELECT * FROM `user` WHERE u_id = %s", (u_id,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'u_id 중복입니다.', 'status': 400, 'data': None})
            
            # nick 중복 검사
            cursor.execute("SELECT * FROM `user` WHERE nick = %s", (nick,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'nick 중복입니다.', 'status': 400, 'data': None})
            
            # 회원 생성
            cursor.execute(
                '''INSERT INTO `user` (u_id, pw, nick, address, created_at) 
                   VALUES (%s, md5(%s), %s, %s, now())''', 
                (u_id, pw, nick, address)
            )
            db.commit()

            return jsonify({
                'success': True, 'message': '회원 생성 완료', 'status': 200,
                'data': {'u_id': u_id, 'pw': pw, 'nick': nick, 'address': address}
            })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': '회원 생성 실패, 내부 서버 에러', 'status': 500, 'data': None})


# 5. id 로 회원 조회
@user_bp.route('/get-user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM `user` WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return jsonify({'success': True, 'message': '회원 조회 완료', 'status': 200, 'data': user})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': '회원 조회 실패, 내부 서버 에러', 'status': 500, 'data': None})


# 6. 전체 회원 조회
@user_bp.route('/all', methods=['GET'])
def get_all_users():
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM `user`")
            users = cursor.fetchall()
            return jsonify({'success': True, 'message': '회원 전체 조회 완료', 'status': 200, 'data': users})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': '회원 전체 조회 실패, 내부 서버 에러', 'status': 500, 'data': None})