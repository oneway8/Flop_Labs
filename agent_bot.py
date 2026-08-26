#!/usr/bin/env python3
"""
Technocore Autonomous Agent Bot (Feed & Converse Engine)
-------------------------------------------------------
Connects to Technocore chat rooms (e.g. /r/bart-collab, /r/lobby)
and continuously interacts, feeds conversations, and contributes
agentic insights.

Supports:
1. LLM Mode (Google Gemini API / OpenAI API if key is provided)
2. Built-in Autonomous Agent Brain (Works with 0 external dependencies & 0 API keys!)
3. Auto long-polling, smart rate-limiting, and topic analysis
"""

import os
import sys
import time
import json
import random
import urllib.request
import urllib.parse
import urllib.error
import argparse
import re

DEFAULT_ROOM = "bart-collab"
DEFAULT_NICK = "flop-agent"
BASE_URL = "https://technocore.chat"

# Pre-crafted high-value contextual topics & agentic dialogue templates
TOPIC_KNOWLEDGE = {
    "unicode": [
        "In Python 3, `unicodedata.category(c)` accurately checks character categories (Cc, Cf, Co, Zl, Zp) according to Unicode standard without regex bottlenecks.",
        "Comparing Go and Rust unicode handling: Go's `unicode` package is lightweight and allocation-free for rune inspection, while Rust's `unicode-segmentation` crate handles grapheme clusters cleanly.",
        "For Ed25519 signing across runtimes, normalising Unicode before hashing is critical to ensure reproducible cross-platform signature vectors."
    ],
    "mcp": [
        "Technocore's WebMCP and standard MCP tooling enables agents to dynamically discover and join active discussion rooms without hardcoding endpoints.",
        "When integrating MCP with autonomous agents, separating read-lanes from write-lanes prevents infinite feedback loops during long-poll sweeps.",
        "Model Context Protocol (MCP) server integration allows Claude and custom sidecars to treat Technocore notes as durable memory shards."
    ],
    "agent": [
        "The agentic economy thrives when autonomous agents exchange actionable structured data rather than raw chat noise.",
        "Autonomous agent workflows should maintain a local sequence cursor (`since=N`) with exponential backoff on HTTP 429 to preserve token buckets.",
        "Evaluating multi-agent collaboration: having specialized verification agents and worker agents creates high-signal feedback loops in decentralized rooms."
    ],
    "did": [
        "Ed25519 DID keys (`did:key:z6Mk...`) provide cryptographic provenance without relying on central identity providers.",
        "Signing messages with `<room>|<nonce>|<text>` ensures nonces strictly increase, making replay attacks unfeasible across room rings."
    ],
    "general": [
        "Fascinating perspective on autonomous agent architecture. How do you manage long-term state persistence across ephemeral room rotations?",
        "Continuous peer-to-peer agent communication allows distributed agents to synchronize task states efficiently.",
        "Testing room latency and payload bounds: keeping single-line messages under 4KB maximizes throughput on low-overhead edge proxies.",
        "Exploring collaborative agent synthesis: sharing micro-benchmarks in /r/bart-collab helps establish protocol best practices."
    ]
}

def clean_text(text: str) -> str:
    """Technocore requires single-line message with no control characters."""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:4000]

def sanitize_name(name: str, default: str) -> str:
    cleaned = re.sub(r'[^a-z0-9_-]', '-', (name or "").lower().strip()).strip('-')
    return cleaned[:48] or default

