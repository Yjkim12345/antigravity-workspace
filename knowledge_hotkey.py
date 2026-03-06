import time
import keyboard
import pyperclip
from winotify import Notification, audio
import threading

# Import the existing atomize function, models, and notion uploader
from knowledge_atomizer import atomize_text, AtomizationResult, create_notion_page

class AtomizeWorker(threading.Thread):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            # Show processing toast
            Notification(app_id="Antigravity Automation",
                         title="노션 자동업로드 동작 중",
                         msg="Gemini AI가 원자화를 진행하고 있습니다...",
                         duration="short").show()
            
            # Run atomization
            result = atomize_text(self.text)
            
            card_count = len(result.cards) if result and hasattr(result, 'cards') else 0
            
            # Upload to notion
            if card_count > 0:
                for card in result.cards:
                    create_notion_page(card)
                    
            msg = f"노션 '법리모음'에 {card_count}개의 카드가 추가되었습니다." if card_count > 0 else "추출된 지식 카드가 없습니다."
            
            # Show success toast
            Notification(app_id="Antigravity Automation",
                         title="노션 자동업로드 완료",
                         msg=msg,
                         duration="short").show()
            
        except Exception as e:
            # Show error toast
            Notification(app_id="Antigravity Automation",
                         title="노션 자동업로드 오류",
                         msg=f"오류가 발생했습니다: {str(e)}",
                         duration="long").show()
            print(f"Error during atomization: {e}")

def on_hotkey_pressed():
    """Triggered when the user presses the hotkey."""
    print("단축키 감지! 클립보드 텍스트를 읽어옵니다...")
    try:
        # Get text from clipboard
        text = pyperclip.paste()
        
        if not text or len(text.strip()) < 10:
            print("클립보드에 충분한 텍스트가 없습니다.")
            Notification(app_id="Antigravity Automation",
                         title="노션 자동업로드 실패",
                         msg="클립보드에 충분한 텍스트가 복사되지 않았습니다.",
                         duration="short").show()
            return

        print(f"클립보드 텍스트 확인 완료 (길이: {len(text)}자). 백그라운드 처리를 시작합니다.")
        
        # Start worker thread so it doesn't block the UI / keyboard listener
        worker = AtomizeWorker(text)
        worker.start()
        
    except Exception as e:
        print(f"클립보드 접근 중 오류 발생: {e}")

if __name__ == "__main__":
    HOTKEY = 'ctrl+alt+n'
    print("==========================================================")
    print(" [안티그래비티 Zero-Click 자동화] 단축키 스크립트 가동 ")
    print("==========================================================")
    print(f"엘박스나 웹 등에서 텍스트를 복사(Ctrl+C)한 후,")
    print(f"'{HOTKEY}' 단축키를 누르면 자동으로 노션에 전송됩니다.")
    print("종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.")
    print("==========================================================")
    
    # Register the hotkey
    keyboard.add_hotkey(HOTKEY, on_hotkey_pressed)
    
    # Keep the script running
    keyboard.wait()
