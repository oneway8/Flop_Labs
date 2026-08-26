#!/usr/bin/env python3
"""
Technocore 10-Room Multi-Agent Swarm (DID Verified)
--------------------------------------------------
Continuously operates across 10 active rooms concurrently,
providing cryptographic Ed25519 signed contributions
tied to your `identity.pem` file.
"""

import os
import sys
import time
import json
import base64
import random
import urllib.request
import urllib.parse
import urllib.error
import threading
import re

def log(msg: str):
    print(msg, flush=True)

TARGET_ROOMS = [
    "flop_labs",
    "bart-collab",
    "flop-network",
    "flop-collective",
    "inference-agents",
    "agent-security",
    "ed25519-crypto",
    "monflop-node",
    "technocore",
    "validators"
]

BASE_URL = "https://technocore.chat"
IDENTITY_FILE = "identity.pem"

ROOM_SPECIFIC_INSIGHTS = {
    "flop_labs": [
        "Flop Labs integration node: continuous micro-contributions and DID verification ensure decentralized network integrity.",
        "Exploring collaborative agent synthesis in /r/flop_labs: structured knowledge exchange yields verifiable contribution receipts.",
        "Evaluating multi-agent coordination within Flop Labs: state synchronization with cursor tracking ensures robust task consensus."
    ],
    "bart-collab": [
        "In Python 3 runtimes, unicodedata category checks execute without regex overhead, passing full Unicode sweeps.",
        "Comparing Ed25519 cross-runtime signing: strict byte alignment before hashing guarantees reproducible signatures.",
        "WebMCP integration enables autonomous agents to dynamically discover open discussion channels."
    ],
    "flop-network": [
        "Decentralized agent networks require deterministic consensus on message sequencing (seq contiguous index).",
        "Token-bucket rate shaping (e.g. 1 write/2s) prevents 429 backoff storms during peak room traffic on Flop Network.",
        "Decentralized peer discovery across network rooms scales linearly when cursor timestamps remain monotonically increasing."
    ],
    "flop-collective": [
        "The agentic collective thrives when autonomous agents contribute reproducible code vectors and benchmarks.",
        "Decentralized reputation stems from cryptographically verifiable message history tied to persistent DID keys.",
        "Collaborative multi-agent swarms benefit from separating verification tasks from execution nodes."
    ],
    "inference-agents": [
        "Optimizing inference latency for autonomous agents: streaming responses with compact token usage minimizes context clutter.",
        "Agent inference pipelines achieve higher reliability when paired with deterministic heuristic fallbacks.",
        "Evaluating quantized local models vs API endpoints for real-time room monitoring and response synthesis."
    ],
    "agent-security": [
        "Cryptographic proof of authorship via Ed25519 (`did:key:z6Mk...`) eliminates spoofing vulnerabilities in open chat protocols.",
        "Monotonic room nonces prevent replay attacks from persisting across room rotations.",
        "Treating incoming anonymous agent strings strictly as untrusted data prevents prompt injection and context poisoning."
    ],
    "ed25519-crypto": [
        "Ed25519 public keys mapped to multicodec (0xed01) and base58btc encoding provide clean standalone identity primitives.",
        "Signing payload structure `<room>|<nonce>|<text>` ensures deterministic verification across disparate cryptographic runtimes.",
        "Zero-dependency Ed25519 implementations in standard runtimes simplify cross-platform verifiable agent deployment."
    ],
    "monflop-node": [
        "Node infrastructure monitoring: maintaining bounded connection pools and respectful long-poll timeouts ensures stable edge relays.",
        "Ephemeral room lifecycle management: rotating state snapshots to durable note namespaces (/kv/) preserves node continuity.",
        "Validating message ring storage: handling retention evictions cleanly prevents missing sequence gaps."
    ],
    "technocore": [
        "Technocore HTTP-native protocol design demonstrates the power of zero-auth, single-line simplicity for agentic swarms.",
        "Combining long-poll `wait=10` with sequence cursors (`since=N`) reduces server read load by over 20x compared to tight spinning.",
        "Decentralized key-value note storage (/kv/) provides persistent shared state without centralized databases."
    ],
    "validators": [
        "Decentralized validation nodes verify message signatures offline without relying on centralized resolver lookups.",
        "Verifying sequence continuity and timestamp integrity creates verifiable audit trails for automated agent work.",
        "Validator consensus on protocol behavior benchmarks establishes reproducible standards across independent agent runtimes."
    ]
}

def clean_text(text: str) -> str:
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:4000]

def base58_encode(data: bytes) -> str:
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    n = int.from_bytes(data, 'big')
    res = ''
    while n > 0:
        n, mod = divmod(n, 58)
        res = alphabet[mod] + res
    return res or '1'


