from flask import Flask, request, jsonify, render_template
from celery.result import AsyncResult
import psycopg2
from datetime import date, datetime
import os

app = Flask(__name__)

DATABASE_URL = 'postgresql://qlinywlvdeayao:74910498f72a2177615b9f280a08235f6543151c8b484a577f87783109c38275@ec2-44-218-23-136.compute-1.amazonaws.com:5432/dd8pvnm4i6jcfe'


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/index2")
def index2():
    return render_template('index2.html')

# Webhook route
# @app.route("/callback", methods=['POST'])
# def callback():
#     # get X-Line-Signature header value
#     signature = request.headers['X-Line-Signature']

#     # get request body as text
#     body = request.get_data(as_text=True)
#     app.logger.info("Request body: " + body)
#     print("-----------------------------body-----------------------------")
#     print(body)
#     print("---------------------------body end test5---------------------------")
#     # handle webhook body
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         abort(400)

#     return 'OK'

# # Handle text messages
# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     if event.message.text == "體重查詢":
#         user_id = event.source.user_id
#         print("user_ide",user_id)
#         reply_message = TextSendMessage(text='請點擊以下連結查詢體重：https://your-liff-app-url')
#         line_bot_api.reply_message(event.reply_token, reply_message)



# # 模擬數據庫
# records = {
#     "weights": [],
#     "heights": []
# }


def calculate_mingo_age(birthday):
    try:

        # # 民国年份转换为公历年份
        # birthday_year = int(birthday[:3]) + 1911
        # birthday_month = int(birthday[3:5])
        # birthday_day = int(birthday[5:7])
        # print(birthday_year, birthday_month, birthday_day)
        # # 计算出生日期
        # birth_date = date(birthday_year, birthday_month, birthday_day)
        
        # # 计算年龄
        # today = date.today()
        # age_year = today.year - birth_date.year
        # age_month = today.month - birth_date.month
    
        # # 如果月份差为负，说明还未到生日，年龄减1，月份加12
        # if age_month < 0:
        #     age_year -= 1
        #     age_month += 12
        
        # # 如果今天日期在生日之前，月份减1
        # if today.day < birthday_day:
        #     age_month -= 1
        #     if age_month < 0:
        #         age_year -= 1
        #         age_month += 12
        
        # return age_year, age_month
                # 民国年份转换为公历年份
        birthday_year = int(birthday[:3]) + 1911
        birthday_month = int(birthday[3:5])
        birthday_day = int(birthday[5:7])
        print(birthday_year, birthday_month, birthday_day)

        # 计算出生日期
        birth_date = date(birthday_year, birthday_month, birthday_day)
        
        # 计算今天的日期
        today = date.today()

        # 计算年份和月份差异
        age_year = today.year - birth_date.year
        age_month = today.month - birth_date.month

        # 如果月份差为负，说明还未到生日，年龄减1，月份加12
        if age_month < 0:
            age_year -= 1
            age_month += 12

        # 计算日期差异，并转换为月份的小数部分
        day_difference = today.day - birthday_day
        days_in_month = 30  # 以平均每月30天计算

        # 如果今天的日在出生日之前，日差为负，需要从月份中减去
        if day_difference < 0:
            age_month -= 1
            day_difference += days_in_month  # 调整为正数
            # 月份减少后，如果月份小于0，则需要调整年份和月份
            if age_month < 0:
                age_year -= 1
                age_month += 12

        # 将日差转换为月份的小数部分
        age_month_decimal = age_month + (day_difference / days_in_month)

        return age_year, age_month_decimal
    except Exception as e:
        print("An error occurred:", e)
        return None, None

@app.route('/name', methods=['GET'])
def get_name():
    user_id = request.args.get('userId')
    if user_id is None:
        return jsonify({'error': 'Missing userId'}), 400

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    number, id_number, birthday, name = select_id1(user_id, cursor)

    cursor.close()
    conn.close()

    return jsonify({'name': name}), 200


def get_growth_data_from_db(month_age, gender):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    conn.autocommit = True

    query = """
    SELECT month_age, height_l, height_m, height_s, height_sd, 
           weight_l, weight_m, weight_s, weight_sd, 
           head_circumference_l, head_circumference_m, head_circumference_s, head_circumference_sd
    FROM growth_percentile_table
    WHERE gender = %s AND month_age = %s
    """
    cur.execute(query, (gender,month_age))
    result = cur.fetchone()
    if not result:
        raise ValueError("No data found for the specified age and gender")
    cur.close()
    conn.close()
    
    return result

def interpolate(age, age_data, percentiles_data):
    if age in age_data:
        print("Exact age found in data")
        return {k: v[age_data.index(age)] for k, v in percentiles_data.items()}

    print("no exact age found in data, try interpolating")
    lower_age = max([a for a in age_data if a < age])
    upper_age = min([a for a in age_data if a > age])

    lower_index = age_data.index(lower_age)
    upper_index = age_data.index(upper_age)

    interpolated_values = {}
    for k in percentiles_data.keys():
        lower_value = percentiles_data[k][lower_index]
        upper_value = percentiles_data[k][upper_index]
        print(f"Interpolating {k} between {lower_value} and {upper_value}")
        print(lower_age ,"+", "(",upper_age,"-",lower_age,")","/", "(",age,"-",lower_age,")")
        interpolated_values[k] = lower_value + (upper_value - lower_value) * ((age - lower_age) / (upper_age - lower_age))

    print(f"Interpolated values for age {age}: {interpolated_values}")
    return interpolated_values

def get_percentile(value, percentiles, percentile_labels):
    for i in range(len(percentiles) - 1):
        print(f"Checking if {percentiles[i]} <= {value} < {percentiles[i + 1]}")
        if percentiles[i] <= value < percentiles[i + 1]:
            return percentile_labels[i]
    if value < percentiles[0]:
        return 'below 3rd percentile'
    elif value >= percentiles[-1]:
        return 'above 97th percentile'


