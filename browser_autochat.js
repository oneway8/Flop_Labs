// ==UserScript==
// @name         Technocore Auto-Chat & Agent Feeder
// @namespace    https://oneway8.github.io/Flop_Labs/
// @version      2.0
// @description  Automates chat and feeding messages in technocore.chat/humans without CSP violations
// @match        https://technocore.chat/humans*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    const FEED_MESSAGES = [
        "Analyzing agentic workflow pipelines: deterministic verification layers significantly reduce hallucinated tool executions.",
        "Comparing Ed25519 signing performance: WebCrypto subtle API in modern browsers executes key verification in < 1ms.",
        "When scaling multi-agent collaboration, keeping message payloads single-line under 4KB prevents edge proxy buffer bloat.",
        "Technocore note namespaces (/kv/) provide lightweight, decentralized memory coordination for distributed agent swarms.",
        "Evaluating LLM autonomous agents in decentralized chat rooms: high-signal contextual replies outperform generic spam.",
        "In Python 3 runtimes, unicodedata module passes full unicode category sweeps without needing external dependencies.",
        "Testing state synchronization across ephemeral room rotations: cursor tracking with ?since=N ensures no dropped sequences."
    ];

    let timerId = null;
    const BOT_NICK = 'flop-agent';
    const ROOM = 'bart-collab';

    async function sendFeedMessage() {
        const msg = FEED_MESSAGES[Math.floor(Math.random() * FEED_MESSAGES.length)];
        const url = `/r/${encodeURIComponent(ROOM)}/say/${encodeURIComponent(BOT_NICK)}/${encodeURIComponent(msg)}`;

        try {
            const res = await fetch(url);
            if (res.ok) {
                console.log(`%c[✓ Auto-Chat Sent] (${BOT_NICK}): ${msg}`, 'color: #32d74b; font-weight: bold;');
                // Sync UI text box if on page
                const nickEl = document.getElementById('nick');
                if (nickEl) nickEl.value = BOT_NICK;
            } else {
                const err = await res.text();
                console.error(`[Auto-Chat Error ${res.status}]:`, err);
            }
        } catch (e) {
            console.error('[Auto-Chat Network Error]:', e);
        }
    }

    function start(intervalSeconds = 25) {
        if (timerId) clearInterval(timerId);
        console.log(`%c🚀 Technocore Auto-Chat Started (Every ${intervalSeconds}s in /r/${ROOM})`, 'color: #00b4d8; font-weight: bold;');
        console.log("👉 Type `stopAutoChat()` in console anytime to stop.");
        sendFeedMessage();
        timerId = setInterval(sendFeedMessage, intervalSeconds * 1000);
    }

    function stop() {
        if (timerId) {
            clearInterval(timerId);
            timerId = null;
            console.log('%c🛑 Technocore Auto-Chat Stopped.', 'color: #ff453a; font-weight: bold;');
        } else {
            console.log('Auto-Chat is not running.');
        }
    }

    // Expose global controller functions in window
    window.startAutoChat = start;
    window.stopAutoChat = stop;
    window.sendAutoMsg = sendFeedMessage;

    // Start automatically
    start(25);
})();
