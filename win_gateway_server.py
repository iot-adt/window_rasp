from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__, template_folder='templates')

# 센서 라즈베리파이의 IP와 포트
SENSOR_SERVER_IP = "10.147.20.102"  # 센서 라즈베리파이 IP
SENSOR_SERVER_PORT = 5001

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lock', methods=['POST'])
def lock_window():
    try:
        response = requests.post(f"http://{SENSOR_SERVER_IP}:{SENSOR_SERVER_PORT}/lock")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/unlock', methods=['POST'])
def unlock_window():
    try:
        response = requests.post(f"http://{SENSOR_SERVER_IP}:{SENSOR_SERVER_PORT}/unlock")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route('/alert' , methods=['POST'])
def alert_handler():
    data = request.get_json()
    distance = data.get('distance' , None)
    print("request sucess") # 초음파 경고 신호 받음 부저 센서로 변환 
    return jsonify({"status":"received","distance":distance})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # 웹사이트 서버는 5000 포트에서 실행
