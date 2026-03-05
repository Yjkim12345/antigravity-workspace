import os
import sys
import json
import argparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Anonymization Review Dashboard</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }
  .container { max-width: 900px; margin: 40px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  h1 { color: #2c3e50; margin-top: 0; border-bottom: 2px solid #ecf0f1; padding-bottom: 15px; }
  .info { color: #7f8c8d; font-size: 15px; margin-bottom: 25px; }
  .candidate-row { display: flex; align-items: center; padding: 12px 10px; border-bottom: 1px solid #f1f2f6; transition: background 0.2s; }
  .candidate-row:hover { background-color: #f8f9fa; }
  .candidate-row.ignored { opacity: 0.5; }
  .term { flex: 1.5; font-weight: 600; font-size: 16px; color: #2c3e50; }
  .replacement { flex: 1; display:flex; align-items:center; }
  input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ced4da; border-radius: 6px; font-size: 14px; outline: none; transition: border-color 0.3s; }
  input[type="text"]:focus { border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }
  input[type="checkbox"] { transform: scale(1.3); margin-right: 15px; cursor: pointer; }
  .actions { margin-top: 30px; text-align: right; }
  button { background-color: #3498db; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.3s; box-shadow: 0 2px 4px rgba(52,152,219,0.3); }
  button:hover { background-color: #2980b9; }
  .toast { position: fixed; bottom: 20px; right: 20px; background: #2ecc71; color: white; padding: 15px 25px; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: none; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
  <h1>🛡️ Anonymization Review Dashboard</h1>
  <p class="info">체크된 단어들만 최종 식별자(가명)로 치환됩니다. 필요 없는 단어는 체크를 해제하세요.</p>
  <div id="list"></div>
  <div class="actions">
    <button onclick="save()">💾 확정 및 매핑 저장 (Save All)</button>
  </div>
</div>
<div class="toast" id="toast">✅ 성공적으로 저장되었습니다! 이 창을 닫아도 됩니다.</div>

<script>
  let candidates = [];
  
  function toggleRow(idx) {
    const chk = document.getElementById(`chk_${idx}`);
    const row = document.getElementById(`row_${idx}`);
    if(chk.checked) row.classList.remove('ignored');
    else row.classList.add('ignored');
  }

  fetch('/api/candidates').then(r => r.json()).then(data => {
    candidates = data;
    const list = document.getElementById('list');
    data.forEach((c, i) => {
      let div = document.createElement('div');
      div.className = 'candidate-row';
      div.id = `row_${i}`;
      
      // Auto-suggest tags based on the word length or typical patterns if desired
      // Default to [가명 1] style
      let defaultTag = "[가명]";
      if(c.includes("법무법인") || c.includes("합동법률")) defaultTag = "[법무법인]";
      else if(c.includes("병원") || c.includes("내과") || c.includes("의원")) defaultTag = "[병원]";
      else if(c.length >= 2 && c.length <= 4 && !c.includes(" ")) defaultTag = "[가명]";
      else defaultTag = "[단체명]";

      div.innerHTML = `
        <input type="checkbox" id="chk_${i}" checked onchange="toggleRow(${i})">
        <div class="term">${c}</div>
        <div class="replacement">
          <input type="text" id="rep_${i}" value="${defaultTag}" placeholder="치환할 가명 (예: [가명 1])">
        </div>
      `;
      list.appendChild(div);
    });
  });

  function save() {
    let mapping = {};
    candidates.forEach((c, i) => {
      if (document.getElementById(`chk_${i}`).checked) {
        let rep = document.getElementById(`rep_${i}`).value.trim();
        if(rep) mapping[c] = rep;
      }
    });
    
    fetch('/api/save', {
      method: 'POST', 
      body: JSON.stringify(mapping),
      headers: {'Content-Type': 'application/json'}
    }).then(r => r.json()).then(res => {
      const toast = document.getElementById('toast');
      toast.style.display = 'block';
      setTimeout(() => toast.style.display = 'none', 4000);
    }).catch(err => alert("저장 중 오류가 발생했습니다. 터미널을 확인하세요."));
  }
</script>
</body>
</html>
"""

class ReviewHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress logging

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/candidates':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            try:
                with open(self.server.candidates_file, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.wfile.write(data.encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps([]).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                mapping = json.loads(post_data)
                # Save to final_mapping_table.json
                out_path_json = os.path.join(self.server.target_dir, "final_mapping_table.json")
                with open(out_path_json, 'w', encoding='utf-8') as f:
                    json.dump(mapping, f, ensure_ascii=False, indent=4)
                
                # Save to final_mapping_table.txt
                out_path_txt = os.path.join(self.server.target_dir, "final_mapping_table.txt")
                with open(out_path_txt, 'w', encoding='utf-8') as f:
                    for term, rep in mapping.items():
                        f.write(f"{rep}: \"{term}\"\n")
                        
                print(f"Mapping saved to {out_path_json} and {out_path_txt} ({len(mapping)} items)")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
                
            except Exception as e:
                print(f"Error saving: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def main():
    parser = argparse.ArgumentParser(description="Start the Review Dashboard")
    parser.add_argument("target_dir", help="Directory containing candidates.json")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the dashboard on")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.target_dir)
    candidates_file = os.path.join(target_dir, "candidates.json")

    if not os.path.exists(candidates_file):
        print(f"Error: {candidates_file} not found.")
        print("Please run step 1 & 2 first (run_pipeline.py).")
        sys.exit(1)

    server = HTTPServer(('127.0.0.1', args.port), ReviewHandler)
    server.target_dir = target_dir
    server.candidates_file = candidates_file
    
    url = f"http://127.0.0.1:{args.port}"
    print("="*60)
    print(f"Review Dashboard running at: {url}")
    print(f"Press CTRL+C in this terminal to stop.")
    print("="*60)

    # Open browser automatically after a short delay
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Review Dashboard...")
        server.server_close()

if __name__ == "__main__":
    main()
