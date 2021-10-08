from flask import Flask
from flask_ldp import LDP, log_call

app = Flask(__name__)
ldp = LDP(app)


@app.route("/test")
def test():
    ldp.info('test', extra=dict(data=dict(some='data')))
    return "thanks"


@app.route("/")
@log_call
def root():
    return "thanks"

if __name__ == "__main__":
    app.debug = True
    app.run()
