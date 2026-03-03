from flask import Flask, request, jsonify,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import os

app = Flask(__name__)
from flask import send_from_directory

# ... baaki code ...

@app.route('/')
def index():
    # Agar aapki HTML file ka naam 'index.html' hai aur wo isi folder mein hai
    return send_from_directory('.', 'index.html')

# ... baaki routes ...
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ledger.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    ledger_data = db.Column(db.Text, default='[]')

with app.app_context():
    db.create_all()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email'], password=data['password']).first()
    if user:
        return jsonify({"email": user.email, "ledger_data": json.loads(user.ledger_data)})
    return jsonify({"error": "Error"}), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Exists"}), 400
    new_user = User(email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Success"})

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Missing fields"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"message": "User already exists"}), 400

    new_user = User(email=email, password=password, ledger_data="[]")
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "email": email,
        "ledger_data": []
    }), 200

# --- REAL-TIME SYNC ROUTES ---

@app.route('/api/delete', methods=['POST'])
def delete_record():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user:
        db_data = json.loads(user.ledger_data)
        # ID ko string me convert karke match kar rahe hain taaki error na aaye
        new_data = [i for i in db_data if str(i.get('id')) != str(data.get('id'))]
        user.ledger_data = json.dumps(new_data)
        db.session.commit() # Database me turant save
        return jsonify({"new_data": new_data})
    return jsonify({"error": "Fail"}), 404

@app.route('/api/edit', methods=['POST'])
def edit_record():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user:
        db_data = json.loads(user.ledger_data)
        for i in db_data:
            if str(i.get('id')) == str(data.get('id')):
                i['n'], i['a'], i['d'], i['t'] = data['n'], float(data['a']), data['d'], data['t']
        user.ledger_data = json.dumps(db_data)
        db.session.commit() # Database me turant save
        return jsonify({"new_data": db_data})
    return jsonify({"error": "Fail"}), 404

@app.route('/api/sync', methods=['POST'])
def sync():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user:
        user.ledger_data = json.dumps(data['ledger_data'])
        db.session.commit()
        return jsonify({"message": "Synced"})
    return jsonify({"error": "Error"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')