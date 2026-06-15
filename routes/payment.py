import logging
from flask import Blueprint, jsonify, request  # 👈 request 임포트 추가
from db import get_db 
from datetime import datetime

payment_bp = Blueprint('payment_bp', __name__, url_prefix='/api/payment')
logger = logging.getLogger(__name__)

@payment_bp.route('/buy_item', methods=['POST'])
def buy_item():
    # 1. Postman 또는 프론트엔드에서 보낸 요청 데이터 받기
    data = request.get_json()
    u_id_pk = data.get('user_id')       # 결제하는 회원의 고유 번호 (user 테이블의 id)
    product_id = data.get('product_id') # 구매할 상품의 고유 번호 (item 테이블의 id)
    req_cnt = data.get('cnt')           # 구매 요구 수량

    # [유효성 검사] 필수 데이터가 누락되었는지 확인
    if not u_id_pk or not product_id or not req_cnt:
        return jsonify({'success': False, 'message': 'user_id, product_id, cnt는 필수입니다.', 'status': 400, 'data': None})
    
    # [유효성 검사] 수량이 올바른지 확인
    if req_cnt <= 0:
        return jsonify({'success': False, 'message': '수량은 1개 이상이어야 합니다.', 'status': 400, 'data': None})

    db = get_db()
    
    # ⭐️ 1. try 문이 가장 먼저 감싸야 안전하게 에러를 잡아 롤백할 수 있습니다.
    try:
        # ⭐️ 2. 트랜잭션 시작
        db.begin()
        
        # ⭐️ 3. 커서는 try 안에서 트랜잭션이 켜진 후에 열어야 합니다.
        with db.cursor() as cursor:
            # 2. 회원 존재 여부 및 보유 포인트 확인 (status가 'Y'인 활성 회원만)
            cursor.execute("SELECT * FROM `user` WHERE id = %s AND status = 'Y'", (u_id_pk,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'success': False, 'message': '존재하지 않거나 탈퇴한 회원입니다.', 'status': 404, 'data': None})
            
            user_point = user['point']

            # 3. 상품 존재 여부 및 현재 재고 확인 (FOR UPDATE 잠금)
            cursor.execute("SELECT * FROM `item` WHERE id = %s FOR UPDATE", (product_id,))
            product = cursor.fetchone()
            if not product:
                return jsonify({'success': False, 'message': '존재하지 않는 상품입니다.', 'status': 404, 'data': None})
            
            product_stock = product['stock_cnt'] 
            product_price = product['price']     

            # [조건 검사 A] 재고 부족 확인
            if product_stock < req_cnt:
                return jsonify({'success': False, 'message': f'재고가 부족합니다. (남은 재고: {product_stock}개)', 'status': 400, 'data': None})

            # 이번 결제의 총 금액 계산
            current_total_price = product_price * req_cnt

            # [조건 검사 B] 포인트 부족 확인
            if user_point < current_total_price:
                return jsonify({'success': False, 'message': f'포인트가 부족합니다. (필요: {current_total_price}, 보유: {user_point})', 'status': 400, 'data': None})

            # --- 4. 데이터 조작 (DML) 시작 ---

            # A. 유저 포인트 차감
            cursor.execute(
                "UPDATE `user` SET point = point - %s, updated_date = %s WHERE id = %s", 
                (current_total_price, datetime.now(), u_id_pk)
            )

            # B. 상품 재고 차감
            cursor.execute(
                "UPDATE `item` SET stock_cnt = stock_cnt - %s, update_date = %s WHERE id = %s", 
                (req_cnt, datetime.now(), product_id)
            )

            # C. 결제(payment) 내역 생성 (새로운 Row 추가)
            cursor.execute(
                '''INSERT INTO `payment` 
                (user_id, product_id, total_price, cnt, create_date) 
                VALUES 
                (%s, %s, %s, %s, %s)''',
                (u_id_pk, product_id, current_total_price, req_cnt, datetime.now())
            )

            # 모든 데이터 조작 성공 시 커밋
            db.commit()

            return jsonify({
                'success': True,
                'message': '결제가 정상적으로 완료되었습니다.',
                'status': 200,
                'data': {
                    'total_price': current_total_price,
                    'cnt': req_cnt,
                    'remaining_point': user_point - current_total_price
                }
            })

    except Exception as e:
        # 🚨try 문과 라인이 딱 맞아야 에러가 났을 때 이 롤백 블록이 실행됩니다!
        db.rollback()
        logger.error(f"❌ [결제 시스템 에러] 오류 내용: {e}")
        return jsonify({'success': False, 'message': '결제 처리 중 서버 내부 에러가 발생하여 취소되었습니다.', 'status': 500, 'data': None})