def calculate_weight_percentile_function(status,age, gender, weight):
    girls_weight_data_young = {
    'age_months': list(range(61)),  # 從 0 到 60 月
    'weight_pr3': [2.4, 3.2, 4.0, 4.6, 5.1, 5.5, 5.8, 6.1, 6.3, 6.6, 6.8, 7.0, 7.1, 7.3, 7.5, 7.7, 7.8, 8.0, 8.2, 8.3, 8.5, 8.7, 8.8, 9.0, 9.2, 9.3, 9.5, 9.6, 9.8, 10.0, 10.1, 10.3, 10.4, 10.5, 10.7, 10.8, 11.0, 11.1, 11.2, 11.4, 11.5, 11.6, 11.8, 11.9, 12.0, 12.1, 12.3, 12.4, 12.5, 12.6, 12.8, 12.9, 13.0, 13.1, 13.2, 13.4, 13.5, 13.6, 13.7, 13.8, 14.0],
    'weight_pr15': [2.8, 3.6, 4.5, 5.1, 5.6, 6.1, 6.4, 6.7, 7.0, 7.3, 7.5, 7.7, 7.9, 8.1, 8.3, 8.5, 8.7, 8.8, 9.0, 9.2, 9.4, 9.6, 9.8, 9.9, 10.1, 10.3, 10.5, 10.7, 10.8, 11.0, 11.2, 11.3, 11.5, 11.7, 11.8, 12.0, 12.1, 12.3, 12.5, 12.6, 12.8, 12.9, 13.1, 13.2, 13.4, 13.5, 13.7, 13.8, 14.0, 14.1, 14.3, 14.4, 14.5, 14.7, 14.8, 15.0, 15.1, 15.3, 15.4, 15.5, 15.7],
    'weight_pr25': [2.9, 3.8, 4.7, 5.4, 5.9, 6.4, 6.7, 7.0, 7.3, 7.6, 7.8, 8.0, 8.2, 8.4, 8.6, 8.8, 9.0, 9.2, 9.4, 9.6, 9.8, 10.0, 10.2, 10.4, 10.6, 10.8, 10.9, 11.1, 11.3, 11.5, 11.7, 11.9, 12.0, 12.2, 12.4, 12.5, 12.7, 12.9, 13.0, 13.2, 13.4, 13.5, 13.7, 13.9, 14.0, 14.2, 14.3, 14.5, 14.7, 14.8, 15.0, 15.1, 15.3, 15.4, 15.6, 15.8, 15.9, 16.1, 16.2, 16.4, 16.5],
    'weight_pr50': [3.2, 4.2, 5.1, 5.8, 6.4, 6.9, 7.3, 7.6, 7.9, 8.2, 8.5, 8.7, 8.9, 9.2, 9.4, 9.6, 9.8, 10.0, 10.2, 10.4, 10.6, 10.9, 11.1, 11.3, 11.5, 11.7, 11.9, 12.1, 12.3, 12.5, 12.7, 12.9, 13.1, 13.3, 13.5, 13.7, 13.9, 14.0, 14.2, 14.4, 14.6, 14.8, 15.0, 15.2, 15.3, 15.5, 15.7, 15.9, 16.1, 16.3, 16.4, 16.6, 16.8, 17.0, 17.2, 17.3, 17.5, 17.7, 17.9, 18.0, 18.2],
    'weight_pr75': [3.6, 4.6, 5.6, 6.4, 7.0, 7.5, 7.9, 8.3, 8.6, 8.9, 9.2, 9.5, 9.7, 10.0, 10.2, 10.4, 10.7, 10.9, 11.1, 11.4, 11.6, 11.8, 12.0, 12.3, 12.5, 12.7, 12.9, 13.2, 13.4, 13.6, 13.8, 14.1, 14.3, 14.5, 14.7, 14.9, 15.1, 15.3, 15.6, 15.8, 16.0, 16.2, 16.4, 16.6, 16.8, 17.0, 17.3, 17.5, 17.7, 17.9, 18.1, 18.3, 18.5, 18.7, 18.9, 19.1, 19.3, 19.6, 19.8, 20.0, 20.2],
    'weight_pr85': [3.7, 4.8, 5.9, 6.7, 7.3, 7.8, 8.3, 8.7, 9.0, 9.3, 9.6, 9.9, 10.2, 10.4, 10.7, 10.9, 11.2, 11.4, 11.6, 11.9, 12.1, 12.4, 12.6, 12.8, 13.1, 13.3, 13.6, 13.8, 14.0, 14.3, 14.5, 14.7, 15.0, 15.2, 15.4, 15.7, 15.9, 16.1, 16.3, 16.6, 16.8, 17.0, 17.3, 17.5, 17.7, 17.9, 18.2, 18.4, 18.6, 18.9, 19.1, 19.3, 19.5, 19.8, 20.0, 20.2, 20.4, 20.7, 20.9, 21.1, 21.3],
    'weight_pr97': [4.2, 5.4, 6.5, 7.4, 8.1, 8.7, 9.2, 9.6, 10.0, 10.4, 10.7, 11.0, 11.3, 11.6, 11.9, 12.2, 12.5, 12.7, 13.0, 13.2, 13.5, 13.8, 14.1, 14.3, 14.6, 14.9, 15.2, 15.4, 15.7, 16.0, 16.2, 16.5, 16.8, 17.1, 17.3, 17.6, 17.9, 18.1, 18.4, 18.6, 18.9, 19.2, 19.5, 19.7, 20.0, 20.3, 20.6, 20.8, 21.1, 21.4, 21.7, 22.0, 22.2, 22.5, 22.8, 23.1, 23.3, 23.6, 23.9, 24.2, 24.4]
    }

    girls_weight_data = {
        'age_years': [5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5],
        'weight_pr3': [15.3, 16.3, 17.4, 18.4, 19.4, 20.5, 21.7, 22.8, 24.0, 25.3, 26.8, 28.2, 29.6, 31.8, 34.0, 36.9, 39.7, 41.7, 43.7, 45.4, 47.0, 48.1, 49.1, 49.6, 50.0, 51.0, 51.0],
        'weight_pr15': [17.1, 18.2, 19.3, 20.4, 21.6, 22.8, 24.0, 25.3, 26.5, 28.3, 30.0, 32.5, 35.0, 37.1, 39.1, 40.9, 42.6, 43.8, 45.0, 45.7, 46.3, 46.7, 47.0, 47.2, 47.3, 47.3, 47.3],
        'weight_pr25': [17.9, 19.0, 20.2, 21.3, 22.7, 24.0, 25.4, 26.8, 28.2, 31.8, 34.0, 36.7, 39.4, 41.7, 43.7, 45.4, 47.0, 48.1, 49.1, 49.6, 50.0, 50.5, 51.0, 51.0, 51.0, 51.0, 51.0],
        'weight_pr50': [19.6, 20.9, 22.3, 23.6, 24.0, 25.4, 26.8, 28.2, 29.6, 31.8, 34.0, 36.9, 39.7, 41.7, 43.7, 45.4, 47.0, 48.1, 49.1, 49.6, 50.0, 50.5, 51.0, 51.0, 51.0, 51.0, 51.0],
        'weight_pr75': [21.6, 23.2, 24.7, 26.3, 28.4, 30.8, 33.0, 35.0, 36.9, 39.8, 42.7, 45.5, 48.2, 50.1, 52.0, 53.5, 55.0, 56.0, 57.0, 57.5, 58.0, 58.0, 58.0, 58.0, 58.0, 58.0, 58.0],
        'weight_pr85': [22.9, 24.7, 26.4, 28.2, 30.1, 32.1, 34.0, 36.9, 39.8, 42.7, 45.5, 48.2, 50.1, 52.0, 53.5, 55.0, 56.0, 57.0, 57.5, 58.0, 58.0, 58.0, 58.0, 58.0, 58.0, 58.0, 58.0],
        'weight_pr97': [26.5, 28.6, 30.8, 32.9, 35.0, 37.8, 40.5, 42.8, 45.0, 47.3, 49.6, 52.7, 55.8, 57.8, 59.7, 61.2, 62.7, 63.9, 65.0, 65.5, 66.0, 66.2, 66.4, 66.7, 67.0, 67.0, 67.0]
    }

    # 男生體重資料
    boys_weight_data_young = {
    'age_months': list(range(61)),  # 從 0 到 60 月
    'weight_pr3': [2.5, 3.4, 4.4, 5.1, 5.6, 6.1, 6.4, 6.7, 7.0, 7.2, 7.5, 7.7, 7.8, 8.0, 8.2, 8.4, 8.5, 8.7, 8.9, 9.0, 9.2, 9.3, 9.5, 9.7, 9.8, 10.0, 10.1, 10.2, 10.4, 10.5, 10.7, 10.8, 10.9, 11.1, 11.2, 11.3, 11.4, 11.6, 11.7, 11.8, 11.9, 12.1, 12.2, 12.3, 12.4, 12.5, 12.7, 12.8, 12.9, 13.0, 13.1, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 14.1, 14.2, 14.3],
    'weight_pr15': [2.9, 3.9, 4.9, 5.6, 6.2, 6.7, 7.1, 7.4, 7.7, 7.9, 8.2, 8.4, 8.6, 8.8, 9.0, 9.2, 9.4, 9.6, 9.7, 9.9, 10.1, 10.3, 10.5, 10.6, 10.8, 11.0, 11.1, 11.3, 11.5, 11.6, 11.8, 11.9, 12.1, 12.2, 12.4, 12.5, 12.7, 12.8, 12.9, 13.1, 13.2, 13.4, 13.5, 13.6, 13.8, 13.9, 14.1, 14.2, 14.3, 14.5, 14.6, 14.7, 14.9, 15.0, 15.2, 15.3, 15.4, 15.6, 15.7, 15.8, 16.0],
    'weight_pr25': [3.0, 4.1, 5.1, 5.9, 6.5, 7.0, 7.4, 7.7, 8.0, 8.3, 8.5, 8.7, 9.0, 9.2, 9.4, 9.6, 9.8, 10.0, 10.1, 10.3, 10.5, 10.7, 10.9, 11.1, 11.3, 11.4, 11.6, 11.8, 12.0, 12.1, 12.3, 12.4, 12.6, 12.8, 12.9, 13.1, 13.2, 13.4, 13.5, 13.7, 13.8, 14.0, 14.1, 14.3, 14.4, 14.6, 14.7, 14.9, 15.0, 15.2, 15.3, 15.4, 15.6, 15.7, 15.9, 16.0, 16.2, 16.3, 16.5, 16.6, 16.7],
    'weight_pr50': [3.3, 4.5, 5.6, 6.4, 7.0, 7.5, 7.9, 8.3, 8.6, 8.9, 9.2, 9.4, 9.6, 9.9, 10.1, 10.3, 10.5, 10.7, 10.9, 11.1, 11.3, 11.5, 11.8, 12.0, 12.2, 12.4, 12.5, 12.7, 12.9, 13.1, 13.3, 13.5, 13.7, 13.8, 14.0, 14.2, 14.3, 14.5, 14.7, 14.8, 15.0, 15.2, 15.3, 15.5, 15.7, 15.8, 16.0, 16.2, 16.3, 16.5, 16.7, 16.8, 17.0, 17.2, 17.3, 17.5, 17.7, 17.8, 18.0, 18.2, 18.3],
    'weight_pr75': [3.7, 4.9, 6.0, 6.9, 7.6, 8.1, 8.5, 8.9, 9.3, 9.6, 9.9, 10.1, 10.4, 10.6, 10.9, 11.1, 11.3, 11.6, 11.8, 12.0, 12.2, 12.5, 12.7, 12.9, 13.1, 13.3, 13.6, 13.8, 14.0, 14.2, 14.4, 14.6, 14.8, 15.0, 15.2, 15.4, 15.6, 15.8, 15.9, 16.1, 16.3, 16.5, 16.7, 16.9, 17.1, 17.3, 17.4, 17.6, 17.8, 18.0, 18.2, 18.4, 18.6, 18.8, 19.0, 19.2, 19.3, 19.5, 19.7, 19.9, 20.1],
    'weight_pr85': [3.9, 5.1, 6.3, 7.2, 7.9, 8.4, 8.9, 9.3, 9.6, 10.0, 10.3, 10.5, 10.8, 11.1, 11.3, 11.6, 11.8, 12.0, 12.3, 12.5, 12.7, 13.0, 13.2, 13.4, 13.7, 13.9, 14.1, 14.4, 14.6, 14.8, 15.0, 15.2, 15.5, 15.7, 15.9, 16.1, 16.3, 16.5, 16.7, 16.9, 17.1, 17.3, 17.5, 17.7, 17.9, 18.1, 18.3, 18.5, 18.7, 18.9, 19.1, 19.3, 19.5, 19.7, 19.9, 20.1, 20.3, 20.5, 20.7, 20.9, 21.1],
    'weight_pr97': [4.3, 5.7, 7.0, 7.9, 8.6, 9.2, 9.7, 10.2, 10.5, 10.9, 11.2, 11.5, 11.8, 12.1, 12.4, 12.7, 12.9, 13.2, 13.5, 13.7, 14.0, 14.3, 14.5, 14.8, 15.1, 15.3, 15.6, 15.9, 16.1, 16.4, 16.6, 16.9, 17.1, 17.3, 17.6, 17.8, 18.0, 18.3, 18.5, 18.7, 19.0, 19.2, 19.4, 19.7, 19.9, 20.1, 20.4, 20.6, 20.9, 21.1, 21.3, 21.6, 21.8, 22.1, 22.3, 22.5, 22.8, 23.0, 23.3, 23.5, 23.8]
    }

    boys_weight_data = {
        'age_years': [5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5],
        'weight_pr3': [15.3, 16.3, 17.4, 18.4, 19.4, 20.3, 21.2, 22.1, 23.0, 24.0, 25.0, 26.3, 27.6, 29.3, 30.5, 32.8, 35.0, 38.0, 41.0, 43.0, 45.0, 46.8, 48.5, 49.3, 50.0, 50.3, 50.5],
        'weight_pr15': [17.1, 18.2, 19.3, 20.4, 21.5, 22.7, 23.8, 24.8, 25.8, 26.9, 28.0, 29.6, 31.2, 33.1, 35.0, 38.0, 41.0, 44.0, 47.0, 49.0, 51.0, 52.0, 53.0, 54.0, 55.0, 55.0, 55.0],
        'weight_pr25': [17.9, 19.0, 20.2, 21.3, 22.5, 23.8, 25.0, 26.0, 27.0, 28.4, 29.8, 31.4, 33.0, 35.2, 37.3, 40.7, 44.0, 46.8, 49.5, 51.3, 53.0, 54.1, 55.1, 56.1, 57.0, 57.5, 58.0],
        'weight_pr50': [19.6, 20.9, 22.3, 23.6, 24.9, 26.3, 27.6, 28.8, 30.0, 31.5, 33.0, 35.3, 37.6, 40.3, 43.0, 46.5, 50.0, 52.5, 54.9, 56.5, 58.0, 59.0, 60.0, 61.0, 62.0, 62.5, 63.0],
        'weight_pr75': [21.6, 23.2, 24.7, 26.3, 27.8, 29.6, 31.4, 32.7, 34.0, 36.0, 38.0, 40.8, 43.5, 46.5, 49.5, 53.0, 56.4, 58.7, 61.0, 62.5, 64.0, 65.0, 66.0, 66.6, 67.2, 67.6, 68.0],
        'weight_pr85': [22.9, 24.7, 26.4, 28.2, 30.0, 32.2, 34.3, 35.7, 37.0, 39.4, 41.8, 44.7, 47.5, 50.4, 53.2, 56.8, 60.4, 62.7, 65.0, 66.5, 68.0, 69.0, 70.0, 70.0, 70.0, 70.5, 71.0],
        'weight_pr97': [26.5, 29.2, 32.0, 34.7, 37.4, 40.2, 42.3, 44.3, 45.6, 48.6, 51.6, 54.8, 58.0, 61.5, 65.0, 68.5, 72.0, 74.3, 76.6, 77.6, 78.5, 79.3, 80.0, 80.0, 80.0, 80.0, 80.0]
    }



    # 定義方法
    try:
        def calculate_weight_percentiles(gender, age, weight):
            weight_percentile = None

            try:
                if weight is not None:
                    if gender == 'boy' and status == 'young':
                        weight_data = boys_weight_data_young
                    elif gender == 'boy' and status == 'old': 
                        weight_data = boys_weight_data
                    elif gender == 'girl' and status == 'young':
                        weight_data = girls_weight_data_young
                    elif gender == 'girl' and status == 'old':
                        weight_data = girls_weight_data
                    else:
                        return None, None

                    if status == 'young':
                        print("try to interpolate;", "age:", age, "weight_data['age_months']:", weight_data['age_months'], "weight_data:", weight_data)
                        age_data_weight = interpolate(age, weight_data['age_months'], weight_data)
                    else:
                        age_data_weight = interpolate(age, weight_data['age_years'], weight_data)

                    weight_percentiles = [
                        age_data_weight['weight_pr3'], age_data_weight['weight_pr15'],
                        age_data_weight['weight_pr25'], age_data_weight['weight_pr50'],
                        age_data_weight['weight_pr75'], age_data_weight['weight_pr85'],
                        age_data_weight['weight_pr97']
                    ]
                    percentile_labels = [
                        '3rd-15th %', '15th-25th %', '25th-50th %',
                        '50th-75th %', '75th-85th %', '85th-97th %'
                    ]
                    weight_percentile = get_percentile(weight, weight_percentiles, percentile_labels)
                
                return weight_percentile
            except Exception as e:
                print("An error occurred when calculate older precentiles:", e)
                return None, None

        weight_percentile = calculate_weight_percentiles(gender, age, weight)
        print("get weight_percentile:", weight_percentile)
        return weight_percentile
    except Exception as e:
        print("An error occurred when calculate older percentile function:", e)
        return None, None   

