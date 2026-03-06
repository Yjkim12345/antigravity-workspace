import os
import time
import shutil
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from winotify import Notification, audio

# Import the existing atomize function and notion uploader
from knowledge_atomizer import atomize_text, create_notion_page

# Configure folders natively on the Desktop
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
WATCH_DIR = os.path.join(DESKTOP_DIR, "노션_자동업로드")
ARCHIVE_DIR = os.path.join(WATCH_DIR, "처리완료")

def setup_directories():
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR)
        print(f"[*] Created watch directory: {WATCH_DIR}")
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
        print(f"[*] Created archive directory: {ARCHIVE_DIR}")

class NotionUploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        # We only care about file creation events
        if event.is_directory:
            return
            
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # We only process text or markdown files
        if not (filename.lower().endswith(".txt") or filename.lower().endswith(".md")):
            return
            
        print(f"\n[+] 새 파일 감지됨: {filename}")
        
        # Start processing in a background thread
        threading.Thread(target=self.process_file, args=(filepath, filename)).start()
        
    def process_file(self, filepath, filename):
        try:
            # Let the file finish writing if it was just copies
            time.sleep(1) 
            
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                
            if not text.strip():
                print("빈 파일입니다. 무시합니다.")
                return

            Notification(app_id="Antigravity Watchdog",
                         title="새로운 문서 감지됨",
                         msg=f"'{filename}' 파일을 노션으로 원자화 전송합니다...",
                         duration="short").show()

            # Run atomization
            result = atomize_text(text)
            card_count = len(result.cards) if result and hasattr(result, 'cards') else 0
            
            # Upload to notion
            if card_count > 0:
                for card in result.cards:
                    create_notion_page(card)
                    
            msg = f"'{filename}' 원자화 및 노션 전송 완료! ({card_count}개 카드 추가됨)"
            print(msg)
            
            # Show success toast
            Notification(app_id="Antigravity Watchdog",
                         title="노션 일괄 업로드 완료",
                         msg=msg,
                         duration="short").show()
                         
            # Archive the file
            current_time = int(time.time())
            new_filename = f"{current_time}_{filename}"
            shutil.move(filepath, os.path.join(ARCHIVE_DIR, new_filename))
            print(f"[*] 처리 완료된 파일을 보관함으로 이동했습니다: {new_filename}")
            
        except Exception as e:
            err_msg = f"오류 발생: {str(e)}"
            print(err_msg)
            Notification(app_id="Antigravity Watchdog",
                         title="업로드 오류",
                         msg=err_msg,
                         duration="long").show()

if __name__ == "__main__":
    setup_directories()
    
    event_handler = NotionUploadHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    
    print("==========================================================")
    print(" [안티그래비티 Zero-Click] 폴더 감시 봇 가동 ")
    print("==========================================================")
    print(f"감시 폴더: {WATCH_DIR}")
    print(f"위 폴더에 .txt 나 .md 파일을 넣으면 자동으로 노션 DB로 전송됩니다.")
    print("종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.")
    print("==========================================================")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("폴더 감시 봇을 종료합니다.")
        
    observer.join()
