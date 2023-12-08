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
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
submissions = []  # 用來保存提交的清單

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        phone = request.form['phone']
        option = request.form['option']
        submission = f"{phone}, {option}"
        submissions.append(submission)  # 添加到提交清單
        return redirect(url_for('home'))  # 重新導向到首頁
    return render_template('home.html', submissions=submissions)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
