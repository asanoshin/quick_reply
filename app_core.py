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

# Webhook route
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print("-----------------------------body-----------------------------")
    print(body)
    print("---------------------------body end test5---------------------------")
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# Handle text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "體重查詢":
        user_id = event.source.user_id
        print("user_ide",user_id)
        reply_message = TextSendMessage(text='請點擊以下連結查詢體重：https://your-liff-app-url')
        line_bot_api.reply_message(event.reply_token, reply_message)


# 模擬數據庫
records = {
    "weights": [],
    "heights": []
}

@app.route('/weights', methods=['POST'])
def add_weight():
    data = request.get_json()
    if 'date' in data and 'value' in data and 'userId' in data:
        new_record = {
            'id': len(records['weights']) + 1,
            'date': data['date'],
            'weight': data['value'],
            'userId': data['userId']
        }
        records['weights'].append(new_record)
        return jsonify(new_record), 201
    return jsonify({'error': 'Invalid data'}), 400

@app.route('/heights', methods=['POST'])
def add_height():
    data = request.get_json()
    if 'date' in data and 'value' in data and 'userId' in data:
        new_record = {
            'id': len(records['heights']) + 1,
            'date': data['date'],
            'height': data['value'],
            'userId': data['userId']
        }
        records['heights'].append(new_record)
        return jsonify(new_record), 201
    return jsonify({'error': 'Invalid data'}), 400

@app.route('/weights', methods=['GET'])
def get_weights():
    userId = request.args.get('userId')
    user_weights = [record for record in records['weights'] if record['userId'] == userId]
    return jsonify(user_weights), 200

@app.route('/heights', methods=['GET'])
def get_heights():
    userId = request.args.get('userId')
    user_heights = [record for record in records['heights'] if record['userId'] == userId]
    return jsonify(user_heights), 200

@app.route('/weights/<int:record_id>', methods=['DELETE'])
def delete_weight(record_id):
    record = next((record for record in records['weights'] if record['id'] == record_id), None)
    if record:
        records['weights'].remove(record)
        return '', 204
    return jsonify({'error': 'Record not found'}), 404

@app.route('/heights/<int:record_id>', methods=['DELETE'])
def delete_height(record_id):
    record = next((record for record in records['heights'] if record['id'] == record_id), None)
    if record:
        records['heights'].remove(record)
        return '', 204
    return jsonify({'error': 'Record not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
if __name__ == '__main__':
    app.run(debug=True)

    