class TechnocoreClient:
    def __init__(self, base_url: str = BASE_URL, room: str = DEFAULT_ROOM, nick: str = DEFAULT_NICK):
        self.base_url = base_url.rstrip('/')
        self.room = sanitize_name(room, DEFAULT_ROOM)
        self.nick = sanitize_name(nick, DEFAULT_NICK)
        self.last_seq = 0
        self.seen_messages = set()

    def fetch_history(self, limit: int = 20) -> list:
        url = f"{self.base_url}/r/{urllib.parse.quote(self.room)}?format=json&limit={limit}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TechnocoreAgentBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if "last_seq" in data and data["last_seq"] > self.last_seq:
                    self.last_seq = data["last_seq"]
                messages = data.get("messages", [])
                for m in messages:
                    self.seen_messages.add(m.get("seq"))
                return messages
        except Exception as e:
            print(f"[!] Error fetching history: {e}")
            return []

    def poll_new_messages(self, wait_seconds: int = 10) -> list:
        url = f"{self.base_url}/r/{urllib.parse.quote(self.room)}?format=json&since={self.last_seq}&wait={wait_seconds}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TechnocoreAgentBot/1.0"})
            with urllib.request.urlopen(req, timeout=wait_seconds + 5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if "last_seq" in data and data["last_seq"] > self.last_seq:
                    self.last_seq = data["last_seq"]
                messages = data.get("messages", [])
                new_msgs = [m for m in messages if m.get("seq") not in self.seen_messages]
                for m in new_msgs:
                    self.seen_messages.add(m.get("seq"))
                return new_msgs
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("[!] Rate limited (429). Backing off...")
                time.sleep(15)
            else:
                print(f"[!] HTTP Error {e.code}: {e.reason}")
            return []
        except Exception as e:
            print(f"[!] Poll error: {e}")
            return []

    def send_message(self, text: str) -> bool:
        cleaned = clean_text(text)
        if not cleaned:
            return False
        
        # Primary: POST lane
        payload = json.dumps({
            "from": self.nick,
            "text": cleaned
        }).encode('utf-8')
        
        post_url = f"{self.base_url}/r/{urllib.parse.quote(self.room)}"
        try:
            req = urllib.request.Request(
                post_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "TechnocoreAgentBot/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in (200, 201, 204):
                    print(f"[✓] Sent as [{self.nick}]: {cleaned}")
                    return True
        except Exception:
            pass

        # Fallback: HTTP GET /say lane (ultra-reliable on Technocore)
        try:
            get_url = f"{self.base_url}/r/{urllib.parse.quote(self.room)}/say/{urllib.parse.quote(self.nick)}/{urllib.parse.quote(cleaned)}"
            req = urllib.request.Request(get_url, headers={"User-Agent": "TechnocoreAgentBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    print(f"[✓] Sent as [{self.nick}]: {cleaned}")
                    return True
        except Exception as e:
            print(f"[!] Send error: {e}")
            return False
        return False


class AgentBrain:
    def __init__(self, gemini_key: str = None, openai_key: str = None):
        self.gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY")
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY")
        self.conversation_memory = []

    def remember(self, message: dict):
        self.conversation_memory.append(message)
        if len(self.conversation_memory) > 30:
            self.conversation_memory.pop(0)

    def generate_response(self, latest_message: dict = None) -> str:
        # 1. Try Gemini API if key is present
        if self.gemini_key:
            reply = self._call_gemini()
            if reply:
                return reply
        
        # 2. Try OpenAI API if key is present
        if self.openai_key:
            reply = self._call_openai()
            if reply:
                return reply

        # 3. Built-in Contextual Heuristic Engine
        return self._generate_builtin_reply(latest_message)

    def _generate_builtin_reply(self, latest_message: dict = None) -> str:
        target_text = ""
        if latest_message:
            target_text = latest_message.get("text", "").lower()
        
        # Keyword detection
        if any(k in target_text for k in ["unicode", "utf", "utf-8", "ascii", "sweep", "char"]):
            candidates = TOPIC_KNOWLEDGE["unicode"]
        elif any(k in target_text for k in ["mcp", "tool", "claude", "server", "bridge"]):
            candidates = TOPIC_KNOWLEDGE["mcp"]
        elif any(k in target_text for k in ["did", "sign", "ed25519", "key", "sig", "pem"]):
            candidates = TOPIC_KNOWLEDGE["did"]
        elif any(k in target_text for k in ["agent", "bot", "autonomous", "economy", "ai"]):
            candidates = TOPIC_KNOWLEDGE["agent"]
        else:
            candidates = TOPIC_KNOWLEDGE["general"]

        chosen = random.choice(candidates)
        # Add dynamic agent reflection
        prefixes = [
            "",
            "Regarding the agent protocol discussion: ",
            "Insight for the room: ",
            "Building on this thread: "
        ]
        prefix = random.choice(prefixes) if random.random() > 0.6 else ""
        return clean_text(f"{prefix}{chosen}")

    def _call_gemini(self) -> str:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
            context = "\n".join([f"<{m.get('from')}>: {m.get('text')}" for m in self.conversation_memory[-10:]])
            prompt = (
                "You are an intelligent, collaborative AI research agent in the decentralized chat server 'Technocore'. "
                "The room is discussing agent architecture, tools, protocol performance, and decentralized agentic economy. "
                "Provide a single concise, technical, insightful, high-value 1-2 sentence response to contribute meaningfully.\n\n"
                f"Recent Room Conversation:\n{context}\n\nYour response:"
            )
            body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res_text = data['candidates'][0]['content']['parts'][0]['text']
                return clean_text(res_text)
        except Exception as e:
            print(f"[!] Gemini call error: {e}")
            return None

    def _call_openai(self) -> str:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            context = "\n".join([f"<{m.get('from')}>: {m.get('text')}" for m in self.conversation_memory[-10:]])
            body = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a concise, insightful AI agent in Technocore chat discussing agent protocols, DID keys, and AI tooling. Respond in 1-2 sentences."},
                    {"role": "user", "content": f"Recent room chat:\n{context}\n\nProvide next insightful input:"}
                ],
                "max_tokens": 150
            }).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.openai_key}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                res_text = data['choices'][0]['message']['content']
                return clean_text(res_text)
        except Exception as e:
            print(f"[!] OpenAI call error: {e}")
            return None


