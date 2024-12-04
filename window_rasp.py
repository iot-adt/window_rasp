from flask import Flask, request, jsonify
import RPi.GPIO as GPIO
import time
import threading
import requests

# Flask 앱 초기화
app = Flask(__name__)

# GPIO 핀 설정
TRIG = 23
ECHO = 24
SERVO_LEFT = 18
SERVO_RIGHT = 17

# GPIO 모드 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(SERVO_LEFT, GPIO.OUT)
GPIO.setup(SERVO_RIGHT, GPIO.OUT)

# 서보 모터 PWM 초기화
left_servo = GPIO.PWM(SERVO_LEFT, 50)  # 50Hz
right_servo = GPIO.PWM(SERVO_RIGHT, 50)  # 50Hz
left_servo.start(0)
right_servo.start(0)

# 알림을 보낼 서버 URL
ALERT_SERVER_URL = "http://10.147.20.102:5000/alert"  # 경고를 보낼 서버 URL

# 잠금 상태 변수
is_locked = False

# 초음파 거리 측정 함수
def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10us 펄스
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        start_time = time.time()
    while GPIO.input(ECHO) == 1:
        end_time = time.time()

    duration = end_time - start_time
    distance = (duration * 34300) / 2  # 단위: cm
    return distance

# 서보 모터 제어 함수
def control_servo(lock):
    if lock:
        left_servo.ChangeDutyCycle(2.5)  # 0도
        right_servo.ChangeDutyCycle(2.5)  # 0도
    else:
        left_servo.ChangeDutyCycle(7.5)  # 90도
        right_servo.ChangeDutyCycle(7.5)  # 90도
    time.sleep(0.5)
    left_servo.ChangeDutyCycle(0)
    right_servo.ChangeDutyCycle(0)

# 거리 감시 및 경고 전송 함수
def alert_distance():
    global is_locked
    while True:
        if is_locked:
            distance = get_distance()
            print(f"측정된 거리: {distance}cm")  # 디버깅용 출력
            if distance > 4:
                print(f"경고: 거리 초과 {distance}cm")
                try:
                    response = requests.post(ALERT_SERVER_URL, json={"distance": distance})
                    response.raise_for_status()  # HTTP 오류 처리
                    print(f"경고 신호 전송 완료: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"경고 신호 전송 실패: {e}")
        time.sleep(1)  # 1초 간격으로 거리 측정

# Flask 라우팅
@app.route('/lock', methods=['POST'])
def lock_window():
    global is_locked
    is_locked = True  # 잠금 상태 활성화
    control_servo(lock=True)
    return jsonify({"status": "locked"})

@app.route('/unlock', methods=['POST'])
def unlock_window():
    global is_locked
    is_locked = False  # 잠금 상태 비활성화
    control_servo(lock=False)
    return jsonify({"status": "unlocked"})

@app.route('/distance', methods=['GET'])
def get_distance_value():
    distance = get_distance()
    return jsonify({"distance": distance})

# Flask 앱 실행
if __name__ == '__main__':
    try:
        # 거리 감시 스레드 시작
        threading.Thread(target=alert_distance, daemon=True).start()
        app.run(host='0.0.0.0', port=5001)  # Flask 서버 실행
    except KeyboardInterrupt:
        pass
    finally:
        left_servo.stop()
        right_servo.stop()
        GPIO.cleanup()
