from flask import Blueprint, render_template    

view_bp = Blueprint('view_bp', __name__, url_prefix='/')

@view_bp.route('/')
def home():
    return render_template('index.html')
