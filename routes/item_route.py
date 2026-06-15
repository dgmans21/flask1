import logging
from flask import Blueprint, jsonify
from db import get_db 

# 🌟 블루프린트 이름을 'item_bp'로 명확하게 선언합니다.
# 주소창에 /api/item/items 로 접근하게 됩니다. (원하시면 url_prefix를 '/api'로 바꾸셔도 됩니다)
item_bp = Blueprint('item_bp', __name__, url_prefix='/api/item')
logger = logging.getLogger(__name__)

# =======================================================
# [상품 도메인] 상품 목록 조회 (/api/item/items)
# =======================================================
@item_bp.route('/top5_item', methods=['GET'])
def get_items():
    try:
        # Flask g 객체에서 안전하게 DB 커넥션을 가져옵니다.
        connection = get_db()
        
        with connection.cursor() as cursor:
            sql = "SELECT user_id, product_name, price FROM item LIMIT 5;"
            cursor.execute(sql)
            result = cursor.fetchall()
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"❌ 상품 조회 중 에러 발생: {e}")
        return jsonify({"error": "DB 에러 발생", "details": str(e)}), 500
        
    # close_db는 app.py가 알아서 해주므로 finally는 필요 없습니다!