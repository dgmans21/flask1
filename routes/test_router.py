from flask import Blueprint, request

test_bp = Blueprint('test_bp', __name__, url_prefix='/api')
from flask import Flask, render_template,request

# Flask 애플리케이션 인스턴스 생성
app = Flask(__name__)


@test_bp.route('/good')
def hello_good():
    return '<h1>행복한하루되세요</h1>'
#params 방식예제
@test_bp.route('/get_user/<int:number>')
def get_user(number):
    return '<h1>회원에 대한 정보를 조회하는 GET 요청 받았습니다. 회원 번호: {}</h1>'.format(number)
#params 방식예제 (상품)
@test_bp.route('/get_items', methods=['GET'])
def get_items():
    item_type = request.args.get('type')
    price = request.args.get('price')
    
    # 주소창과 return문의 들여쓰기 라인(4칸 공백)을 똑같이 맞춰줍니다.
    return f"""
    <h1>상품에 대한 정보를 조회하는 GET 요청 받았습니다</h1>
    <p><b>선택한 상품:</b> {item_type}</p>
    <p><b>상품 가격:</b> {price}원</p>
        """
@test_bp.route('/vp/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    # 1. 값이 없거나 빈 상태로 오면 무조건 세팅될 '철통 기본값' 정의
    DEFAULT_TYPE = "진짜가아닌 더미상품"
    DEFAULT_PRICE = "0"
    DEFAULT_VENDOR = "unknown_vendor"
    
    # 2. request.args.get('키', default=기본값) 양식으로 1차 방어
    item_type = request.args.get('type', default=DEFAULT_TYPE)
    price = request.args.get('price', default=DEFAULT_PRICE)
    vendor_id = request.args.get('vendor_id', default=DEFAULT_VENDOR)
    
    # 3. 쓰레기 값 유효성 검사 (주소창에 ?type=&price= 처럼 빈 통만 보냈을 때 방어)
    if not item_type or item_type.strip() == "":
        item_type = DEFAULT_TYPE
        
    if not vendor_id or vendor_id.strip() == "":
        vendor_id = DEFAULT_VENDOR
        
    # 4. 가격(숫자) 유효성 검사 (숫자가 아니거나 음수면 기본값 0원으로 강제 대체)
    if not price or not price.strip().isdigit() or int(price) < 0:
        price = DEFAULT_PRICE
    else:
        # 천 단위 콤마(,)를 넣어서 포맷팅 (예: 2500000 -> 2,500,000)
        price = f"{int(price):,}"

    return f"""
    <h1>상품 상세 정보를 조회하는 GET 요청 받았습니다. 상품 ID: {product_id}</h1>
    <p><b>선택한 상품:</b> {item_type}</p>
    <p><b>상품 가격:</b> {price}원</p>
    <p><b>상품 판매자 ID:</b> {vendor_id}</p>
    """
@test_bp.route('/get_body',methods=['POST'])
def get_body():
    data = request.get_json()
    name = data.get('name') 
    age = data.get('age')   
    email = data.get('email')
    return{
        'status':200,
        'message':'생성된데이터입니다',
        'success':True,
        'data':{
            'name': name,
            'age': age,
            'email': email
        }
    }

@test_bp.route('/post', methods=['POST'])
def test_post():
    return '<h1>회원에 대한 정보를 등록하는 POST 요청 받았습니다</h1>'
# 스크립트가 직접 실행될 때 서버 가동
if __name__ == '__main__':
    app.run(debug=True)