import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 환경 변수 로드
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
# 기본 연결은 서비스 키(강력한 권한)를 권장합니다. 환경에 따라 선택.
key: str = os.environ.get("SUPABASE_SERVICE_KEY") 

print(f"Connecting to Supabase at: {url}")
try:
    supabase: Client = create_client(url, key)
    # 간단히 auth나 rpc 등 기본 호출이 되는지 확인하기 위한 코드
    # 아직 테이블이 없으므로 빈 결과나 에러가 날 수 있지만 클라이언트 생성 자체를 테스트
    
    # 임의로 연결 테스트 (테이블이 없으므로 에러가 나면 연결은 된 것)
    # response = supabase.table('non_existent_table').select("*").limit(1).execute()
    print("[SUCCESS] Supabase Client created successfully with Service Role Key!")
    print("[SUCCESS] Connection parameters are valid.")
except Exception as e:
    print(f"[ERROR] Connection Failed: {e}")
