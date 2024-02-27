import time

from flask import Flask, Response, session,render_template

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route('/set')
def set_session():
    session['uploaded_indication'] = 'example'
    return 'Session value set.'
@app.route('/')
def home():
    return render_template('index2.html')

@app.route('/stream')
def stream():
    # 在生成器外部访问session，并将值传递给生成器
    uploaded_indication = session.get('uploaded_indication')
    aa='Data based on session value'

    def generate(uploaded_indication):
        # 使用传入的参数而不是直接在生成器内部访问session
        if uploaded_indication != None:
            for i in aa:
                time.sleep(0.1)
                print(i)
                yield i
        else:
            yield 'No session value set\n'

    return Response(generate(uploaded_indication), content_type='application/octet-stream')


if __name__ == '__main__':
    app.run(debug=True)
