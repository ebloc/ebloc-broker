from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    # sinfo %A | grep -o 'idle' | wc -l
    # sinfo %A | grep -o 'allocated' | wc -l
    return "Hello, World!"
