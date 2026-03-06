# Antigravity Zero-Click Automation Archive

본 문서는 안티그래비티 노션 자동화(Zero-Click) 파이프라인 구축을 위해 작성된 핵심 스크립트 모음집입니다. 향후 환경 복원이나 타 PC 세팅 시 아래 스크립트들을 활용할 수 있습니다.

## 1. 윈도우 시작프로그램 스크립트 (VBS)
위치: `C:\Users\SAMSUNG\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
컴퓨터 부팅 시 검은 콘솔 창 없이 백그라운드에서 자동화 봇들을 실행시키는 역할. 로그를 파일로 기록함.

### `startup_hotkey.vbs`
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c ""cd /d C:\Users\SAMSUNG\.gemini\antigravity\sync_workspace && python -u knowledge_hotkey.py > hotkey.log 2>&1""", 0, False
```

### `startup_watchdog.vbs`
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c ""cd /d C:\Users\SAMSUNG\.gemini\antigravity\sync_workspace && node knowledge_watchdog.js > watchdog.log 2>&1""", 0, False
```

---

## 2. 노션 지식 원자화 코어 (Python)
위치: `C:\Users\SAMSUNG\.gemini\antigravity\sync_workspace`
Gemini AI를 이용해 텍스트에서 한줄법리를 추출하고, Notion DB로 업로드하는 공통 모듈.

### `knowledge_atomizer.py`
```python
import os
import sys
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from datetime import datetime

# ==========================================
# 0. CONFIGURATION
# ==========================================

home_dir = os.path.expanduser("~")
config_path1 = os.path.join(home_dir, '.gemini', 'antigravity', 'mcp_settings.json')
config_path2 = os.path.join(home_dir, '.gemini', 'antigravity', 'mcp_config.json')

config_path = config_path1 if os.path.exists(config_path1) else (config_path2 if os.path.exists(config_path2) else None)

if not config_path:
    print(f"Config file not found. Checked: \n{config_path1}\n{config_path2}")
    sys.exit(1)

with open(config_path, "r", encoding="utf-8") as f:
    try:
        config = json.load(f)
    except json.JSONDecodeError:
        config = {}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
NOTION_API_KEY = ""

if "mcpServers" in config and "notion-mcp-server" in config["mcpServers"]:
    GEMINI_API_KEY = config.get("GEMINI_API_KEY", GEMINI_API_KEY)
    try:
        headers_str = config["mcpServers"]["notion-mcp-server"]["env"].get("OPENAPI_MCP_HEADERS", "{}")
        headers_dict = json.loads(headers_str)
        NOTION_API_KEY = headers_dict.get("Authorization", "").replace("Bearer ", "")
    except Exception as e:
        print(f"Failed to parse Notion headers: {e}")
elif config.get("notionApiKey"):
    NOTION_API_KEY = config.get("notionApiKey")
    GEMINI_API_KEY = config.get("geminiApiKey", GEMINI_API_KEY)

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

NOTION_DB_ID = "31b063a28bb180b1a135ebc3f6813a3c"

client = genai.Client()

# ==========================================
# 1. GEMINI SCHEMA DEFINITION
# ==========================================

class KnowledgeCard(BaseModel):
    title: str = Field(description="'~여부', '~요건' 등의 명사형 제목")
    one_line_principle: str = Field(description="단 1~3줄의 초응축된 핵심 법칙 (한줄법리)")
    related_laws: str = Field(description="관련 법령 (예: '민법 제1008조, 상속세법 제4조')")
    keywords: str = Field(description="검색용 핵심 키워드 (예: '#상속회복청구 #가분채권')")
    source: str = Field(description="원문 출처 또는 사건번호 (예: '대법원 2025다212863')")
    card_type: str = Field(description="지식 유형. 다음 중 하나만 선택: '일반법리', '공격논리', '방어논리', '절차팁', '기재례', '소수설'")
    detailed_text: str = Field(description="이 한줄법리를 도출해낸 원본 판결문/문서의 원문 발췌 단락 (상세 내용)")

class AtomizationResult(BaseModel):
    cards: list[KnowledgeCard] = Field(description="입력된 문서에서 추출된 핵심 법리 카드 목록 (문서 길이가 짧다면 반드시 1개, 아주 길고 복합적인 경우에만 최대 2~3개 추출. 과도한 쪼개기 금지.)")


SYSTEM_PROMPT = """당신은 대한민국의 최고참 파트너 변호사이자 제텔카스텐(Zettelkasten) 지식 아키텍트입니다.

[지시사항]
사용자가 판례나 법리를 제공하면, 이를 분석하여 '독립적으로 재활용 가능한 추상화된 법리'로 정리하십시오.