# weight_percent = calculate_weight_percentile_function('young',0.041666666666666664,'girl',3.275)
# print("weight_percent:", weight_percent)
# input("Press Enter to continue...")

@app.route('/weights', methods=['POST'])
def add_weight():
    try:
        # print("進入 add_weight")
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        data = request.get_json()
        if 'date' in data and 'value' in data and 'userId' in data:

            user_id = data['userId']
            number, id_number, birthday, name = select_id1(user_id, cursor)
            record_date = data['date']
            try:
                record_date = datetime.strptime(record_date, '%Y-%m-%d')  # 假设日期格式为 'YYYY-MM-DD'
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
            
            weight = data['value']
            source = 'line' 
            age_year, age_month = calculate_mingo_age(birthday)

            gender_code = id_number[1]  # 獲取 id_number 的第二個字符
            gender = 'boy' if gender_code == '1' else 'girl'
                    
            month_age = age_year * 12 + age_month

            if month_age <= 60:
                status = 'young'
                print("status:", status,";month_age:", month_age,";weight:", weight)
                weight_percentile= calculate_weight_percentile_function(
                    status,month_age, gender, weight=float(weight) if weight is not None else None)
                print("weight_percentile:", weight_percentile)
            else:
                year_age = month_age / 12
                status = 'old'
                weight_percentile = calculate_weight_percentile_function(
                    status ,year_age, gender, weight=float(weight) if weight is not None else None)
                print("weight_percentile:", weight_percentile)

            age_in_years = age_year + age_month / 12
            cursor.execute('''
                INSERT INTO child_bw_height_table (source, id_number, age_in_years, record_date, weight,weight_percentile)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (source, id_number, age_in_years, record_date.date(), weight, weight_percentile))

            conn.commit()
            print('source:', source,';id_number:', id_number,';age_in_years:', age_in_years,';record_date:', record_date.date(),'weight:', weight,'weight_percentile:', weight_percentile)
            return jsonify({'status': 'success'}), 201
        return jsonify({'error': '資料不完整'}), 400
    except Exception as e:
        print("An error occurred:", e)
        return jsonify({'error': f'An error occurred:{e}'}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/weights', methods=['GET'])
def get_weights():
    user_id = request.args.get('userId')
    if user_id is None:
        return jsonify({'error': 'Missing userId'}), 400
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    number, id_number, birthday, name = select_id1(user_id, cursor)

    cursor.execute('''
        SELECT serial_id, record_date, weight, weight_percentile
        FROM child_bw_height_table
        WHERE id_number = %s AND weight IS NOT NULL
        ORDER BY record_date
    ''', (id_number,))

    user_weights = cursor.fetchall()

    if not user_weights:
        records =[{'id': user_id, 'date': "", 'weight': "無資料", 'percentile': ""}]
    else:
        records = [{'id': record[0], 'date': record[1], 'weight': record[2], 'percentile': record[3] if record[3] is not None else ""} for record in user_weights]

    cursor.close()
    conn.close()

    # print("user_id", user_id)
    # print("user_weights", records)

    return jsonify(records), 200

@app.route('/weights/<int:record_id>', methods=['DELETE'])
def delete_weight(record_id):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM child_bw_height_table
        WHERE serial_id = %s
    ''', (record_id,))

    conn.commit()
    rowcount = cursor.rowcount
    cursor.close()
    conn.close()

    if rowcount == 0:
        return jsonify({'error': 'Record not found'}), 404

    return '', 204

