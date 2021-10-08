from flask import Flask
from flask_ldp import LDP

app = Flask(__name__)
ldp = LDP(app)


@app.route("/test")
def test():
    ldp.info('test', extra=dict(data=dict(some='data')))
    return "thanks"

@app.route('/details')
def details():
    ldp.info('details', add_flask=True, add_request=True)
    return 'details'


if __name__ == "__main__":
    app.debug = True
    app.run()
