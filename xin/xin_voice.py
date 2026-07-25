#!/usr/bin/env python3
"""
道归 · 语音输入桥接器 (Firefox 适配版)
支持: Firefox / Chrome / Edge / Safari
纯本地，浏览器语音识别 + 手动输入双模式
"""

import http.server
import json
import os
import sys
import webbrowser
import urllib.parse
from pathlib import Path

PORT = 18777
HTML_PATH = Path.home() / ".xin_voice_input.html"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>道归 · 语音输入</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0e0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
  }
  .container { max-width: 600px; width: 100%; text-align: center; }
  h1 { font-size: 1.8em; margin-bottom: 4px; color: #fff; letter-spacing: 2px; }
  .subtitle { color: #888; font-size: 0.9em; margin-bottom: 20px; }

  .mic-btn {
    width: 120px; height: 120px; border-radius: 50%;
    border: 4px solid #555; background: #1a1a2e; color: #ccc;
    font-size: 48px; cursor: pointer; transition: all 0.3s;
    margin: 10px auto; display: flex; align-items: center; justify-content: center;
    user-select: none; -webkit-user-select: none;
  }
  .mic-btn:hover { border-color: #888; }
  .mic-btn.listening { border-color: #44ff44; background: #1a3a1a; color: #44ff44; }
  .mic-btn.error { border-color: #ff4444; background: #3a1a1a; color: #ff4444; }
  @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(68,255,68,0.4); } 70% { box-shadow: 0 0 0 20px rgba(68,255,68,0); } 100% { box-shadow: 0 0 0 0 rgba(68,255,68,0); } }
  .mic-btn.listening { animation: pulse 1.5s infinite; }

  .status { font-size: 0.95em; min-height: 1.5em; color: #aaa; margin: 6px 0; }
  .result-box {
    background: rgba(255,255,255,0.05); border: 1px solid #444; border-radius: 12px;
    padding: 16px; min-height: 80px; margin: 15px 0; font-size: 1.1em; line-height: 1.6;
    text-align: left; white-space: pre-wrap; word-wrap: break-word; color: #ddd;
    max-height: 250px; overflow-y: auto;
  }
  .result-box:empty::before { content: "点击🎤说话，或直接在下方输入…"; color: #555; font-style: italic; }
  .btn-row { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin: 10px 0; }
  .btn {
    padding: 8px 18px; border: 1px solid #555; border-radius: 8px;
    background: #2a2a4a; color: #ddd; font-size: 0.9em; cursor: pointer; transition: all 0.2s;
  }
  .btn:hover { background: #3a3a5a; border-color: #888; }
  .btn.primary { background: #4a4a8a; border-color: #6666aa; }
  .btn.green { background: #2a5a2a; border-color: #4a8a4a; }
  .btn.green:hover { background: #3a6a3a; }

  .text-input { width: 100%; padding: 12px; border: 1px solid #444; border-radius: 8px;
    background: rgba(255,255,255,0.05); color: #ddd; font-size: 1em; resize: vertical;
    min-height: 60px; font-family: inherit; margin: 10px 0; }
  .text-input:focus { outline: none; border-color: #6666aa; }

  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin: 2px; }
  .badge-ok { background: #2a5a2a; color: #88ff88; }
  .badge-err { background: #5a2a2a; color: #ff8888; }
  .badge-warn { background: #5a5a2a; color: #ffff88; }

  .tab-bar { display: flex; gap: 0; margin: 10px 0; }
  .tab {
    flex: 1; padding: 10px; border: 1px solid #444; background: #1a1a2e;
    color: #888; cursor: pointer; font-size: 0.9em; transition: all 0.2s;
  }
  .tab:first-child { border-radius: 8px 0 0 8px; }
  .tab:last-child { border-radius: 0 8px 8px 0; }
  .tab.active { background: #2a2a4a; color: #fff; border-color: #6666aa; }
  .tab:hover { background: #2a2a4a; }

  .mode-panel { display: none; }
  .mode-panel.active { display: block; }

  .footer { margin-top: 25px; font-size: 0.8em; color: #555; }
  .tip { font-size: 0.85em; color: #777; margin: 5px 0; }
</style>
</head>
<body>
<div class="container">
  <h1>🎤 道归·语音输入</h1>
  <p class="subtitle">🌙 火狐/Chrome/Edge 通用 · 你说我看</p>

  <!-- 浏览器状态 -->
  <div style="margin-bottom: 10px;">
    <span id="detectStatus" class="badge badge-err">🔍 检测中…</span>
    <span id="browserName" class="badge badge-err">🌐 ?</span>
  </div>

  <!-- 模式切换 -->
  <div class="tab-bar">
    <div class="tab active" id="tabVoice" onclick="switchMode('voice')">🎤 语音</div>
    <div class="tab" id="tabType" onclick="switchMode('type')">⌨️ 手动</div>
  </div>

  <!-- 语音模式 -->
  <div class="mode-panel active" id="panelVoice">
    <div class="mic-btn" id="micBtn" onclick="toggleRecording()">🎤</div>
    <div class="status" id="voiceStatus">点击🎤开始说话</div>
    <div class="result-box" id="voiceResult" contenteditable="true"></div>
    <div class="tip" id="firefoxTip"></div>
  </div>

  <!-- 手动输入模式 -->
  <div class="mode-panel" id="panelType">
    <div class="status">直接在下方输入症状描述</div>
    <textarea class="text-input" id="textInput" placeholder="例如：失眠、心悸、烦躁不安、舌红少苔"></textarea>
  </div>

  <!-- 通用操作按钮 -->
  <div class="btn-row">
    <select id="langSelect" style="background:#1a1a2e;color:#ddd;border:1px solid #555;padding:8px;border-radius:6px;font-size:0.9em;">
      <option value="zh-CN">中文</option>
      <option value="zh-TW">中文(繁體)</option>
      <option value="en-US">English</option>
      <option value="ja-JP">日本語</option>
    </select>
    <button class="btn green" onclick="sendToDoctor()">🧑‍⚕️ 辨证</button>
    <button class="btn" onclick="getText()">📋 取文字</button>
    <button class="btn" onclick="clearAll()">🗑️ 清除</button>
  </div>

  <div class="footer">道归 · 本地语音输入 | 浏览器 Speech API + 手动备用</div>
</div>

<script>
// ── 模式切换 ──
function switchMode(mode) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.mode-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(mode === 'voice' ? 'tabVoice' : 'tabType').classList.add('active');
  document.getElementById(mode === 'voice' ? 'panelVoice' : 'panelType').classList.add('active');
  if (mode === 'voice' && !recognition) initSpeech();
  if (mode === 'voice' && isFirefox) showFirefoxTip();
}

// ── 浏览器检测 ──
let isFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
let isChrome = navigator.userAgent.toLowerCase().indexOf('chrome') > -1 && !isFirefox;
let browserName = isFirefox ? 'Firefox' : (isChrome ? 'Chrome' : '其他');

document.getElementById('browserName').textContent = '🌐 ' + browserName;
document.getElementById('browserName').className = 'badge ' + (isFirefox || isChrome ? 'badge-ok' : 'badge-warn');

function showFirefoxTip() {
  const tip = document.getElementById('firefoxTip');
  if (isFirefox) {
    tip.innerHTML = '💡 Firefox 语音: 说几句后如果自动停止，再点🎤继续即可。或者切换到⌨️手动模式输入。';
  } else {
    tip.innerHTML = '';
  }
}

// ── 语音识别 ──
let recognition = null;
let isRecording = false;
let finalTranscript = '';
let autoRestart = true;

function initSpeech() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const detectStatus = document.getElementById('detectStatus');

  if (!SpeechRecognition) {
    detectStatus.textContent = '❌ 不支持语音';
    detectStatus.className = 'badge badge-err';
    document.getElementById('voiceStatus').textContent = '⚠️ 当前浏览器不支持语音识别，请切换⌨️手动模式';
    return;
  }

  detectStatus.textContent = '✅ 就绪';
  detectStatus.className = 'badge badge-ok';
  document.getElementById('voiceStatus').textContent = '点击🎤开始说话';
  showFirefoxTip();
}

function createRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recog = new SpeechRecognition();
  recog.lang = document.getElementById('langSelect').value;
  recog.interimResults = !isFirefox;      // Firefox 上关掉中间结果更稳定
  recog.continuous = !isFirefox;           // Firefox 上关掉连续模式
  recog.maxAlternatives = 1;

  recog.onresult = function(event) {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
        document.getElementById('voiceResult').textContent = finalTranscript;
      } else if (!isFirefox) {
        // Chrome: 显示中间结果
        document.getElementById('voiceResult').textContent = finalTranscript + '…' + transcript;
      }
    }
    document.getElementById('voiceStatus').textContent = isFirefox ? '🎤 录音中…说完了点停止' : '🎤 正在听…';
  };

  recog.onerror = function(event) {
    console.log('Recognition error:', event.error);
    if (event.error === 'no-speech') {
      if (isRecording && isFirefox) {
        // Firefox 无语音超时后自动重启
        document.getElementById('voiceStatus').textContent = '🔄 自动重连…';
        setTimeout(() => { if (isRecording) tryCreate(); }, 300);
      } else {
        document.getElementById('voiceStatus').textContent = '⏸️ 未检测到语音，再点🎤重试';
        stopRecording();
      }
    } else if (event.error === 'not-allowed') {
      document.getElementById('voiceStatus').textContent = '❌ 麦克风权限被拒绝';
      document.getElementById('micBtn').className = 'mic-btn error';
    } else {
      document.getElementById('voiceStatus').textContent = '⚠️ ' + event.error;
      // Firefox 遇到错误自动重启
      if (isRecording && isFirefox) {
        setTimeout(() => { if (isRecording) tryCreate(); }, 500);
      } else {
        stopRecording();
      }
    }
  };

  recog.onend = function() {
    document.getElementById('micBtn').className = 'mic-btn';
    if (isRecording && isFirefox) {
      // Firefox 单次说完后自动重连
      tryCreate();
    } else if (isRecording && !isFirefox) {
      // Chrome continuous 模式不应该触发 onend
      tryCreate();
    }
  };

  return recog;
}

let retryCount = 0;
function tryCreate() {
  if (!isRecording) return;
  try {
    if (recognition) {
      try { recognition.abort(); } catch(e) {}
    }
    recognition = createRecognition();
    if (recognition) {
      recognition.start();
      document.getElementById('voiceStatus').textContent = '🎤 录音中…';
      retryCount = 0;
    }
  } catch(e) {
    retryCount++;
    if (retryCount < 3) {
      setTimeout(tryCreate, 500);
    } else {
      document.getElementById('voiceStatus').textContent = '❌ 启动失败，切换⌨️手动模式';
      stopRecording();
    }
  }
}

function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

function startRecording() {
  isRecording = true;
  autoRestart = true;
  retryCount = 0;
  document.getElementById('micBtn').className = 'mic-btn listening';
  document.getElementById('voiceStatus').textContent = '🎤 启动中…';
  finalTranscript = document.getElementById('voiceResult').textContent || '';
  tryCreate();
}

function stopRecording() {
  isRecording = false;
  autoRestart = false;
  document.getElementById('micBtn').className = 'mic-btn';
  document.getElementById('voiceStatus').textContent = '⏹️ 已停止';
  if (recognition) {
    try { recognition.abort(); } catch(e) {}
    try { recognition.stop(); } catch(e) {}
    recognition = null;
  }
}

// ── 通用功能 ──
function getText() {
  // 取当前模式下的文字
  const voiceText = document.getElementById('voiceResult').textContent.trim();
  const typedText = document.getElementById('textInput').value.trim();
  const text = typedText || voiceText;

  if (!text) {
    setStatus('⚠️ 没有可获取的内容');
    return '';
  }
  navigator.clipboard.writeText(text).then(() => {
    setStatus('✅ 已复制到剪贴板');
  }).catch(() => {
    // fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    setStatus('✅ 已复制');
  });
  return text;
}

function clearAll() {
  document.getElementById('voiceResult').textContent = '';
  document.getElementById('textInput').value = '';
  finalTranscript = '';
  setStatus('已清除');
}

function sendToDoctor() {
  const voiceText = document.getElementById('voiceResult').textContent.trim();
  const typedText = document.getElementById('textInput').value.trim();
  const text = typedText || voiceText;

  if (!text) {
    setStatus('⚠️ 请先说话或输入');
    return;
  }

  setStatus('🔍 请联系道归辨证…');

  // 复制到剪贴板，方便粘贴到对话框
  navigator.clipboard.writeText(text).then(() => {
    setStatus('✅ 已复制到剪贴板 - 粘贴到对话框发送给道归');
  }).catch(() => {
    setStatus('📋 文字已准备: ' + text.slice(0, 40) + '…');
  });

  // 尝试调用本地辨证
  fetch('/diagnose', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: text })
  })
  .then(r => r.json())
  .then(data => {
    if (data.done) {
      setStatus('✅ 已发送');
    }
  })
  .catch(() => {
    // 本地服务可能没跑起来，静默忽略
  });
}

function setStatus(msg) {
  document.getElementById('voiceStatus').textContent = msg;
}

// ── 键盘快捷键 ──
document.addEventListener('keydown', function(e) {
  if (e.code === 'Space' && !e.target.matches('input, textarea, [contenteditable]')) {
    e.preventDefault();
    const mode = document.getElementById('panelVoice').classList.contains('active');
    if (mode) toggleRecording();
  }
  if (e.code === 'Escape' && isRecording) stopRecording();
  if (e.code === 'Enter' && (e.ctrlKey || e.metaKey)) sendToDoctor();
});

// ── 初始化 ──
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(initSpeech, 300);
  if (isFirefox) showFirefoxTip();
});
</script>
</body>
</html>
"""


def build_html() -> str:
    """写入 HTML 文件"""
    HTML_PATH.write_text(HTML_TEMPLATE, encoding="utf-8")
    return str(HTML_PATH)


class VoiceHandler(http.server.BaseHTTPRequestHandler):
    """HTTP 服务"""

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            html = HTML_PATH.read_text(encoding="utf-8") if HTML_PATH.exists() else HTML_TEMPLATE
            self.wfile.write(html.encode("utf-8"))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "browser_compat": "firefox,chrome,edge,safari"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/diagnose":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            try:
                data = json.loads(body)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"done": True, "text": data.get("text", "")}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    html_path = build_html()
    print(f"\n{'═' * 50}")
    print(f"🎤 道归 · 语音输入桥接器 (火狐适配版)")
    print(f"{'═' * 50}")
    print(f"\n  🌐 打开浏览器访问:")
    print(f"     http://localhost:{PORT}")
    print(f"\n  🎯 两种模式：")
    print(f"     语音模式 🎤 — 点🎤开始说话，再点停止")
    print(f"     手动模式 ⌨️ — 直接打字输入")
    print(f"\n  📋 操作流程：")
    print(f"     1. 说/打字")
    print(f"     2. 点「取文字」复制到剪贴板")
    print(f"     3. 粘贴到对话框发给我")
    print(f"\n  🔒 纯本地，数据不上传任何服务器")
    print(f"  🔥 Firefox 已适配（单次模式+自动重连）")
    print(f"{'═' * 50}\n")

    server = http.server.HTTPServer(("0.0.0.0", PORT), VoiceHandler)
    print(f"服务已启动，按 Ctrl+C 停止")

    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
