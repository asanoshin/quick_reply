# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/about')
# def about():
#     return render_template('about.html')

# if __name__ == '__main__':
#     app.run(debug=True)

# ------------------------------------------
# from flask import Flask, render_template, request

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/submit', methods=['POST'])
# def submit():
#     phone = request.form['phone']
#     option = request.form['option']
#     print(f"{phone}, {option}")
#     return f"提交成功！電話：{phone}, 選項：{option}"

# @app.route('/about')
# def about():
#     return render_template('about.html')

# if __name__ == '__main__':
#     app.run(debug=True)

#--------------------------
# from flask import Flask, render_template, request, redirect, url_for

# app = Flask(__name__)
# submissions = []  # 用來保存提交的清單

# @app.route('/', methods=['GET', 'POST'])
# def home():
#     if request.method == 'POST':
#         phone = request.form['phone']
#         option = request.form['option']
#         submission = f"{phone}, {option}"
#         submissions.append(submission)  # 添加到提交清單
#         return redirect(url_for('home'))  # 重新導向到首頁
#     return render_template('home.html', submissions=submissions)

# @app.route('/about')
# def about():
#     return render_template('about.html')

# if __name__ == '__main__':
#     app.run(debug=True)
# -------------------------------------------------------

# from flask import Flask, render_template, request, redirect, url_for
# from linebot import LineBotApi
# from linebot.models import TextSendMessage

# app = Flask(__name__)
# submissions = []  # 保存提交的清單
# sent_submissions = set()  # 保存已送出的項目

# channel_access_token = 'YOUR_CHANNEL_ACCESS_TOKEN'

# # 替換為目標用戶的 ID
# user_id = 'TARGET_USER_ID'

# # 初始化 LINE Bot API
# line_bot_api = LineBotApi(channel_access_token)

# @app.route('/', methods=['GET', 'POST'])
# def home():
#     if request.method == 'POST':
#         if 'submit_form' in request.form:
#             # 處理表單提交
#             phone = request.form['phone']
#             option = request.form['option']
#             submission = f"{phone}, {option}"
#             submissions.append(submission)
#         elif 'submit_form2' in request.form:
#             # 處理送出動作
#             submission_to_send = request.form['send']
#             sent_submissions.add(submission_to_send)

#             # 拆分 submission_to_send 以打印 phone 和 option
#             phone, option = submission_to_send.split(', ')
#             print(f"Phone: {phone}")
#             print(f"Option: {option}")

#         return redirect(url_for('home'))
#     return render_template('home.html', submissions=submissions, sent_submissions=sent_submissions)

# @app.route('/about')
# def about():
#     return render_template('about.html')



# if __name__ == '__main__':
#     app.run(debug=True)

# ---------------------
from flask import Flask, render_template, request, redirect, url_for
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)
submissions = []  # 保存提交的清單
sent_submissions = set()  # 保存已送出的項目

# 替換為你的 Channel Access Token
channel_access_token = 'CFpKo+Ei6jeRbHhKFB6H70Fs806m2HIyydxv0GmqKR5d1kgNtBaf6Dq1vPnIVv10RwrrfNPDMLULyAltA6v0ANkq2a3eFnVHChajvOoJfv1YvGpHqTftBXPjl/PwQYzeRbA/yGxFhrcxNZAlPP07LgdB04t89/1O/w1cDnyilFU='

# 替換為目標用戶的 ID
user_id = 'U879e3796fbb1185b9654c34152d07ed9'

# 初始化 LINE Bot API
line_bot_api = LineBotApi(channel_access_token)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'submit_form' in request.form:
            # 處理表單提交
            phone = request.form['phone']
            option = request.form['option']
            submission = f"{phone}, {option}"
            submissions.append(submission)
        elif 'submit_form2' in request.form:
            # 處理送出動作
            submission_to_send = request.form['send']
            sent_submissions.add(submission_to_send)

            # 拆分 submission_to_send 以打印 phone 和 option
            phone, option = submission_to_send.split(', ')
            print(f"Phone: {phone}")
            print(f"Option: {option}")

            # 發送訊息給特定用戶
            sent_education_message(option)
        return redirect(url_for('home'))
    return render_template('home.html', submissions=submissions, sent_submissions=sent_submissions)

@app.route('/about')
def about():
    return render_template('about.html')

def sent_education_message(education_message):
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=education_message))
        print("訊息已發送")
    except Exception as e:
        print(f"發送失敗: {e}")

if __name__ == '__main__':
    app.run(debug=True)