@payment_bp.route('/cancel_item', methods=['POST'])
def cancel_item():
    # 1. 요청 데이터 받기
    data = request.get_json()
    payment_id = data.get('payment_id') # 취소할 주문의 고유 번호 (payment 테이블의 id)
    u_id_pk = data.get('user_id')       # 취소를 요청한 현재 유저의 고유 번호 (user 테이블의 id)

    # 유효성 검사
    if not payment_id or not u_id_pk:
        return jsonify({'success': False, 'message': 'payment_id와 user_id는 필수입니다.', 'status': 400, 'data': None})

    db = get_db()
    
    try:
        db.begin() # 트랜잭션 시작
        
        with db.cursor() as cursor:
            # 2. 🔍 주문 내역이 실제로 존재하는지 확인 (FOR UPDATE로 다른 동시 요청 차단)
            cursor.execute("SELECT * FROM `payment` WHERE id = %s FOR UPDATE", (payment_id,))
            payment = cursor.fetchone()
            
            if not payment:
                return jsonify({'success': False, 'message': '존재하지 않는 주문 내역입니다.', 'status': 404, 'data': None})

            # 3. 🛡️ 먹튀 검증: 주문 내역의 user_id와 현재 취소를 요청한 user_id가 일치하는지 확인
            if payment['user_id'] != u_id_pk:
                return jsonify({'success': False, 'message': '본인의 주문 내역만 취소할 수 있습니다.', 'status': 403, 'data': None})

            # 환불에 필요한 정보 추출
            refund_price = payment['total_price']
            refund_cnt = payment['cnt']
            product_id = payment['product_id']

            # 4. 💰 유저의 포인트 원상복구 (돈 다시 + 해주기)
            cursor.execute(
                "UPDATE `user` SET point = point + %s, updated_date = %s WHERE id = %s",
                (refund_price, datetime.now(), u_id_pk)
            )

            # 5. 📦 상품의 재고 원상복구 (재고 다시 + 해주기)
            cursor.execute(
                "UPDATE `item` SET stock_cnt = stock_cnt + %s, update_date = %s WHERE id = %s",
                (refund_cnt, datetime.now(), product_id)
            )

            # 6. ❌ 취소가 완료되었으니 payment 테이블에서 해당 주문 내역 삭제 (or 상태 변경)
            # 실무에서는 데이터를 지우기보다 status = 'CANCEL'로 바꾸지만, 여기서는 깔끔하게 삭제로 구현합니다.
            cursor.execute("DELETE FROM `payment` WHERE id = %s", (payment_id,))

            # 모든 쿼리가 성공했으므로 최종 반영!
            db.commit()

            return jsonify({
                'success': True,
                'message': '주문 취소 및 환불 처리가 완료되었습니다.',
                'status': 200,
                'data': {
                    'payment_id': payment_id,
                    'refund_price': refund_price,
                    'refund_cnt': refund_cnt
                }
            })

    except Exception as e:
        db.rollback() # 하나라도 실패하면 전원 원상복구
        logger.error(f"❌ [주문 취소 시스템 에러] 오류 내용: {e}")
        return jsonify({'success': False, 'message': '주문 취소 처리 중 서버 내부 에러가 발생하여 취소되었습니다.', 'status': 500, 'data': None})
from flask import request  # 상단에 request 있는지 다시 한번 확인!

@payment_bp.route('/list', methods=['GET'])  # 👈 GET 방식으로 변경
def get_payment_list_get():
    # 1. URL 주소창에 붙어오는 ?user_id=1 값 꺼내기
    # 💡 GET 파라미터는 무조건 '문자열'로 들어오기 때문에 int()로 형변환을 해주는 것이 안전합니다.
    user_pk = request.args.get('user_id')

    if not user_pk:
        return jsonify({'success': False, 'message': 'user_id는 필수입니다.', 'status': 400, 'data': None})

    try:
        user_pk = int(user_pk)
    except ValueError:
        return jsonify({'success': False, 'message': 'user_id는 숫자여야 합니다.', 'status': 400, 'data': None})

    db = get_db()
    
    try:
        with db.cursor() as cursor:
            # 2. payment와 item 테이블을 JOIN하여 최신순 정렬
            query = '''
                SELECT 
                    p.product_id,
                    i.product_name,
                    i.maker,
                    p.total_price,
                    p.cnt,
                    p.create_date
                FROM `payment` p
                INNER JOIN `item` i ON p.product_id = i.id
                WHERE p.user_id = %s
                ORDER BY p.create_date DESC
            '''
            cursor.execute(query, (user_pk,))
            payment_list = cursor.fetchall()

            if not payment_list:
                return jsonify({
                    'success': True,
                    'message': '주문 내역이 존재하지 않습니다.',
                    'status': 200,
                    'data': []
                })

            # datetime 객체를 문자열로 변환
            for row in payment_list:
                if row['create_date']:
                    row['create_date'] = row['create_date'].strftime('%Y-%m-%d %H:%M:%S')

            return jsonify({
                'success': True,
                'message': '주문 내역 조회가 완료되었습니다.',
                'status': 200,
                'data': payment_list
            })

    except Exception as e:
        logger.error(f"❌ [주문 내역 조회 GET 에러] 오류 내용: {e}")
        return jsonify({'success': False, 'message': '조회 중 서버 내부 에러가 발생했습니다.', 'status': 500, 'data': None})        