def calculate_height_percentile_function(status,age, gender, height):
    # 女生身高資料
    
    girls_height_data_young = {
        'age_months': list(range(61)),  # 從 0 到 60 月
        'height_pr3': [45.6, 50.0, 53.2, 55.8, 58.0, 59.9, 61.5, 62.9, 64.3, 65.6, 66.8, 68.0, 69.2, 70.3, 71.3, 72.4, 73.3, 74.3, 75.2, 76.2, 77.0, 77.9, 78.7, 79.6, 79.6, 80.4, 81.2, 81.9, 82.6, 83.4, 84.0, 84.7, 85.4, 86.0, 86.7, 87.3, 87.9, 88.5, 89.1, 89.7, 90.3, 90.8, 91.4, 92.0, 92.5, 93.0, 93.6, 94.1, 94.6, 95.1, 95.7, 96.2, 96.7, 97.2, 97.6, 98.1, 98.6, 99.1, 99.6, 100.0, 100.5],
        'height_pr15': [47.2, 51.7, 55.0, 57.6, 59.8, 61.7, 63.4, 64.9, 66.3, 67.6, 68.9, 70.2, 71.3, 72.5, 73.6, 74.7, 75.7, 76.7, 77.7, 78.7, 79.6, 80.5, 81.4, 82.2, 82.4, 83.2, 84.0, 84.8, 85.5, 86.3, 87.0, 87.7, 88.4, 89.1, 89.8, 90.5, 91.1, 91.7, 92.4, 93.0, 93.6, 94.2, 94.8, 95.4, 96.0, 96.6, 97.2, 97.7, 98.3, 98.8, 99.4, 99.9, 100.4, 101.0, 101.5, 102.0, 102.5, 103.0, 103.5, 104.0, 104.5],
        'height_pr25': [47.9, 52.4, 55.7, 58.4, 60.6, 62.5, 64.2, 65.7, 67.2, 68.5, 69.8, 71.1, 72.3, 73.4, 74.6, 75.7, 76.7, 77.7, 78.7, 79.7, 80.7, 81.6, 82.5, 83.4, 83.5, 84.4, 85.2, 86.0, 86.8, 87.6, 88.3, 89.0, 89.7, 90.4, 91.1, 91.8, 92.5, 93.1, 93.8, 94.4, 95.1, 95.7, 96.3, 96.9, 97.5, 98.1, 98.7, 99.3, 99.8, 100.4, 100.9, 101.5, 102.0, 102.6, 103.1, 103.6, 104.2, 104.7, 105.2, 105.7, 106.2],
        'height_pr50': [49.1, 53.7, 57.1, 59.8, 62.1, 64.0, 65.7, 67.3, 68.7, 70.1, 71.5, 72.8, 74.0, 75.2, 76.4, 77.5, 78.6, 79.7, 80.7, 81.7, 82.7, 83.7, 84.6, 85.5, 85.7, 86.6, 87.4, 88.3, 89.1, 89.9, 90.7, 91.4, 92.2, 92.9, 93.6, 94.4, 95.1, 95.7, 96.4, 97.1, 97.7, 98.4, 99.0, 99.7, 100.3, 101.0, 101.5, 102.1, 102.7, 103.3, 103.9, 104.5, 105.0, 105.6, 106.2, 106.7, 107.3, 107.8, 108.4, 108.9, 109.4],
        'height_pr75': [50.4, 55.0, 58.4, 61.2, 63.5, 65.5, 67.3, 68.8, 70.3, 71.8, 73.1, 74.5, 75.8, 77.0, 78.2, 79.4, 80.5, 81.6, 82.7, 83.7, 84.7, 85.7, 86.7, 87.7, 87.9, 88.8, 89.7, 90.6, 91.4, 92.2, 93.1, 93.9, 94.6, 95.4, 96.2, 96.9, 97.6, 98.3, 99.0, 99.7, 100.4, 101.1, 101.8, 102.4, 103.1, 103.7, 104.4, 105.0, 105.6, 106.3, 106.9, 107.5, 108.1, 108.6, 109.2, 109.8, 110.4, 111.0, 111.5, 112.1, 112.6],
        'height_pr85': [51.1, 55.7, 59.2, 62.0, 64.3, 66.3, 68.1, 69.7, 71.2, 72.6, 74.0, 75.4, 76.7, 77.9, 79.2, 80.3, 81.5, 82.6, 83.7, 84.8, 85.8, 86.8, 87.8, 88.8, 89.1, 90.0, 90.9, 91.8, 92.7, 93.5, 94.3, 95.2, 95.9, 96.7, 97.5, 98.3, 99.0, 99.7, 100.5, 101.2, 101.9, 102.6, 103.3, 103.9, 104.6, 105.3, 105.9, 106.6, 107.2, 107.8, 108.4, 109.1, 109.7, 110.3, 110.9, 111.5, 112.1, 112.6, 113.2, 113.8, 114.4],
        'height_pr97': [52.7, 57.4, 60.9, 63.8, 66.2, 68.2, 70.0, 71.6, 73.2, 74.7, 76.1, 77.5, 78.9, 80.2, 81.4, 82.7, 83.9, 85.0, 86.2, 87.3, 88.4, 89.4, 90.5, 91.5, 91.8, 92.8, 93.7, 94.6, 95.6, 96.4, 97.3, 98.2, 99.0, 99.8, 100.6, 101.4, 102.2, 103.0, 103.7, 104.5, 105.2, 106.0, 106.7, 107.4, 108.1, 108.8, 109.5, 110.2, 110.8, 111.5, 112.1, 112.8, 113.4, 114.1, 114.7, 115.3, 116.0, 116.6, 117.2, 117.8, 118.4]
    }

    girls_height_data = {
        'age_years': [5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5],
        'height_pr3': [103.0, 105.5, 108.1, 110.6, 113.1, 115.7, 118.3, 120.7, 123.0, 125.8, 128.5, 131.8, 135.0, 137.9, 140.8, 143.2, 145.5, 146.8, 148.0, 148.5, 149.0, 149.5, 150.0, 150.0, 150.0, 150.0, 150.0],
        'height_pr15': [107.1, 109.7, 112.3, 114.9, 117.5, 120.3, 123.0, 125.5, 128.0, 131.0, 134.0, 137.5, 141.0, 143.8, 146.5, 148.5, 150.5, 151.3, 152.0, 152.5, 153.0, 153.5, 154.0, 154.0, 154.0, 154.0, 154.0],
        'height_pr25': [108.8, 111.3, 113.9, 116.4, 119.0, 122.0, 125.0, 127.5, 130.0, 133.0, 136.0, 139.8, 143.5, 146.3, 149.0, 150.7, 152.4, 153.2, 154.0, 154.5, 155.0, 155.3, 155.5, 155.8, 156.0, 156.0, 156.0],
        'height_pr50': [112.1, 114.8, 117.6, 120.3, 123.0, 125.8, 128.5, 131.3, 134.0, 137.5, 141.0, 144.5, 148.0, 150.5, 153.0, 154.5, 156.0, 156.8, 157.5, 157.9, 158.3, 158.7, 159.0, 159.3, 159.5, 159.5, 159.5],
        'height_pr75': [115.3, 118.0, 120.8, 123.5, 126.2, 129.2, 132.2, 135.4, 138.5, 142.3, 146.0, 149.4, 152.7, 154.9, 157.0, 158.4, 159.7, 160.4, 161.0, 161.5, 162.0, 162.3, 162.5, 162.8, 163.0, 163.0, 163.0],
        'height_pr85': [117.1, 119.9, 122.6, 125.4, 128.1, 131.3, 134.5, 137.8, 141.0, 144.8, 148.5, 151.8, 155.0, 157.0, 159.0, 160.3, 161.5, 162.3, 163.0, 163.5, 164.0, 164.2, 164.4, 164.7, 165.0, 165.0, 165.0],
        'height_pr97': [121.3, 124.2, 127.2, 130.1, 133.0, 136.5, 140.0, 143.5, 147.0, 150.8, 154.5, 157.3, 160.0, 161.8, 163.5, 164.8, 166.0, 167.0, 167.9, 168.2, 168.5, 168.8, 169.0, 169.0, 169.0, 169.0, 169.0]
    }


    # 男生身高資料
    boys_height_data_young = {
    'age_months': list(range(61)),  # 從 0 到 60 月
    'height_pr3': [46.3, 51.1, 54.7, 57.6, 60.0, 61.9, 63.6, 65.1, 66.5, 67.7, 69.0, 70.2, 71.3, 72.4, 73.4, 74.4, 75.4, 76.3, 77.2, 78.1, 78.9, 79.7, 80.5, 81.3, 81.4, 82.1, 82.8, 83.5, 84.2, 84.9, 85.5, 86.2, 86.8, 87.4, 88.0, 88.5, 89.1, 89.7, 90.2, 90.8, 91.3, 91.9, 92.4, 92.9, 93.4, 93.9, 94.4, 94.9, 95.4, 95.9, 96.4, 96.9, 97.4, 97.9, 98.4, 98.8, 99.3, 99.8, 100.3, 100.8, 101.2],
    'height_pr15': [47.9, 52.7, 56.4, 59.3, 61.7, 63.7, 65.4, 66.9, 68.3, 69.6, 70.9, 72.1, 73.3, 74.4, 75.5, 76.5, 77.5, 78.5, 79.5, 80.4, 81.3, 82.2, 83.0, 83.8, 83.9, 84.7, 85.5, 86.3, 87.0, 87.7, 88.4, 89.1, 89.7, 90.4, 91.0, 91.6, 92.2, 92.8, 93.4, 94.0, 94.6, 95.2, 95.7, 96.3, 96.8, 97.4, 97.9, 98.5, 99.0, 99.5, 100.0, 100.5, 101.1, 101.6, 102.1, 102.6, 103.1, 103.6, 104.1, 104.7, 105.2],
    'height_pr25': [48.6, 53.4, 57.1, 60.1, 62.5, 64.5, 66.2, 67.7, 69.1, 70.5, 71.7, 73.0, 74.1, 75.3, 76.4, 77.4, 78.5, 79.5, 80.4, 81.4, 82.3, 83.2, 84.1, 84.9, 85.1, 85.9, 86.7, 87.4, 88.2, 88.9, 89.6, 90.3, 91.0, 91.7, 92.3, 93.0, 93.6, 94.2, 94.8, 95.4, 96.0, 96.6, 97.2, 97.7, 98.3, 98.9, 99.4, 100.0, 100.5, 101.0, 101.6, 102.1, 102.6, 103.2, 103.7, 104.2, 104.7, 105.3, 105.8, 106.3, 106.8],
    'height_pr50': [49.9, 54.7, 58.4, 61.4, 63.9, 65.9, 67.6, 69.2, 70.6, 72.0, 73.3, 74.5, 75.7, 76.9, 78.0, 79.1, 80.2, 81.2, 82.3, 83.2, 84.2, 85.1, 86.0, 86.9, 87.1, 88.0, 88.8, 89.6, 90.4, 91.2, 91.9, 92.7, 93.4, 94.1, 94.8, 95.4, 96.1, 96.7, 97.4, 98.0, 98.6, 99.2, 99.9, 100.4, 101.0, 101.6, 102.2, 102.8, 103.3, 103.9, 104.4, 105.0, 105.6, 106.1, 106.7, 107.2, 107.8, 108.3, 108.9, 109.4, 110.0],
    'height_pr75': [51.2, 56.0, 59.8, 62.8, 65.3, 67.3, 69.1, 70.6, 72.1, 73.5, 74.8, 76.1, 77.4, 78.6, 79.7, 80.9, 82.0, 83.0, 84.1, 85.1, 86.1, 87.1, 88.0, 89.0, 89.2, 90.1, 90.9, 91.8, 92.6, 93.4, 94.2, 95.0, 95.7, 96.5, 97.2, 97.9, 98.6, 99.3, 99.9, 100.6, 101.3, 101.9, 102.5, 103.1, 103.8, 104.4, 105.0, 105.6, 106.2, 106.7, 107.3, 107.9, 108.5, 109.1, 109.6, 110.2, 110.8, 111.4, 111.9, 112.5, 113.1],
    'height_pr85': [51.8, 56.7, 60.5, 63.5, 66.0, 68.1, 69.8, 71.4, 72.9, 74.3, 75.6, 77.0, 78.2, 79.4, 80.6, 81.8, 82.9, 84.0, 85.1, 86.1, 87.1, 88.1, 89.1, 90.0, 90.3, 91.2, 92.1, 93.0, 93.8, 94.7, 95.5, 96.2, 97.0, 97.8, 98.5, 99.2, 99.9, 100.6, 101.3, 102.0, 102.7, 103.3, 104.0, 104.6, 105.2, 105.8, 106.5, 107.1, 107.7, 108.3, 108.9, 109.5, 110.1, 110.7, 111.2, 111.8, 112.4, 113.0, 113.6, 114.2, 114.8],
    'height_pr97': [53.4, 58.4, 62.2, 65.3, 67.8, 69.9, 71.6, 73.2, 74.7, 76.2, 77.6, 78.9, 80.2, 81.5, 82.7, 83.9, 85.1, 86.2, 87.3, 88.4, 89.5, 90.5, 91.6, 92.6, 92.9, 93.8, 94.8, 95.7, 96.6, 97.5, 98.3, 99.2, 100.0, 100.8, 101.5, 102.3, 103.1, 103.8, 104.5, 105.2, 105.9, 106.6, 107.3, 108.0, 108.6, 109.3, 109.9, 110.6, 111.2, 111.8, 112.5, 113.1, 113.7, 114.3, 115.0, 115.6, 116.2, 116.8, 117.4, 118.1, 118.7]
    }

    boys_height_data = {
        'age_years': [5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5],
        'height_pr3': [103.9, 106.5, 109.2, 111.8, 114.5, 117.0, 119.5, 121.8, 124.0, 126.0, 128.0, 130.5, 133.0, 135.6, 138.2, 141.9, 145.5, 149.3, 153.0, 155.5, 158.0, 159.3, 160.5, 160.9, 161.0, 161.5, 162.0],
        'height_pr15': [107.9, 110.5, 113.2, 115.8, 118.5, 121.3, 124.0, 126.0, 128.0, 130.5, 133.0, 135.6, 138.1, 141.1, 144.0, 148.5, 153.0, 156.3, 159.6, 161.3, 163.0, 164.0, 165.0, 165.5, 166.0, 166.0, 166.0],
        'height_pr25': [109.5, 112.3, 115.0, 117.8, 120.5, 123.3, 126.0, 128.0, 130.0, 132.5, 135.0, 137.8, 140.5, 143.8, 147.0, 151.5, 156.0, 159.0, 162.0, 163.5, 165.0, 166.2, 167.3, 167.7, 168.0, 168.0, 168.0],
        'height_pr50': [112.8, 115.6, 118.4, 121.2, 124.0, 126.8, 129.5, 131.8, 134.0, 136.5, 139.0, 142.0, 145.0, 148.8, 152.5, 156.9, 161.2, 163.7, 166.2, 167.6, 169.0, 170.0, 171.0, 171.5, 172.0, 172.0, 172.0],
        'height_pr75': [116.0, 118.9, 121.7, 124.6, 127.5, 130.3, 133.0, 135.5, 138.0, 140.5, 143.0, 146.7, 150.4, 154.2, 158.0, 162.0, 166.0, 168.3, 170.5, 171.8, 173.0, 173.8, 174.5, 174.8, 175.0, 175.0, 175.0],
        'height_pr85': [117.7, 120.6, 123.6, 126.5, 129.4, 132.2, 135.0, 137.5, 140.0, 142.8, 145.5, 149.4, 153.2, 157.1, 161.0, 164.9, 168.7, 170.8, 172.8, 173.9, 175.0, 175.8, 176.5, 176.8, 177.0, 177.3, 177.5],
        'height_pr97': [121.8, 124.9, 128.1, 131.2, 134.3, 137.2, 140.0, 142.5, 145.0, 148.3, 151.5, 156.1, 160.7, 164.4, 168.0, 171.0, 174.0, 176.0, 178.0, 179.0, 180.0, 180.5, 181.0, 181.5, 182.0, 182.0, 182.0]
    }


    # 定義方法
    try:
        def calculate_height_percentiles(gender, age, height):
            height_percentile = None

            try:
                if height is not None:
                    if gender == 'boy' and status == 'young':
                        height_data = boys_height_data_young
                    elif gender == 'boy' and status == 'old': 
                        height_data = boys_height_data
                    elif gender == 'girl' and status == 'young':
                        height_data = girls_height_data_young
                    elif gender == 'girl' and status == 'old':
                        height_data = girls_height_data
                    else:
                        return None, None

                    if status == 'young':
                        age_data_height = interpolate(age, height_data['age_months'], height_data)
                    else:
                        age_data_height = interpolate(age, height_data['age_years'], height_data)

                    height_percentiles = [
                        age_data_height['height_pr3'], age_data_height['height_pr15'],
                        age_data_height['height_pr25'], age_data_height['height_pr50'],
                        age_data_height['height_pr75'], age_data_height['height_pr85'],
                        age_data_height['height_pr97']
                    ]
                    percentile_labels = [
                        '3rd-15th %', '15th-25th %', '25th-50th %',
                        '50th-75th %', '75th-85th %', '85th-97th %'
                    ]
                    height_percentile = get_percentile(height, height_percentiles, percentile_labels)
                
                return height_percentile
            except Exception as e:
                print("An error occurred when calculate older precentiles:", e)
                return None, None

        height_percentile = calculate_height_percentiles(gender, age, height)
        print("get height_percentile:", height_percentile)
        return height_percentile
    except Exception as e:
        print("An error occurred when calculate older percentile function:", e)
        return None, None   


