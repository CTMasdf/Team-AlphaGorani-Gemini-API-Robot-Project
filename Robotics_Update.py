# 카메라를 활용해 사진을 찍고 사물을 인식하는 기능과 
# 예)"앞으로 5초 갔다가 멈춰", "오른쪽으로 2초 돌아" 등의 명령들을 수행하는 기능을 추가하였습니다.


import serial
import time
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import os
import json
import subprocess 
import re # 정규표현식 모듈 추가
from dotenv import load_dotenv

# .env 파일에서 API 키 불러오기
load_dotenv()
# IMPORTANT: API Key is loaded from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    exit()

genai.configure(api_key=GEMINI_API_KEY)
# 기본 모델 사용
model = genai.GenerativeModel("gemini-2.5-flash")

# ------------------- 경로 및 상수 설정 -------------------
IMAGE_PATH = "capture.jpg" # 현재 디렉토리에 사진 저장
HISTORY_FILE = "conversation_history.json"
WAKE_WORD = "알파"  
CAMERA_TRIGGER_KEYWORDS = ['사진', '카메라', '찍어', '촬영']

# 아두이노 명령 키워드 (단순 키워드)
ARDUINO_COMMAND_KEYWORDS = [
    'M_Sunny', 'M_partly_cloudy', 'M_cloudy', 'M_rainy', 'M_sleet', 'M_snowy',
    'forward', 'backward', 'turn_left', 'turn_right', 'stop'
     # 움직임 키워드는 이제 TIMED_COMMANDS에서 처리
]

# 아두이노 명령 키워드 (시간 기반 움직임 키워드)
TIMED_COMMANDS = ['forward', 'backward', 'turn_left', 'turn_right', 'stop'] 

# ------------------- 초기화 및 연결 -------------------
def load_conversation_history():
    """대화 기록 로드."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("대화 기록 파일이 손상되었습니다. 새 기록으로 시작합니다.")
            return []
    return []

def save_conversation_history(history):
    """대화 기록 저장."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# 아두이노 연결
try:
    # 포트 설정을 사용자 환경에 맞게 확인하세요.
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1) 
    print("아두이노 연결 성공")
except Exception as e:
    print(f"아두이노 연결 실패: {e}. 아두이노 기능이 비활성화됩니다.")
    arduino = None

time.sleep(2)
conversation_history = load_conversation_history()

# ------------------- STT/TTS (기존과 동일) -------------------

