from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import DuplicateKeyError
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)

uri = "mongodb+srv://santiagosayshey:d43jKVixZuvDxe2B@whoami.hlbxfgv.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.whoami 
users_collection = db.users

@app.route('/signup', methods=['POST'])
def signup():
    firstName = request.json.get('firstName', None)
    lastName = request.json.get('lastName', None)
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    if not firstName or not lastName or not password or not email:
        return jsonify({"error": "Missing data. Please provide first name, last name, password, and email."}), 400

    hashed_password = generate_password_hash(password)

    try:
        users_collection.insert_one({
            "firstName": firstName,
            "lastName": lastName,
            "password": hashed_password,
            "email": email
        })
        app.logger.debug('User created successfully')
        # Now automatically log the user in after signup
        # Since we just checked the password, we know this should succeed
        return jsonify({"message": "User created and logged in successfully", "user": {"firstName": firstName, "lastName": lastName, "email": email}}), 201
    except DuplicateKeyError as e:
        app.logger.error('Duplicate key error: %s', e)
        return jsonify({"error": "Email already exists."}), 409
    

@app.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    app.logger.debug('Login attempt: %s', email)

    if not email or not password:
        app.logger.debug('Missing email or password')
        return jsonify({"error": "Please provide email and password."}), 400

    user = users_collection.find_one({"email": email})
    if user:
        app.logger.debug('User found in database: %s', user)
    else:
        app.logger.debug('No user found with email: %s', email)
        return jsonify({"error": "Invalid email or password."}), 401

    if check_password_hash(user['password'], password):
        app.logger.debug('Password check passed')
        return jsonify({"message": "Login successful", "user": {"firstName": user["firstName"], "lastName": user["lastName"], "email": user["email"]}}), 200
    else:
        app.logger.debug('Password check failed')
        return jsonify({"error": "Invalid email or password."}), 401


if __name__ == '__main__':
    app.run(debug=True)