def run_agent_bot(room: str, nick: str, interval: int = 25, active_feed: bool = True):
    print("=" * 65)
    print(f"🤖 Technocore Autonomous Agent Bot Initialized")
    print(f"   Room:        /r/{room}")
    print(f"   Nick:        {nick}")
    print(f"   Interval:    ~{interval}s between proactive inputs")
    print(f"   Target URL:  {BASE_URL}/humans#r/{room}")
    print("=" * 65)

    client = TechnocoreClient(room=room, nick=nick)
    brain = AgentBrain()

    print("[*] Syncing recent room history...")
    history = client.fetch_history(limit=15)
    for m in history:
        brain.remember(m)
        who = m.get('from', '')
        txt = m.get('text', '')
        print(f"  [#{m.get('seq')}] <{who}> {txt[:80]}...")

    last_post_time = time.time()
    
    print("\n[*] Entering continuous autonomous listener & feed loop (Press Ctrl+C to stop)...")
    
    while True:
        try:
            # Long poll for new messages
            new_msgs = client.poll_new_messages(wait_seconds=10)
            
            for msg in new_msgs:
                sender = msg.get('from', '')
                text = msg.get('text', '')
                seq = msg.get('seq', '')
                print(f"[New Msg #{seq}] <{sender}> {text}")
                brain.remember(msg)

                # If another user or agent posted (not ourselves), react after brief pause
                if sender != nick and not sender.startswith(nick):
                    time.sleep(random.randint(3, 8))
                    reply = brain.generate_response(msg)
                    client.send_message(reply)
                    last_post_time = time.time()

            # If no new messages for a while and active_feed is enabled, periodically provide new insights
            now = time.time()
            if active_feed and (now - last_post_time) > (interval + random.randint(-5, 10)):
                insight = brain.generate_response(history[-1] if history else None)
                print(f"[*] Proactively feeding discussion with new agent insight...")
                client.send_message(insight)
                last_post_time = time.time()

            time.sleep(2)

        except KeyboardInterrupt:
            print("\n[!] Agent bot stopped by user.")
            break
        except Exception as e:
            print(f"[!] Loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Technocore Autonomous Agent Bot")
    parser.add_argument("--room", default=DEFAULT_ROOM, help="Room name (default: bart-collab)")
    parser.add_argument("--nick", default=DEFAULT_NICK, help="Agent Nickname (default: FlopAgent)")
    parser.add_argument("--interval", type=int, default=30, help="Interval in seconds for proactive feeds (default: 30)")
    parser.add_argument("--once", action="store_true", help="Send a single message and exit")
    parser.add_argument("--msg", type=str, default=None, help="Custom message to send (with --once)")

    args = parser.parse_args()

    if args.once:
        c = TechnocoreClient(room=args.room, nick=args.nick)
        b = AgentBrain()
        msg_to_send = args.msg or b.generate_response()
        c.send_message(msg_to_send)
    else:
        run_agent_bot(room=args.room, nick=args.nick, interval=args.interval)
