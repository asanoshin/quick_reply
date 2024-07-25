from flask import Flask, request, jsonify, render_template
from datetime import date, datetime
import psycopg2


app = Flask(__name__)

# # LINE channel access token and secret
# line_bot_api = LineBotApi('bvoaealgSeBUNivXvkNi27W7SFUTwAWmXIshvTZbbiw3aBdqtCN77irNRrXHsrWAlCRlDSYy0vBVLYjJ5pCA/GOuiE+4T8kSCtuaUM5x6eCa2drL2ltM4E707KNQax+HmtCH5bhI/K5LHp8g1xkJQwdB04t89/1O/w1cDnyilFU=')
# handler = WebhookHandler('1bbe70b270080e112f6f495709b43c30')

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

        # 民国年份转换为公历年份
        birthday_year = int(birthday[:3]) + 1911
        birthday_month = int(birthday[3:5])
        birthday_day = int(birthday[5:7])
        print(birthday_year, birthday_month, birthday_day)
        # 计算出生日期
        birth_date = date(birthday_year, birthday_month, birthday_day)
        
        # 计算年龄
        today = date.today()
        age_year = today.year - birth_date.year
        age_month = today.month - birth_date.month
    
        # 如果月份差为负，说明还未到生日，年龄减1，月份加12
        if age_month < 0:
            age_year -= 1
            age_month += 12
        
        # 如果今天日期在生日之前，月份减1
        if today.day < birthday_day:
            age_month -= 1
            if age_month < 0:
                age_year -= 1
                age_month += 12
        
        return age_year, age_month
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

@app.route('/weights', methods=['POST'])
def add_weight():
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
            
            weight = data['value']
            source = 'line' 
            age_year, age_month = calculate_mingo_age(birthday)
            age_in_years = age_year + age_month / 12
            cursor.execute('''
                INSERT INTO child_bw_height_table (source, id_number, age_in_years, record_date, height, weight)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (source, id_number, age_in_years, record_date.date(), None, weight))  # height 為 None，因為您未提供身高值
            print("成功插入體重數據")
            print(source, id_number, age_in_years, record_date.date(), None, weight)

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'status': 'success'}), 201
        return jsonify({'error': '資料不完整'}), 400
    except Exception as e:
        print("An error occurred:", e)
        return jsonify({'error': 'An error occurred'}), 500
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
        SELECT serial_id, record_date, weight
        FROM child_bw_height_table
        WHERE id_number = %s AND weight IS NOT NULL
        ORDER BY record_date
    ''', (id_number,))

    user_weights = cursor.fetchall()

    if not user_weights:
        records =[{'id': user_id, 'date': "", 'weight': "無資料"}]
    else:
        records = [{'id': record[0], 'date': record[1], 'weight': record[2]} for record in user_weights]

    cursor.close()
    conn.close()

    print("user_id", user_id)
    print("user_weights", records)

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
            age_in_years = age_year + age_month / 12
            cursor.execute('''
                INSERT INTO child_bw_height_table (source, id_number, age_in_years, record_date, height, weight)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (source, id_number, age_in_years, record_date.date(), height, None))  # weight 为 None，因为未提供体重值
        
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
        SELECT serial_id, record_date, height
        FROM child_bw_height_table
        WHERE id_number = %s AND height IS NOT NULL
        ORDER BY record_date
    ''', (id_number,))

    user_heights = cursor.fetchall()

    if not user_heights:
        print("yes, it is none")
        records =[{'id': user_id, 'date': "", 'height': "無資料"}]
    else:
        records = [{'id': record[0], 'date': record[1], 'height': record[2]} for record in user_heights]

    cursor.close()
    conn.close()

    print("user_id", user_id)
    print("user_heights", records)

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

        print("baby_data:", baby_data)

        for list in table_list:
            select_sql = f"SELECT 幼兒身分證字號, 出生日期,幼兒姓名 FROM {list} where 聯絡電話 = %s"
            cursor.execute(select_sql, (number,))
            records = cursor.fetchall()

            if records:
                record_number += 1
                if record_number == int(baby_data):
                    nation_id = records[0][0]
                    birthday = records[0][1].replace("-", "")
                    name = records[0][2]
                    break

        return number, nation_id, birthday, name  # 如果沒有找到，返回 True

    except Exception as e:
        print(f"An error occurred while selecting data: {e}")
        return False  # 發生錯誤時返回 False

if __name__ == '__main__':
    app.run(debug=True)
