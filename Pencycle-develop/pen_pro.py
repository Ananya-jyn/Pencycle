from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Waste Pen Project Running!"

app.run(debug=True)