@app.route('/heights', methods=['POST'])
def add_height():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        data = request.get_json()
        if 'date' in data and 'value' in data and 'userId' in data:
            user_id = data['userId']
            number, id_number, birthday, name = select_id1(user_id, cursor)
            record_date = data['date']
            try:
                record_date = datetime.strptime(record_date, '%Y-%m-%d')  # 假设日期格式为 'YYYY-MM-DD'
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
            
            height = data['value']
            source = 'line'
            age_year, age_month = calculate_mingo_age(birthday)

            gender_code = id_number[1]  # 獲取 id_number 的第二個字符
            gender = 'boy' if gender_code == '1' else 'girl'
                    
            month_age = age_year * 12 + age_month

            if month_age <= 60:
                status = 'young'
                height_percentile= calculate_height_percentile_function(
                    status,month_age, gender, height=float(height) if height is not None else None)
                print("height_percentile:", height_percentile)
            else:
                year_age = month_age / 12
                status = 'old'
                height_percentile = calculate_height_percentile_function(
                    status, year_age, gender, height=float(height) if height is not None else None)
                print("height_percentile:", height_percentile)



            age_in_years = age_year + age_month / 12
            cursor.execute('''
                INSERT INTO child_bw_height_table (source, id_number, age_in_years, record_date, height, height_percentile)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (source, id_number, age_in_years, record_date.date(), height, height_percentile))

            print(source, id_number, age_in_years, record_date.date(), height, height_percentile)
        
            conn.commit()
            cursor.close()
            conn.close()

            print(source, id_number, age_in_years, record_date.date(), height, None)
            return jsonify({'status': 'success'}), 201
        return jsonify({'error': '数据不完整'}), 400
    except Exception as e:
        print("An error occurred:", e)
        return jsonify({'error': 'An error occurred'}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/heights', methods=['GET'])
def get_heights():
    user_id = request.args.get('userId')
    if user_id is None:
        return jsonify({'error': 'Missing userId'}), 400
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    
    number, id_number, birthday, name = select_id1(user_id, cursor)


    cursor.execute('''
        SELECT serial_id, record_date, height, height_percentile
        FROM child_bw_height_table
        WHERE id_number = %s AND height IS NOT NULL
        ORDER BY record_date
    ''', (id_number,))

    user_heights = cursor.fetchall()

    if not user_heights:
        print("yes, it is none")
        records =[{'id': user_id, 'date': "", 'height': "無資料", 'percentile': ""}]
    else:
        records = [{'id': record[0], 'date': record[1], 'height': record[2], 'percentile': record[3] if record[3] is not None else ""} for record in user_heights]

    cursor.close()
    conn.close()

    # print("user_id", user_id)
    # print("user_heights", records)

    return jsonify(records), 200

@app.route('/heights/<int:record_id>', methods=['DELETE'])
def delete_height(record_id):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM child_bw_height_table
        WHERE serial_id = %s
    ''', (record_id,))

    conn.commit()
    rowcount = cursor.rowcount
    cursor.close()
    conn.close()

    print("success delet height")

    if rowcount == 0:
        return jsonify({'error': 'Record not found'}), 404

    return '', 204


