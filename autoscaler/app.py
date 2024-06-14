from flask import Flask, jsonify
import autoscaler

app = Flask(__name__)

@app.route('/scale', methods=['POST'])
def scale():
    autoscaler.scale_from_cpu_util()
    return

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
