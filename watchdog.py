#!/usr/bin/env python3
"""
Technocore Swarm Watchdog & Telegram Alert System
-------------------------------------------------
Monitors multi_agent_bot.py process status.
If the process ever stops, it automatically restarts it and sends an instant
alert to your Telegram bot (@technocoreA_bot).
"""

import os
import sys
import time
import subprocess
import json
import urllib.request
import urllib.parse

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(WORK_DIR, "multi_agent_bot.py")
LOG_PATH = os.path.join(WORK_DIR, "swarm.log")
WATCHDOG_LOG = os.path.join(WORK_DIR, "watchdog.log")
CONFIG_FILE = os.path.join(WORK_DIR, "telegram_config.json")

TELEGRAM_BOT_TOKEN = "8872033818:AAFIiXlNNh_OWVlyoWST9zDu8zmKqCmplxg"

def log(msg: str):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line, flush=True)
    try:
        with open(WATCHDOG_LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_saved_chat_id():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("chat_id")
        except Exception:
            pass
    return None

def save_chat_id(chat_id):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"chat_id": chat_id, "token": TELEGRAM_BOT_TOKEN}, f, indent=2)
    except Exception:
        pass

def fetch_chat_id_from_updates():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WatchdogTelegram/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get("result", [])
            if results:
                # Get latest message's chat_id
                last_msg = results[-1]
                chat = last_msg.get("message", {}).get("chat", {}) or last_msg.get("channel_post", {}).get("chat", {})
                chat_id = chat.get("id")
                if chat_id:
                    save_chat_id(chat_id)
                    log(f"[📱 Telegram] Discovered and saved chat_id: {chat_id}")
                    return chat_id
    except Exception as e:
        log(f"[!] Telegram getUpdates error: {e}")
    return None

def send_telegram_alert(message: str):
    chat_id = get_saved_chat_id()
    if not chat_id:
        chat_id = fetch_chat_id_from_updates()

    if not chat_id:
        log("[!] Telegram alert pending: Waiting for user to send /start to @technocoreA_bot.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "WatchdogTelegram/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                log(f"[📱 Telegram] Alert successfully sent to chat_id {chat_id}")
                return True
    except Exception as e:
        log(f"[!] Failed to send Telegram alert: {e}")
    return False

def is_bot_running() -> bool:
    try:
        output = subprocess.check_output(["ps", "aux"]).decode('utf-8')
        for line in output.splitlines():
            l_lower = line.lower()
            if "multi_agent_bot.py" in l_lower and "python" in l_lower and "grep" not in l_lower and "watchdog" not in l_lower:
                return True
        return False
    except Exception as e:
        log(f"[!] Process check error: {e}")
        return False

def restart_bot():
    log("[⚠️] multi_agent_bot is NOT running! Restarting now...")
    alert_msg = (
        "🚨 *[Technocore Alert]* 10개 에이전트 스웜 프로세스가 중단되어 자동 재시작을 진행합니다!\n\n"
        "• 대상: `multi_agent_bot.py` (10개 방 에이전트)\n"
        "• 상태: 🔄 자동 복구 중..."
    )
    send_telegram_alert(alert_msg)

    try:
        subprocess.Popen(
            f"nohup python3 -u {SCRIPT_PATH} > {LOG_PATH} 2>&1 &",
            shell=True,
            cwd=WORK_DIR,
            preexec_fn=os.setpgrp
        )
        time.sleep(3)
        if is_bot_running():
            log("[✓] Successfully restarted multi_agent_bot!")
            send_telegram_alert("✅ *[Technocore Recovery]* 10개 에이전트 스웜이 성공적으로 자동 재시작되어 정상 가동 중입니다.")
        else:
            log("[!] Failed to restart multi_agent_bot.")
            send_telegram_alert("❌ *[Technocore Error]* 에이전트 재시작에 실패했습니다. 확인이 필요합니다.")
    except Exception as e:
        log(f"[!] Restart error: {e}")

def check_once():
    # Sync telegram chat_id if not known yet
    if not get_saved_chat_id():
        fetch_chat_id_from_updates()

    if is_bot_running():
        log("[🟢] Health Check Passed: 10-Agent Swarm is running normally.")
    else:
        restart_bot()

def run_loop():
    log("🛡️ Technocore Swarm Watchdog with Telegram Alert Started.")
    fetch_chat_id_from_updates()
    
    while True:
        try:
            check_once()
            time.sleep(60) # Check every 60 seconds
        except KeyboardInterrupt:
            log("Watchdog stopped.")
            break
        except Exception as e:
            log(f"Watchdog loop error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    if "--once" in sys.argv:
        check_once()
    elif "--test-tg" in sys.argv:
        send_telegram_alert("🔔 *[Technocore Test]* 텔레그램 알림 시스템이 정상 연동되었습니다!")
    else:
        run_loop()
