import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    print("INFO: Minimal app - Hello route was called")
    app.logger.info("INFO: Minimal app - Logger - Hello route was called")
    return "Hello from Minimal Railway App!"

@app.route('/ping')
def ping():
    print("INFO: Minimal app - Ping route was called")
    app.logger.info("INFO: Minimal app - Logger - Ping route was called")
    return "pong"

if __name__ == '__main__':
    local_port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=local_port)