[원자화 3대 원칙 및 💥제한사항💥]
1. (중요) 과도한 쪼개기(Over-atomization)를 엄격히 금지합니다. 비슷한 맥락이나 같은 판례 안에서 도출되는 연관된 법리들은 억지로 분리하지 말고, 가장 핵심이 되는 1개의 카드로 통합하여 굵직하게 뽑아내십시오.
2. 입력된 텍스트가 A4 반 페이지 이하의 짧은 판결요지나 단일 단락이라면, 무조건 '단 1개의 지식 카드'만 생성하십시오.
3. 사안의 구체적 사실관계와 추상화된 법리를 분리하되, '한줄법리'에는 결론을, '상세내용'에는 그 결론을 뒷받침하는 원문 전체를 풍부하게 담으십시오.
"""

def atomize_text(text: str) -> AtomizationResult:
    print(f"[*] Analyzing and atomizing text with Gemini (Length: {len(text)} chars)...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AtomizationResult,
            temperature=0.2,
        ),
    )
    
    return response.parsed

# ==========================================
# 2. NOTION API INTEGRATION
# ==========================================
import urllib.request
import urllib.error

def create_notion_page(card: KnowledgeCard):
    url = "https://api.notion.com/v1/pages"
    
    one_line = card.one_line_principle[:2000]
    laws = card.related_laws[:2000]
    tags = card.keywords[:2000]
    source = card.source[:2000]
    card_type = card.card_type if card.card_type in ["일반법리", "공격논리", "방어논리", "절차팁", "기재례", "소수설"] else "일반법리"
    
    data = {
        "parent": { "database_id": NOTION_DB_ID },
        "properties": {
            "이름": { "title": [ { "text": { "content": card.title } } ] },
            "한줄법리": { "rich_text": [ { "text": { "content": one_line } } ] },
            "관련 법령": { "rich_text": [ { "text": { "content": laws } } ] },
            "키워드": { "rich_text": [ { "text": { "content": tags } } ] },
            "사건번호/출처": { "rich_text": [ { "text": { "content": source } } ] },
            "Type": { "select": { "name": card_type } }
        },
        "children": [
            { "object": "block", "type": "heading_3", "heading_3": { "rich_text": [{"type": "text", "text": {"content": "📖 상세 내용 (원문 발췌)"}}] } },
            { "object": "block", "type": "quote", "quote": { "rich_text": [{"type": "text", "text": {"content": card.detailed_text[:2000]}}] } },
            { "object": "block", "type": "divider", "divider": {} },
            { "object": "block", "type": "heading_3", "heading_3": { "rich_text": [{"type": "text", "text": {"content": "🧠 변호사 코멘트 / 실무 적용 메모"}}] } }
        ]
    }
    
    req = urllib.request.Request(url, method="POST")
    req.add_header("Authorization", f"Bearer {NOTION_API_KEY}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    
    try:
        response = urllib.request.urlopen(req, data=json.dumps(data).encode("utf-8"))
        res_data = json.loads(response.read())
        print(f"[+] Successfully created Notion page: {card.title}")
        return res_data
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"[-] Failed to create Notion page. Status: {e.code}, Error: {err_msg}")
        return None

def main(file_path: str):
    if not os.path.exists(file_path): return
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    result = atomize_text(text)
    for i, card in enumerate(result.cards):
        create_notion_page(card)

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        main(sys.argv[1])
```

---

## 3. 단축키 데몬 봇 (Python)
위치: `C:\Users\SAMSUNG\.gemini\antigravity\sync_workspace`
사용자가 `Ctrl+Alt+N`을 누르면 클립보드를 읽어 원자화 코어에 넘겨줌. 백그라운드 스레드를 사용하여 UI 멈춤 현상(Freezing) 방지.

### `knowledge_hotkey.py`
```python
import time
import keyboard
import pyperclip
from winotify import Notification, audio
import threading
import sys

from knowledge_atomizer import atomize_text, AtomizationResult, create_notion_page

class AtomizeWorker(threading.Thread):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            Notification(app_id="Antigravity Automation",
                         title="노션 자동업로드 동작 중",
                         msg="Gemini AI가 원자화를 진행하고 있습니다...",
                         duration="short").show()
            
            result = atomize_text(self.text)
            card_count = len(result.cards) if result and hasattr(result, 'cards') else 0
            
            if card_count > 0:
                for card in result.cards:
                    create_notion_page(card)
                    
            msg = f"노션 '법리모음'에 {card_count}개의 카드가 추가되었습니다." if card_count > 0 else "추출된 지식 카드가 없습니다."
            
            Notification(app_id="Antigravity Automation", title="노션 자동업로드 완료", msg=msg, duration="short").show()
            
        except Exception as e:
            Notification(app_id="Antigravity Automation", title="노션 자동업로드 오류", msg=f"오류가 발생했습니다: {str(e)}", duration="long").show()
            print(f"Error during atomization: {e}")

def on_hotkey_pressed():
    try:
        text = pyperclip.paste()
        if not text or len(text.strip()) < 10:
            Notification(app_id="Antigravity Automation", title="노션 자동업로드 실패", msg="클립보드에 충분한 텍스트가 없습니다.", duration="short").show()
            return

        worker = AtomizeWorker(text)
        worker.start()
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    HOTKEY = 'ctrl+alt+n'
    keyboard.add_hotkey(HOTKEY, on_hotkey_pressed)
    keyboard.wait()
```

---

## 4. 폴더 감시 데몬 봇 (Node.js)
위치: `C:\Users\SAMSUNG\.gemini\antigravity\sync_workspace`
바탕화면의 `노션_자동업로드` 폴더에 파일이 생성(Drag&Drop 등)되면, 바로 감지하여 원자화 코어에 넘겨줌. 처리가 끝나면 `처리완료` 폴더로 이동.

### `knowledge_watchdog.js`
```javascript
import fs from 'fs';
import path from 'path';
import chokidar from 'chokidar';
import notifier from 'node-notifier';
import { atomizeText, createNotionPage } from './knowledge_atomizer.js';

const DESKTOP_DIR = path.join(process.env.USERPROFILE, 'Desktop');
const WATCH_DIR = path.join(DESKTOP_DIR, '노션_자동업로드');
const ARCHIVE_DIR = path.join(WATCH_DIR, '처리완료');

function setupDirectories() {
    if (!fs.existsSync(WATCH_DIR)) {
        fs.mkdirSync(WATCH_DIR, { recursive: true });
    }
    if (!fs.existsSync(ARCHIVE_DIR)) {
        fs.mkdirSync(ARCHIVE_DIR, { recursive: true });
    }
}

async function processFile(filepath) {
    const filename = path.basename(filepath);

    if (!(filename.toLowerCase().endsWith('.txt') || filename.toLowerCase().endsWith('.md'))) {
        return;
    }

    await new Promise(resolve => setTimeout(resolve, 1500)); // 파일 쓰기 대기

    try {
        const text = fs.readFileSync(filepath, 'utf8');
        if (!text.trim()) return;

        notifier.notify({
            title: "새로운 문서 감지됨",
            message: `'${filename}' 파일을 노션으로 원자화 전송합니다...`,
            appID: "Antigravity Watchdog"
        });

        const result = await atomizeText(text);
        const cardCount = result?.cards?.length || 0;

        if (cardCount > 0) {
            for (const card of result.cards) {
                await createNotionPage(card);
            }
        }

        const msg = `'${filename}' 원자화 및 노션 전송 완료! (${cardCount}개 카드 추가됨)`;
        notifier.notify({ title: "노션 일괄 업로드 완료", message: msg, appID: "Antigravity Watchdog" });

        const newFilename = `${Math.floor(Date.now() / 1000)}_${filename}`;
        const newFilePath = path.join(ARCHIVE_DIR, newFilename);
        fs.renameSync(filepath, newFilePath);

    } catch (e) {
        console.error(`오류 발생: ${e.message}`);
        notifier.notify({ title: "업로드 오류", message: `오류 발생: ${e.message}`, appID: "Antigravity Watchdog" });
    }
}

setupDirectories();

const watcher = chokidar.watch(WATCH_DIR, {
    ignored: /(^|[\/\\])\../,
    persistent: true,
    depth: 0,
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 1000, pollInterval: 100 }
});

watcher.on('add', (filepath) => {
    processFile(filepath).catch(e => console.error("Unhandled error processing file:", e));
});

process.on('SIGINT', () => {
    watcher.close().then(() => { process.exit(0); });
});
```

---

## 5. 의존성 정보 (package.json)
```json
{
    "name": "antigravity_automation",
    "version": "1.0.0",
    "type": "module",
    "dependencies": {
        "@google/genai": "^1.44.0",
        "@notionhq/client": "^5.11.1",
        "chokidar": "^5.0.0",
        "clipboardy": "^5.3.1",
        "node-global-key-listener": "^0.3.0",
        "node-notifier": "^10.0.1"
    }
}
```

(파이썬 의존성 명령어: `pip install google-genai pydantic keyboard pyperclip winotify`)
