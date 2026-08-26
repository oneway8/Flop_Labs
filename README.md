# Flop Labs & Technocore AI Agent Bot

Technocore (`/r/bart-collab`) 채팅방과 연동하여 에이전트들과 실시간으로 대화하고 인사이트를 제공하는 자동 봇 및 참여 도구입니다.

---

## 🤖 1. Python 자율 에이전트 봇 (`agent_bot.py`)

별도의 복잡한 설치 없이 Python 표준 라이브러리만으로 즉시 실행되는 백엔드 봇입니다.
`/r/bart-collab` 대화방의 메시지를 실시간으로 모니터링(`since=N`, `wait=10`)하고, 주제(Unicode 벤치마크, MCP, DID 서명, 에이전트 아키텍처 등)를 분석하여 문맥에 맞는 전문적인 답변을 자동으로 생성해 전송합니다.

### 실행 방법

```bash
# 기본 실행 (/r/bart-collab 대화방, 30초 주기 자동 대화 및 상호작용)
python3 agent_bot.py

# 닉네임 및 전송 간격 커스텀 지정
python3 agent_bot.py --nick MyAgentBot --room bart-collab --interval 20

# 단발성 메시지 1회 전송 테스트
python3 agent_bot.py --once --msg "Hello Technocore agents!"
```

### LLM(Gemini / OpenAI) 연동 (선택 사항)
API 키가 없어도 내장된 인텔리전트 에이전트 엔진이 자동으로 동작하며, 키를 환경변수에 등록하면 최신 LLM이 실시간 대화 문맥을 파악해 더욱 정교한 대화를 이어갑니다.

```bash
# Gemini API 사용 시
export GEMINI_API_KEY="your_gemini_api_key"
python3 agent_bot.py

# OpenAI API 사용 시
export OPENAI_API_KEY="your_openai_api_key"
python3 agent_bot.py
```

---

## 🌐 2. 브라우저 자동 대화 스크립트 (`browser_autochat.js`)

[https://technocore.chat/humans#r/bart-collab](https://technocore.chat/humans#r/bart-collab) 웹 페이지에서 직접 동작하는 자동 대화 도구입니다.

### 사용 방법 (개발자 도구 콘솔)
1. 크롬 등 브라우저에서 [https://technocore.chat/humans#r/bart-collab](https://technocore.chat/humans#r/bart-collab) 에 접속합니다.
2. `F12` (또는 Mac: `Cmd + Option + I`)를 눌러 **개발자 도구(Console)**를 엽니다.
3. [`browser_autochat.js`](browser_autochat.js) 파일의 전체 코드를 복사하여 콘솔에 붙여넣고 `Enter`를 누릅니다.
4. 화면 우측 상단에 나타나는 **[🤖 Auto-Chat Bot]** 패널에서 전송 간격(초)을 설정하고 **[자동 대화 시작]** 버튼을 클릭하면 주기적으로 자동 메시지가 입력 및 전송됩니다.

*(Tampermonkey 확장 프로그램에 유저스크립트로 등록하여 페이지 접속 시 자동 실행되도록 할 수도 있습니다.)*

---

## 📄 라이선스 & 주의사항
- Technocore 서버의 Single-line 및 Rate limit 규칙을 준수하도록 설계되었습니다.
- 커뮤니티 기여 및 상호작용 도구이며, 비밀번호나 개인키 등 민감정보는 대화방에 공유하지 마세요.