def select_id1(user_id, cursor):
    """檢查資料庫中是否存在給定的用戶 ID"""
    try:

        # 查詢資料庫中是否有給定的用戶 ID , 且 delete_date 是 NULL
        select_query = f"SELECT number, baby_data FROM id_table11 WHERE id = %s AND delete_date IS NULL"
        cursor.execute(select_query, (user_id,))
        number, baby_data = cursor.fetchone()

        table_list = ['crp_huang_table', 'crp_lin_table', 'crp_wang_table', 'crp_li_table']
        record_number =0

        # print("baby_data:", baby_data)

        for list in table_list:
            select_sql = f"SELECT 幼兒身分證字號, 出生日期,幼兒姓名 FROM {list} where 聯絡電話 = %s"
            cursor.execute(select_sql, (number,))
            records = cursor.fetchall()
            if records:
                record_number += len(records)  # Counting all fetched records
                
                # If the number of accumulated records is less than or equal to the target baby_data
                if record_number >= int(baby_data):
                    # Fetch the last record's data as specified
                    target_index = min(int(baby_data) - 1, len(records) - 1)  # Ensuring we do not go out of index
                    nation_id = records[target_index][0]
                    birthday = records[target_index][1].replace("-", "")
                    name = records[target_index][2]
                    break
                else:
                    baby_data= int(baby_data) - len(records)  
                    print(f"{list} has {len(records)} records, and baby_data is now {baby_data}")

        return number, nation_id, birthday, name  # 如果沒有找到，返回 True

    except Exception as e:
        print(f"An error occurred while selecting data: {e}")
        return False  # 發生錯誤時返回 False

if __name__ == '__main__':
    app.run(debug=True)