def recognize_speech(prompt=None):
    """마이크를 통해 음성을 인식합니다."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        if prompt:
            print(prompt)
        try:
            # 음성 인식 대기
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return ""

    try:
        text = r.recognize_google(audio, language="ko-KR")
        print("인식된 텍스트:", text)
        return text
    except sr.UnknownValueError:
        # 음성 인식 실패 시 오류 메시지 출력 대신 빈 문자열 반환
        return ""
    except sr.RequestError as e:
        print(f"음성 인식 실패 (Google API 오류): {e}")
        return ""

def speak_text(text):
    """텍스트를 음성으로 변환하고 재생합니다."""
    print("챗봇:", text)
    try:
        tts = gTTS(text=text, lang='ko')
        tts.save("response.mp3")
        # mpg321을 사용하여 재생 (에러 메시지 숨김) 및 파일 삭제
        os.system("mpg321 -q response.mp3 > /dev/null 2>&1")
        os.remove("response.mp3")
    except Exception as e:
        print(f"⚠️ 음성 출력 오류 (gTTS 또는 mpg321): {e}")

# ------------------- 아두이노 -------------------

def extract_command(text):
    """텍스트에서 단순 아두이노 명령을 추출합니다."""
    text_lower = text.lower()
    for keyword in ARDUINO_COMMAND_KEYWORDS:
        if keyword.lower() in text_lower: # 대소문자 구분 없이 찾기
            return keyword
    return None

def extract_timed_command(text):
    """
    텍스트에서 'forward 5', 'backward 10'과 같은 시간 기반 명령을 추출합니다.
    (command, duration) 튜플을 반환합니다.
    """
    text_lower = text.lower()
    for cmd in TIMED_COMMANDS:
        # 정규표현식: 'forward' 또는 'backward' 뒤에 공백이 있고, 그 뒤에 숫자가 오는 패턴을 찾습니다.
        # 예: "forward 5" -> ('forward', '5')
        match = re.search(rf'\b({cmd})\s+(\d+)\b', text_lower)
        if match:
            command = match.group(1)
            duration = int(match.group(2))
            return command, duration
    return None, None

def send_to_arduino(command):
    """아두이노로 명령을 전송합니다."""
    if arduino and command:
        try:
            arduino.write((command + '\n').encode('utf-8'))
            print("아두이노로 전송:", command)
        except Exception as e:
            print("아두이노 전송 오류:", e)
    elif command:
        print(f"ℹ️ 아두이노가 연결되지 않아 명령 '{command}'를 전송할 수 없습니다.")


# ------------------- Gemini API & History (시스템 프롬프트 수정) -------------------

def build_prompt(history):
    """대화 기록을 기반으로 텍스트 프롬프트를 구성합니다."""
    prompt = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Chatbot"
        text_content = msg.get('parts', [''])[0] if isinstance(msg.get('parts'), list) else msg.get('parts', '')
        
        if role == "User":
             prompt += f"User: {text_content}\n"
        else:
             prompt += f"Model: {text_content}\n"
    
    # 모델의 역할 정의 (Gemini 챗봇한테 시간 명령을 출력하도록 명시) 
    system_instruction = (
        "당신은 라즈베리 파이 기반의 로봇 제어 챗봇입니다. "
        "모든 응답은 한국어로 친절하게 작성합니다. "
        "로봇의 움직임에 대한 요청(예: '앞으로 가', '뒤로 3초간 가')을 받으면, "
        "답변의 **가장 마지막 줄에** 파이썬 스크립트가 파싱할 수 있도록 정확한 명령어를 다음 형식으로 출력합니다. "
        
        "**[중요 규칙]**: "
        "1. **시간 기반 움직임 요청**: 사용자가 '5초 앞으로'처럼 시간과 움직임을 요청하면, 명령어와 시간을 띄어쓰기로 구분하여 마지막 줄에 출력하세요. (예: 'forward 5' 또는 'backward 3'). "
        "2. **단순 이동 요청**: '앞으로 가'와 같이 시간 없이 단순 이동만 요청하면, 'forward 1'처럼 기본 시간(1초)을 적용하여 출력하세요. "
        "3. **날씨 명령 요청**: 날씨 관련 요청을 받으면 답변의 맨 마지막 줄에 날씨 명령어만 출력하세요. (예: M_Sunny). "
        "4. **다른 모든 명령**: 다른 모든 단순 명령(예: turn_left)은 응답의 맨 마지막 줄에 해당 명령어를 출력하세요. "
        "5. **출력 예시**: "
        "   - '네, 5초 동안 앞으로 움직일게요.' \n   **forward 5**"
    )
    
    return system_instruction + "\n" + prompt


def generate_text_response(prompt_text):
    """텍스트 기반 응답을 생성합니다."""
    try:
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        # 오류 발생 시 디버깅을 위해 콘솔에 출력
        print(f"⚠️ Gemini API 호출 오류: {e}")
        return f"Gemini API 호출 중 오류가 발생했습니다: {e}"

# ------------------- 사진 촬영 및 분석 (기존과 동일) -------------------

def take_picture():
    """rpicam-still을 사용하여 사진을 촬영하고 저장합니다."""
    try:
        print("📷 사진 촬영 중...")
        # -t 500ms 미리보기
        subprocess.run(["rpicam-still", "-t", "500", "-o", IMAGE_PATH], check=True)
        print("✅ 사진 촬영 완료:", IMAGE_PATH)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ rpicam-still 실행 오류: 카메라 모듈이 활성화되어 있는지 확인하세요. {e}")
        return False
    except FileNotFoundError:
        print("❌ 'rpicam-still' 명령을 찾을 수 없습니다. libcamera 패키지가 설치되었는지 확인하세요.")
        return False

def ask_gemini_about_image(user_text):
    """저장된 이미지를 읽어 질문과 함께 Gemini에 전송합니다."""
    if not os.path.exists(IMAGE_PATH):
        return "죄송해요. 사진을 찍는 데 실패했거나 파일이 존재하지 않습니다."
    
    try:
        with open(IMAGE_PATH, "rb") as f:
            image_data = f.read()

        # 이미지 데이터와 사용자 텍스트를 함께 전송
        contents = [
            user_text,
            {"mime_type": "image/jpeg", "data": image_data}
        ]
        
        # 이미지 전송 시에는 대화 기록을 사용하지 않고 현재 요청만 보냅니다.
        response = model.generate_content(contents)
        return response.text
        
    except Exception as e:
        print(f"⚠️ 이미지 분석 오류: {e}")
        return f"이미지 분석 중 오류가 발생했습니다: {e}"

# ------------------- 명령어 처리 메인 함수 (주요 수정) -------------------

def handle_command(user_text):
    """사용자 텍스트를 처리하고, 카메라 사용 여부를 결정합니다."""
    global conversation_history
    answer = ""

    # 카메라 트리거 확인
    is_camera_req = any(keyword in user_text for keyword in CAMERA_TRIGGER_KEYWORDS)

    if is_camera_req:
        # 카메라 처리 로직 (이 부분은 시간 명령과 무관하게 기존 로직 유지)
        print("--- 카메라 명령이 감지되었습니다. ---")
        speak_text("사진을 찍고 분석할게요.")
        
        # ... (카메라 및 이미지 분석 로직)
        if take_picture():
            cleaned_question = user_text
            for keyword in CAMERA_TRIGGER_KEYWORDS:
                cleaned_question = cleaned_question.replace(keyword, '').strip() 
            
            # 찍은 사진에 대해 원하는 답변을 받기 위한 명령
            if not cleaned_question:
                cleaned_question = "방금 찍은 사진에 대해 한국어로 간단하게 2줄 이내로 설명해주세요."

            answer = ask_gemini_about_image(cleaned_question)
            conversation_history.append({"role": "user", "parts": [cleaned_question]})
            conversation_history.append({"role": "model", "parts": [answer]})
        else:
            answer = "카메라를 실행하는 데 문제가 발생했어요. 연결 상태를 확인해 주세요."
    
    else:
        # 일반 텍스트 대화
        conversation_history.append({"role": "user", "parts": [user_text]})
        prompt = build_prompt(conversation_history)
        answer = generate_text_response(prompt) 
        conversation_history.append({"role": "model", "parts": [answer]})
    
    save_conversation_history(conversation_history)

    # 1. 시간 기반 명령어 추출 및 처리 (가장 높은 우선순위)
    command, duration = extract_timed_command(answer)
    
    if command and duration is not None:
        # Gemini 응답 텍스트에서 명령어와 시간을 찾은 경우
        speak_text(answer) # 챗봇 응답 먼저 출력
        
        print(f"--- 시간 기반 이동 명령 감지: {command}, {duration}초 ---")
        
        # 1. 이동 명령 전송
        send_to_arduino(command)
        
        # 2. 지정된 시간만큼 대기
        print(f"ℹ️ {duration}초 동안 대기 중...")
        time.sleep(duration)
        
        # 3. 정지 명령 전송
        send_to_arduino('stop')
        print("정지 명령 전송 완료.")
        # 정지 메시지는 음성 출력하지 않음
        
    else:
        # 2. 단순 명령어 또는 날씨 명령어 추출 및 처리
        command = extract_command(answer)
        
        # 아두이노 명령은 응답 후 한 번만 전송
        send_to_arduino(command)
        
        # 챗봇 응답 출력
        speak_text(answer)

# ------------------- 챗봇 메인 루프 (기존과 동일) -------------------

def chat_bot():
    """메인 챗봇 루프."""
    print(f"음성 기반 챗봇이 시작되었습니다. '{WAKE_WORD}'라고 말하면 질문을 받을게요.")
    global conversation_history

    while True:
        # 호출어 인식
        trigger = recognize_speech(f"'{WAKE_WORD}'라고 말해주세요")
        if WAKE_WORD in trigger:
            speak_text("질문하세요")
            question = recognize_speech("질문을 말해주세요")
            
            if not question:
                continue

            if "종료" in question or "그만" in question:
                speak_text("대화를 종료합니다. 안녕히 계세요!")
                break
            
            # 명령어 처리 (일반 대화 또는 카메라)
            handle_command(question)


if __name__ == "__main__":
    try:
        chat_bot()
    finally:
        print("챗봇 프로그램을 종료합니다.")
