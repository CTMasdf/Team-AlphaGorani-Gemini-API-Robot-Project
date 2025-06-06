# 필요한 라이브러리들을 불러옵니다
import serial  # 아두이노와 시리얼 통신을 위한 라이브러리
import time    # 시간 지연을 위한 라이브러리
import google.generativeai as genai  # Google Gemini API를 사용하기 위한 라이브러리
import speech_recognition as sr  # 음성 인식을 위한 라이브러리
from gtts import gTTS  # 텍스트를 음성으로 바꾸는 라이브러리 (Google Text-to-Speech)
import os  # 운영체제와 상호작용을 위한 라이브러리 (파일 경로, 환경 변수 등)
import json  # 대화 기록을 파일로 저장하고 불러오기 위한 라이브러리
from dotenv import load_dotenv  # .env 파일에서 환경 변수(API 키 등)를 불러오기 위한 라이브러리

# .env 파일에서 API 키를 불러옵니다
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # .env 파일에 저장된 Gemini API 키를 불러옵니다
genai.configure(api_key=GEMINI_API_KEY)  # Gemini API를 설정합니다

HISTORY_FILE = "conversation_history.json"  # 대화 기록을 저장할 파일 이름
COMMAND_KEYWORDS = ['forward', 'backward', 'turn_left', 'turn_right', 'stop']  # 아두이노 명령어 키워드

# 대화 기록 파일을 불러오는 함수
def load_conversation_history():
    if os.path.exists(HISTORY_FILE):  # 파일이 존재하면
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)  # JSON 형식으로 불러옴
    return []  # 파일이 없으면 빈 리스트 반환

# 대화 기록을 파일에 저장하는 함수
def save_conversation_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(conversation_history, f, ensure_ascii=False, indent=2)  # JSON 형식으로 저장

# 아두이노와 시리얼 통신 연결 시도
try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # 포트와 통신 속도 설정
    print("✅ 아두이노 연결 성공")
except Exception as e:
    print(f"❌ 아두이노 연결 실패: {e}")  # 연결 실패 시 에러 메시지 출력
    exit()  # 프로그램 종료

time.sleep(2)  # 아두이노 연결 후 잠시 대기
conversation_history = load_conversation_history()  # 대화 기록 불러오기

# Gemini에게 질문을 보내고 응답을 받아오는 함수
def generate_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # Gemini 모델 선택
        response = model.generate_content(prompt)  # 프롬프트를 보내고 응답 받기
        return response.text  # 텍스트만 추출하여 반환
    except Exception as e:
        return f"Gemini 오류: {e}"  # 에러 발생 시 에러 메시지 반환

# 대화 기록을 기반으로 프롬프트 문자열을 만드는 함수
def build_prompt():
    prompt = ""
    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "Chatbot"  # 역할 구분
        prompt += f"{role}: {msg['parts']}\n"  # 형식에 맞게 문자열 구성
    return prompt

# 텍스트를 음성으로 변환하고 재생하는 함수
def speak_text(text):
    tts = gTTS(text=text, lang='ko')  # 텍스트를 한국어 음성으로 변환
    tts.save("response.mp3")  # mp3 파일로 저장
    os.system("mpg321 response.mp3")  # 음성 파일 재생 (mpg321 플레이어 사용)

# 마이크로부터 음성을 받아 텍스트로 변환하는 함수
def recognize_speech(prompt=None):
    r = sr.Recognizer()  # 음성 인식기 생성
    with sr.Microphone() as source:  # 마이크로부터 입력 받기
        if prompt:
            print(prompt)  # 안내 문구 출력
        audio = r.listen(source)  # 음성 듣기
    try:
        text = r.recognize_google(audio, language="ko-KR")  # Google을 이용해 음성을 텍스트로 변환
        print("📝 인식된 텍스트:", text)
        return text
    except:
        print("⚠️ 음성 인식 실패")
        return ""

# 텍스트에서 명령어 키워드를 추출하는 함수
def extract_command(text):
    text_lower = text.lower()  # 소문자로 변환
    for keyword in COMMAND_KEYWORDS:
        if keyword in text_lower:
            return keyword  # 키워드가 있으면 반환
    return None  # 없으면 None 반환

# 추출된 명령어를 아두이노로 보내는 함수
def send_to_arduino(command):
    if command:
        try:
            arduino.write((command + '\n').encode('utf-8'))  # 명령어 전송
            print("📤 아두이노로 전송:", command)
        except Exception as e:
            print("⚠️ 아두이노 전송 오류:", e)

# 챗봇의 메인 루프 함수
def chat_bot():
    print("🎙️ 음성 기반 챗봇이 시작되었습니다. '알파'라고 말하면 질문을 받을게요.")
    while True:
        trigger = recognize_speech("📣 '알파'라고 말해주세요")  # 호출어 대기
        if "알파" in trigger:
            speak_text("질문하세요")  # 사용자에게 질문 유도
            question = recognize_speech("🎤 질문을 말해주세요")  # 질문 듣기
            if not question:
                continue  # 질문이 없으면 다시 반복

            conversation_history.append({"role": "user", "parts": question})  # 대화 기록 저장
            prompt = build_prompt()  # 프롬프트 만들기
            response_text = generate_response(prompt)  # Gemini 응답 받기
            print(f"🤖 챗봇: {response_text}")

            command = extract_command(response_text)  # 응답에서 명령어 추출
            send_to_arduino(command)  # 아두이노에 명령 전송
            speak_text(response_text)  # 응답 음성 출력

            conversation_history.append({"role": "model", "parts": response_text})  # 대화 기록 저장
            save_conversation_history()  # 기록 파일 저장

# 프로그램 실행 시작점
if __name__ == "__main__":
    chat_bot()  # 챗봇 실행