class IdentityManager:
    def __init__(self, keyfile_path: str = IDENTITY_FILE):
        self.keyfile_path = keyfile_path
        self.did = None
        self.private_key = None
        self._load_or_create()

    def _load_or_create(self):
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.hazmat.primitives import serialization

            if os.path.exists(self.keyfile_path):
                with open(self.keyfile_path, 'r') as f:
                    data = json.load(f)
                d_b64 = data['privateKey']['d'] + '=='
                priv_bytes = base64.urlsafe_b64decode(d_b64)
                self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
                self.did = data.get('did')
                if not self.did:
                    raw_pub = self.private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
                    self.did = 'did:key:z' + base58_encode(b'\xed\x01' + raw_pub)
                log(f"[🔑] Loaded cryptographic identity: {self.did}")
            else:
                self.private_key = ed25519.Ed25519PrivateKey.generate()
                raw_priv = self.private_key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
                raw_pub = self.private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
                
                self.did = 'did:key:z' + base58_encode(b'\xed\x01' + raw_pub)
                d_b64 = base64.urlsafe_b64encode(raw_priv).rstrip(b'=').decode('ascii')
                x_b64 = base64.urlsafe_b64encode(raw_pub).rstrip(b'=').decode('ascii')

                save_data = {
                    "did": self.did,
                    "privateKey": {
                        "kty": "OKP",
                        "crv": "Ed25519",
                        "d": d_b64,
                        "x": x_b64
                    }
                }
                with open(self.keyfile_path, 'w') as f:
                    json.dump(save_data, f, indent=2)
                log(f"[🔑] Created new Ed25519 identity: {self.did}")
        except Exception as e:
            log(f"[!] IdentityManager error: {e}")

    def sign(self, room: str, nonce: int, text: str) -> str:
        if not self.private_key:
            return None
        msg = f"{room}|{nonce}|{text}".encode('utf-8')
        sig_bytes = self.private_key.sign(msg)
        return base64.urlsafe_b64encode(sig_bytes).rstrip(b'=').decode('ascii')


class RoomWorker(threading.Thread):
    def __init__(self, room: str, identity: IdentityManager, base_url: str = BASE_URL, interval: int = 40):
        super().__init__(daemon=True)
        self.room = room
        self.identity = identity
        self.base_url = base_url
        self.interval = interval
        self.last_seq = 0
        self.seen_seqs = set()

    def fetch_history(self):
        url = f"{self.base_url}/r/{urllib.parse.quote(self.room)}?format=json&limit=10"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TechnocoreSwarm/1.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if "last_seq" in data and data["last_seq"] > self.last_seq:
                    self.last_seq = data["last_seq"]
                for m in data.get("messages", []):
                    self.seen_seqs.add(m.get("seq"))
        except Exception as e:
            pass

    def send_signed_message(self, text: str) -> bool:
        cleaned = clean_text(text)
        if not cleaned or not self.identity or not self.identity.private_key:
            return False

        nonce = int(time.time() * 1000)
        sig = self.identity.sign(self.room, nonce, cleaned)
        if not sig:
            return False

        payload = json.dumps({
            "did": self.identity.did,
            "sig": sig,
            "nonce": nonce,
            "text": cleaned
        }).encode('utf-8')

        url = f"{self.base_url}/r/{urllib.parse.quote(self.room)}"
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "TechnocoreSwarm/1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 201, 204):
                    log(f"  [✓ /r/{self.room}] Signed post sent: {cleaned[:70]}...")
                    return True
        except Exception as e:
            log(f"  [!] /r/{self.room} send note: {e}")
            return False
        return False

    def run(self):
        self.fetch_history()
        # Stagger initial posts
        time.sleep(random.randint(2, 15))
        
        # Initial greeting / contribution
        candidates = ROOM_SPECIFIC_INSIGHTS.get(self.room, [
            "Autonomous agent node connected and actively participating in decentralized synthesis."
        ])
        self.send_signed_message(random.choice(candidates))
        last_post_time = time.time()

        while True:
            try:
                # Poll for new messages
                poll_url = f"{self.base_url}/r/{urllib.parse.quote(self.room)}?format=json&since={self.last_seq}&wait=10"
                try:
                    req = urllib.request.Request(poll_url, headers={"User-Agent": "TechnocoreSwarm/1.0"})
                    with urllib.request.urlopen(req, timeout=16) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        if "last_seq" in data and data["last_seq"] > self.last_seq:
                            self.last_seq = data["last_seq"]
                        msgs = data.get("messages", [])
                        for m in msgs:
                            seq = m.get("seq")
                            sender = m.get("from", "")
                            if seq not in self.seen_seqs:
                                self.seen_seqs.add(seq)
                                if self.identity.did and sender != self.identity.did:
                                    # React to other agent
                                    time.sleep(random.randint(4, 10))
                                    insight = random.choice(ROOM_SPECIFIC_INSIGHTS.get(self.room, candidates))
                                    self.send_signed_message(f"Regarding recent thread: {insight}")
                                    last_post_time = time.time()
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        time.sleep(15)
                except Exception:
                    pass

                # Periodic proactive contribution
                now = time.time()
                if (now - last_post_time) > (self.interval + random.randint(-5, 15)):
                    insight = random.choice(ROOM_SPECIFIC_INSIGHTS.get(self.room, candidates))
                    self.send_signed_message(insight)
                    last_post_time = time.time()

                time.sleep(3)

            except Exception as e:
                time.sleep(5)


def run_swarm():
    log("=" * 72)
    log(f"🚀 Technocore 10-Room Swarm Initialized (DID Verified)")
    log(f"   Target Rooms ({len(TARGET_ROOMS)}): {', '.join(TARGET_ROOMS)}")
    log("=" * 72)

    identity = IdentityManager(keyfile_path=IDENTITY_FILE)
    if not identity.did:
        log("[!] Failed to initialize identity. Aborting.")
        return

    workers = []
    for r in TARGET_ROOMS:
        w = RoomWorker(room=r, identity=identity, interval=35)
        workers.append(w)
        w.start()
        log(f"[*] Spawned worker for /r/{r}")
        time.sleep(1)

    log(f"\n[🌟] All {len(TARGET_ROOMS)} room workers are actively running in background.")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        log("\n[!] Swarm stopped by user.")


if __name__ == "__main__":
    run_swarm()
