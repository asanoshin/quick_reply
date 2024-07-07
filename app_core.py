from flask import Flask, request, abort, jsonify, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE channel access token and secret
line_bot_api = LineBotApi('bvoaealgSeBUNivXvkNi27W7SFUTwAWmXIshvTZbbiw3aBdqtCN77irNRrXHsrWAlCRlDSYy0vBVLYjJ5pCA/GOuiE+4T8kSCtuaUM5x6eCa2drL2ltM4E707KNQax+HmtCH5bhI/K5LHp8g1xkJQwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('1bbe70b270080e112f6f495709b43c30')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/index2")
def index2():
    return render_template('index2.html')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')

    if not signature:
        abort(400, 'Missing X-Line-Signature header')

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400, 'Invalid signature')

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "體重查詢":
        user_id = event.source.user_id
        reply_message = TextSendMessage(text='請點擊以下連結查詢體重：https://your-liff-app-url')
        line_bot_api.reply_message(event.reply_token, reply_message)

records = {
    "weights": [],
    "heights": []
}

@app.route('/users', methods=['GET'])
def get_users():
    user_id = request.args.get('userId')
    if user_id:
        name = 'John Doe'
        return jsonify({'name': name}), 200
    else:
        return jsonify({'error': 'userId is required'}), 400

@app.route('/weights', methods=['POST'])
def add_weight():
    data = request.get_json()
    if validate_record_data(data):
        new_record = create_record(data, 'weights')
        return jsonify(new_record), 201
    return jsonify({'error': 'Invalid data'}), 400

@app.route('/heights', methods=['POST'])
def add_height():
    data = request.get_json()
    if validate_record_data(data):
        new_record = create_record(data, 'heights')
        return jsonify(new_record), 201
    return jsonify({'error': 'Invalid data'}), 400

@app.route('/weights', methods=['GET'])
def get_weights():
    user_id = request.args.get('userId')
    user_weights = get_user_records(user_id, 'weights')
    return jsonify(user_weights), 200

@app.route('/heights', methods=['GET'])
def get_heights():
    user_id = request.args.get('userId')
    user_heights = get_user_records(user_id, 'heights')
    return jsonify(user_heights), 200

@app.route('/weights/<int:record_id>', methods=['DELETE'])
def delete_weight(record_id):
    return delete_record(record_id, 'weights')

@app.route('/heights/<int:record_id>', methods=['DELETE'])
def delete_height(record_id):
    return delete_record(record_id, 'heights')

def validate_record_data(data):
    return 'date' in data and 'value' in data and 'userId' in data

def create_record(data, record_type):
    new_record = {
        'id': len(records[record_type]) + 1,
        'date': data['date'],
        'value': data['value'],
        'userId': data['userId']
    }
    records[record_type].append(new_record)
    return new_record

def get_user_records(user_id, record_type):
    return [record for record in records[record_type] if record['userId'] == user_id]

def delete_record(record_id, record_type):
    record = next((record for record in records[record_type] if record['id'] == record_id), None)
    if record:
        records[record_type].remove(record)
        return '', 204
    return jsonify({'error': 'Record not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)