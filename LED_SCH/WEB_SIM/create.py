import os
import json

os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

with open("static/style.css", "w") as f:
    f.write(
        """body { font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }"""
    )

with open("templates/index.html", "w") as f:
    f.write(
        """<!DOCTYPE html>
<html>
<head>
    <title>Index Page</title>
    <link rel="stylesheet" type="text/css" href="/static/style.css">
</head>
<body>
    <h1>Welcome to the Index Page</h1>
</body>
</html>"""
    )

with open("data.json", "w") as f:
    json.dump({"message": "This is sample data."}, f, indent=4)

with open("bin_queue.json", "w") as f:
    json.dump({"queue": []}, f, indent=4)

with open("app.py", "w") as f:
    f.write(
        """from flask import Flask, render_template, send_from_directory, jsonify
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    with open('data.json') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/bin_queue')
def get_bin_queue():
    with open('bin_queue.json') as f:
        queue = json.load(f)
    return jsonify(queue)

if __name__ == '__main__':
    app.run(debug=True)
"""
    )
