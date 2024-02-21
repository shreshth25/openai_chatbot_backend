from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
import mysql.connector
load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


mysql  = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='chat'
)


def allow_cors(f):
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = jsonify({"success": True})
            response.headers.add("Access-Control-Allow-Methods", "POST")
            return response
        else:
            return f(*args, **kwargs)
    return wrapper

@app.get('/')
def index():
    return "Health Check, application working fine"

@app.route("/createpost", methods=['POST', 'OPTIONS'])
@allow_cors
def create_post():
    data = request.json
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=data,
    )
    text =  response.choices[0].message.content

    return jsonify({'data':text})


@app.route("/configration", methods=['GET', 'OPTIONS'])
def configrations():
    data = {
        'background-color': '#FFF000'
    }
    cursor = mysql.cursor()
    # Assuming you have a 'users' table with 'name' and 'age' columns
    cursor.execute("INSERT INTO users (name, username, password) VALUES (%s, %s, %s)", ("shreshth", "username", "password"))
    mysql.commit()

    return jsonify({'data':data})

@socketio.on('connect')
def connect():
    print("User Connected")
    return jsonify({'user':"test"})


@socketio.on('message')
def receive_message(message):
    print("Received message from client:", message)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=message['messages']
    )
    socketio.emit('receiver-message', response.choices[0].message.content)
    
@socketio.on('stream-message')
def stream_message(message):
    print("Received message from client:", message)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=message['messages'],
        stream=True
    )
    full_text = ""
    for chunk in response:
        text = chunk.choices[0].delta.content
        if text is not None:
            if text == "":
                socketio.emit('stream-message', "newline")
            else:
                socketio.emit('stream-message', text)
            full_text+=text

    socketio.emit('stream-receive-message', full_text)

if __name__ == '__main__':
    app.run(debug=True)
