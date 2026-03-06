import urllib.request
import json
import os

with open(r'c:\Users\user\.gemini\antigravity\mcp_config.json', 'r') as f:
    config = json.load(f)

headers_str = config['mcpServers']['notion-mcp-server']['env']['OPENAPI_MCP_HEADERS']
NOTION_API_KEY = json.loads(headers_str)['Authorization'].replace('Bearer ', '')

DB_ID = "31b063a28bb180b1a135ebc3f6813a3c"
url = f"https://api.notion.com/v1/databases/{DB_ID}/query"

req = urllib.request.Request(url, method='POST')
req.add_header('Authorization', f'Bearer {NOTION_API_KEY}')
req.add_header('Notion-Version', '2022-06-28')
req.add_header('Content-Type', 'application/json')

res = urllib.request.urlopen(req, data=b'{}')
data = json.loads(res.read())
results = data.get("results", [])

print(f'Total pages found: {len(results)}')
for page in results:
    title_prop = page['properties'].get('이름', {}).get('title', [])
    title = title_prop[0]['text']['content'] if title_prop else 'Untitled'
    print(f'- [{page["id"]}] {title}')
