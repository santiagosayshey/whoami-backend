from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

# Setup basic logging
logging.basicConfig(level=logging.DEBUG)

uri = "mongodb+srv://santiagosayshey:d43jKVixZuvDxe2B@whoami.hlbxfgv.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.whoami 
users_collection = db.users
questions_collection = db.questions

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
        result = users_collection.insert_one({
            "firstName": firstName,
            "lastName": lastName,
            "password": hashed_password,
            "email": email
        })
        user_id = result.inserted_id
        return jsonify({"message": "User created and logged in successfully", "user": {"_id": str(user_id), "firstName": firstName, "lastName": lastName, "email": email}}), 201
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
    if user and check_password_hash(user['password'], password):
        app.logger.debug('Password check passed')
        # Include the _id in the response
        return jsonify({"message": "Login successful", "user": {"_id": str(user["_id"]), "firstName": user["firstName"], "lastName": user["lastName"], "email": user["email"]}}), 200
    else:
        app.logger.debug('Password check failed')
        return jsonify({"error": "Invalid email or password."}), 401

    
@app.route('/questions/<user_id>', methods=['GET'])
def get_questions(user_id):
    try:
        app.logger.debug(f"Fetching questions for user {user_id}")
        user_questions = questions_collection.find({"user_id": ObjectId(user_id)})
        questions_list = [{"_id": str(q["_id"]), "text": q["text"]} for q in user_questions]
        
        return jsonify({"questions": questions_list}), 200

    except Exception as e:
        app.logger.error(f"Error fetching questions for user {user_id}: {str(e)}")
        return jsonify({"error": "Error fetching questions"}), 500



@app.route('/questions/<user_id>', methods=['POST'])
def add_question(user_id):
    try:
        question_text = request.json.get('text', None)
        
        if not question_text:
            return jsonify({"error": "No question text provided"}), 400

        # Create a new document for the question
        result = questions_collection.insert_one({
            "text": question_text,
            "user_id": ObjectId(user_id)  # Store the user_id as an ObjectId
        })

        return jsonify({"message": "Question added successfully", "question_id": str(result.inserted_id)}), 201
    except Exception as e:
        app.logger.error("Error adding question for user {}: {}".format(user_id, str(e)))
        return jsonify({"error": "Error adding question"}), 500


@app.route('/questions/<user_id>/<question_id>', methods=['DELETE'])
def delete_question(user_id, question_id):
    try:
        # Convert question_id from string to ObjectId
        oid_question = ObjectId(question_id)

        # Directly delete the question document
        result = questions_collection.delete_one({"_id": oid_question})

        if result.deleted_count > 0:
            return jsonify({"message": "Question deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete question"}), 404  # Not found or already deleted
    except Exception as e:
        app.logger.error("Error deleting question for user {}: {}".format(user_id, str(e)))
        return jsonify({"error": "Error deleting question"}), 500


if __name__ == '__main__':
    app.run(debug=True)
