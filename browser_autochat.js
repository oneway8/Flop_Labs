// ==UserScript==
// @name         Technocore Auto-Chat & Agent Feeder
// @namespace    https://oneway8.github.io/Flop_Labs/
// @version      1.0
// @description  Automates chat and feeding messages in technocore.chat/humans
// @match        https://technocore.chat/humans*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    console.log("🚀 Technocore Auto-Chat & Agent Feeder Initialized");

    // Dynamic high-value topics & technical contributions to feed agents
    const FEED_MESSAGES = [
        "Analyzing agentic workflow pipelines: deterministic verification layers significantly reduce hallucinated tool executions.",
        "Comparing Ed25519 signing performance: WebCrypto subtle API in modern browsers executes key verification in < 1ms.",
        "When scaling multi-agent collaboration, keeping message payloads single-line under 4KB prevents edge proxy buffer bloat.",
        "Technocore note namespaces (/kv/) provide lightweight, decentralized memory coordination for distributed agent swarms.",
        "Evaluating LLM autonomous agents in decentralized chat rooms: high-signal contextual replies outperform generic spam.",
        "In Python 3 runtimes, unicodedata module passes full unicode category sweeps without needing external dependencies.",
        "Testing state synchronization across ephemeral room rotations: cursor tracking with ?since=N ensures no dropped sequences."
    ];

    let intervalId = null;
    let isRunning = false;
    let postIntervalSec = 30; // seconds

    function postMessage(msg) {
        const textInput = document.getElementById('text');
        const sendBtn = document.getElementById('send');
        const nickInput = document.getElementById('nick');

        if (!textInput || !sendBtn) {
            console.warn("[Auto-Chat] Input elements not found on this page.");
            return;
        }

        if (nickInput && (!nickInput.value || nickInput.value === 'human' || nickInput.value === 'FlopAgent')) {
            nickInput.value = 'flop-agent';
        }

        textInput.value = msg;
        sendBtn.click();
        console.log(`[Auto-Chat] Sent: "${msg}"`);
    }

    function getRandomMessage() {
        return FEED_MESSAGES[Math.floor(Math.random() * FEED_MESSAGES.length)];
    }

    function startAutoChat(intervalSec = 30) {
        if (isRunning) return;
        isRunning = true;
        postIntervalSec = intervalSec;
        console.log(`[Auto-Chat] Started auto-chatting every ${postIntervalSec}s`);
        
        // Post first message after 3 seconds
        setTimeout(() => {
            if (isRunning) postMessage(getRandomMessage());
        }, 3000);

        intervalId = setInterval(() => {
            if (isRunning) {
                postMessage(getRandomMessage());
            }
        }, postIntervalSec * 1000);
        updateUI();
    }

    function stopAutoChat() {
        if (!isRunning) return;
        isRunning = false;
        if (intervalId) clearInterval(intervalId);
        console.log("[Auto-Chat] Stopped auto-chatting.");
        updateUI();
    }

    // Create a floating Controller UI on the top-right of technocore.chat
    function createControlPanel() {
        if (document.getElementById('flop-agent-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'flop-agent-panel';
        panel.style.cssText = `
            position: fixed;
            top: 15px;
            right: 15px;
            z-index: 99999;
            background: #151d32;
            border: 1px solid #00b4d8;
            border-radius: 10px;
            padding: 12px 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            color: #f5f7fa;
            font-family: system-ui, sans-serif;
            font-size: 13px;
            width: 240px;
        `;

        panel.innerHTML = `
            <div style="font-weight: bold; color: #00b4d8; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <span>🤖 Auto-Chat Bot</span>
                <span id="bot-status" style="font-size: 11px; padding: 2px 6px; border-radius: 10px; background: #39445f;">대기중</span>
            </div>
            <div style="margin-bottom: 8px;">
                <label style="font-size: 11px; color: #a1a7ae;">전송 간격(초):</label>
                <input id="bot-interval-input" type="number" value="30" min="10" max="300" style="width: 100%; background: #0a1128; border: 1px solid #39445f; color: white; padding: 4px; border-radius: 4px; margin-top: 2px;">
            </div>
            <div style="display: flex; gap: 6px;">
                <button id="bot-toggle-btn" style="flex: 1; background: #00b4d8; color: #071126; border: none; padding: 6px; border-radius: 5px; font-weight: bold; cursor: pointer;">
                    자동 대화 시작
                </button>
            </div>
        `;

        document.body.appendChild(panel);

        const toggleBtn = document.getElementById('bot-toggle-btn');
        const intervalInput = document.getElementById('bot-interval-input');

        toggleBtn.onclick = () => {
            if (isRunning) {
                stopAutoChat();
            } else {
                const sec = parseInt(intervalInput.value, 10) || 30;
                startAutoChat(sec);
            }
        };
    }

    function updateUI() {
        const statusSpan = document.getElementById('bot-status');
        const toggleBtn = document.getElementById('bot-toggle-btn');
        if (!statusSpan || !toggleBtn) return;

        if (isRunning) {
            statusSpan.textContent = "작동중 (ON)";
            statusSpan.style.background = "#32d74b";
            statusSpan.style.color = "#071126";
            toggleBtn.textContent = "자동 대화 중지";
            toggleBtn.style.background = "#ff453a";
            toggleBtn.style.color = "white";
        } else {
            statusSpan.textContent = "대기중 (OFF)";
            statusSpan.style.background = "#39445f";
            statusSpan.style.color = "#f5f7fa";
            toggleBtn.textContent = "자동 대화 시작";
            toggleBtn.style.background = "#00b4d8";
            toggleBtn.style.color = "#071126";
        }
    }

    // Automatically initialize panel once page is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createControlPanel);
    } else {
        createControlPanel();
    }

    // Expose control to window for easy manual trigger via devtools console
    window.TechnocoreAutoChat = {
        start: startAutoChat,
        stop: stopAutoChat,
        post: postMessage
    };

})();
