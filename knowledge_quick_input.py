import os
import sys
import threading
from tkinter import Tk, Text, BOTH, END
from winotify import Notification
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from knowledge_atomizer import atomize_text, insert_to_supabase

def bg_process_and_upload(content, root):
    Notification(app_id="Antigravity Notepad",
                 title="메모 작성 완료",
                 msg="작성하신 메모를 Supabase DB로 전송합니다...",
                 duration="short").show()
    try:
        result = atomize_text(content)
        card_count = len(result.cards) if result and hasattr(result, 'cards') else 0
        if card_count > 0:
            for card in result.cards:
                insert_to_supabase(card)
        msg = f"메모가 분석되어 {card_count}개의 카드로 DB에 저장되었습니다." if card_count > 0 else "추출된 지식 카드가 없습니다."
        Notification(app_id="Antigravity Notepad",
                     title="업로드 완료",
                     msg=msg,
                     duration="short").show()
    except Exception as e:
        Notification(app_id="Antigravity Notepad",
                     title="업로드 오류",
                     msg=f"전송 중 오류: {str(e)}",
                     duration="long").show()
    finally:
        root.destroy()
        sys.exit(0)

def on_save(event, text_widget, root):
    content = text_widget.get("1.0", END).strip()
    if not content:
        Notification(app_id="Antigravity Notepad", title="알림", msg="입력된 내용이 없어 취소합니다.", duration="short").show()
        root.destroy()
        sys.exit(0)
        return "break"
        
    # Start the background upload (pass root so it can be destroyed when done)
    threading.Thread(target=bg_process_and_upload, args=(content, root), daemon=False).start()
    
    # Hide the window immediately so the user thinks it closed
    root.withdraw()
    
    return "break" # Prevent default Ctrl+S behavior

def main():
    root = Tk()
    root.title("Antigravity 법리 메모장 (Ctrl+S로 저장 및 노션 전송)")
    root.geometry("600x400")
    
    # Configure grid behavior
    text_widget = Text(root, font=("맑은 고딕", 12), wrap="word")
    text_widget.pack(fill=BOTH, expand=True, padx=10, pady=10)
    text_widget.focus_set()
    
    # Bind Ctrl+S
    root.bind("<Control-s>", lambda event: on_save(event, text_widget, root))
    root.bind("<Control-S>", lambda event: on_save(event, text_widget, root))

    root.mainloop()

if __name__ == "__main__":
    main()
