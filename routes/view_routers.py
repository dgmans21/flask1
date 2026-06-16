from flask import Blueprint, render_template    

view_bp = Blueprint('view_bp', __name__, url_prefix='/')

@view_bp.route('/')
def home():
    return render_template('index.html')

@view_bp.route('/basic')
def basic():
    return render_template('basic.html')

@view_bp.route('/login')
def login():
    return render_template('login.html')

@view_bp.route('/lectures')
def lectures():
    return render_template('lectures.html')
@view_bp.route('/class')
def register():
    return render_template('class-id.html')
@view_bp.route('/layout')
def layout():
    return render_template('layout.html')