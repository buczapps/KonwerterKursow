from flask import Flask


application = Flask(__name__)


@application.route('/')
def hello_world():
    text = f'<h1>Konwerter kursów walut</h1>'
    return(text)


if __name__ == '__main__':
    application.run(debug=True)