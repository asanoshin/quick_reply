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
        reply_message = TextSendMessage(text='請點擊以下連結查詢體重：https://your-liff-app-url')
        line_bot_api.reply_message(event.reply_token, reply_message)


# 模擬的資料庫
weight_records = []

# 新增體重記錄
@app.route('/weights', methods=['POST'])
def add_weight():
    data = request.get_json()
    record = {
        'id': len(weight_records) + 1,
        'date': data['date'],
        'weight': data['weight'],
        'user_id': data['userId']
    }
    weight_records.append(record)
    return jsonify(record), 201

# 刪除體重記錄
@app.route('/weights/<int:record_id>', methods=['DELETE'])
def delete_weight(record_id):
    global weight_records
    weight_records = [record for record in weight_records if record['id'] != record_id]
    return '', 204

# 查詢體重記錄
@app.route('/weights', methods=['GET'])
def get_weights():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    user_id = request.args.get('userId')
    filtered_records = [record for record in weight_records if start_date <= record['date'] <= end_date and record['user_id'] == user_id]
    return jsonify(filtered_records)

if __name__ == '__main__':
    app.run(debug=True)

    


