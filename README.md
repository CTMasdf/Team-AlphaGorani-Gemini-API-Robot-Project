# 🤖 Team AlphaGorani - Gemini API Robot Project

음성 인식 기반으로 사용자의 명령을 이해하고, Gemini API를 활용해 자연스럽게 대화하며 로봇을 제어하는 **임베디드 AI 로봇 프로젝트**입니다.  
라즈베리파이4와 아두이노를 연동하여 음성(STT), 음성 출력(TTS), 자연어 처리(NLP), 로봇 제어 기능을 통합하였습니다.  

---

## 📌 프로젝트 개요
이번 임베디드 캡스톤디자인 과제는 인공지능, 마이크로프로세서, 회로 설계 등을 종합적으로 활용하여 **Gemini API 기반 AI 로봇**을 개발하는 것입니다.  
- 사용자는 마이크를 통해 음성으로 질문/명령을 입력합니다.  
- 라즈베리파이는 **STT**로 음성을 텍스트로 변환 후 **Gemini API**를 호출하여 응답을 생성합니다.  
- 응답은 **TTS**로 스피커를 통해 출력되며, 동시에 제어 명령어는 아두이노로 전달됩니다.  
- 아두이노는 명령어에 따라 **모터, LED, 도트매트릭스** 등을 제어합니다.  

---

## 📂 코드
- [🔗 Arduino Code (로봇 제어)](https://github.com/CTMasdf/Team-AlphaGorani-Gemini-API-Robot-Project/blob/main/Arduino_code_robot_control.ino)  
- [🔗 Raspberry Pi Code (STT, TTS, Gemini API, 시리얼 통신)](https://github.com/CTMasdf/Team-AlphaGorani-Gemini-API-Robot-Project/blob/main/voice.py)

---

## 🎥 시연 영상
[![프로젝트 시연 영상](https://img.youtube.com/vi/UFUamMonCCo/0.jpg)](https://youtu.be/UFUamMonCCo)

---

## 🛠️ 적용 기술
### 하드웨어
- Raspberry Pi 4 (라즈비안 OS)
- Arduino UNO
- DC 모터, 모터 드라이버
- 도트 매트릭스, LED
- USB 마이크, 스피커
- DC-DC 컨버터 (5V / 12V 전원 분배)

### 소프트웨어
- **Python** (라즈베리파이, Gemini API, STT/TTS, 시리얼 통신)
- **C++ / Arduino IDE** (아두이노 제어)
- **Gemini API** (자연어 처리 및 임베딩)
- **SpeechRecognition / pyttsx3** (STT & TTS)

---

## ⚙️ 시스템 동작
1. 사용자가 음성 입력 → 마이크 수집  
2. 라즈베리파이 → STT 처리 → Gemini API 호출  
3. Gemini 응답 → TTS 출력 + 문자열 명령어 아두이노 전송  
4. 아두이노 → 모터 / LED / 도트매트릭스 동작 수행  

---

## 📊 프로젝트 문서
- [📑 최종 보고서 (문서)](https://gamma.app/docs/-6w2qbxwzts394mj?follow_on_start=true&following_id=8ix1jva0prf9maq&mode=doc)

---

## 🚀 기대 효과 및 활용 방안
- 가정: AI 홈 비서, 노약자 보조 로봇  
- 교육: 학생들의 AI·임베디드 학습용 도구  
- 산업: 반복 작업 자동화, 위험 지역 원격 제어 로봇  
- 확장: 카메라·센서 추가 → 자율주행 및 객체 인식 가능  

---

## 👥 팀 소개
**Team AlphaGorani**  
- Embedded System 개발  
- AI 챗봇 & 음성 인터페이스 구현  
- 하드웨어 제작 및 통합  

---
