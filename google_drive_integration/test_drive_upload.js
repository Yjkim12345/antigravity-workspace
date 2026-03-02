const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

// 1. 서비스 계정 키 파일 경로 설정
const KEYFILEPATH = path.join(__dirname, 'drive-credentials.json');
// 2. 요청할 권한(스코프) 설정: 파일 읽기/쓰기 권한
const SCOPES = ['https://www.googleapis.com/auth/drive.file'];

async function uploadFileToDrive(fileName, filePath, folderId) {
    try {
        // 3. 인증 객체 생성
        const auth = new google.auth.GoogleAuth({
            keyFile: KEYFILEPATH,
            scopes: SCOPES,
        });

        const driveService = google.drive({ version: 'v3', auth });

        // 4. 업로드할 파일 메타데이터 및 스트림 설정
        const fileMetadata = {
            name: fileName,
            // 💡 중요: 서비스 계정은 기본 저장 용량이 없으므로, 반드시 기존 드라이브의 "공유 폴더" ID를 지정해야 합니다.
            parents: folderId ? [folderId] : []
        };

        const media = {
            mimeType: 'text/plain', // 업로드할 파일의 MIME 타입
            body: fs.createReadStream(filePath),
        };

        console.log(`[Google Drive] 업로드 시작: ${fileName}...`);

        // 5. 파일 업로드 API 호출
        const response = await driveService.files.create({
            resource: fileMetadata,
            media: media,
            fields: 'id, name, webViewLink, webContentLink',
            supportsAllDrives: true,
        });

        console.log(`[Google Drive] 업로드 성공! 🎉`);
        console.log(`- 파일 ID: ${response.data.id}`);
        console.log(`- 브라우저 링크: ${response.data.webViewLink}`);

        return response.data;
    } catch (error) {
        console.error('[Google Drive] 에러 발생:', error.message);
    }
}

// ---------------------------------------------------------
// [테스트 실행 영역]
// ---------------------------------------------------------

// 🚨 여기에 구글 드라이브에서 복사한 '폴더 ID'를 문자열로 입력하세요!
// 예: '1A2b3C4d5E6f7G8h9I0j_K1l2M3n4O5p'
const TARGET_FOLDER_ID = '1JefLBBovwHNMfGH50T-RxhC3vwykR7qt';

const testFileName = 'drive_test_hello.txt';
const testFilePath = path.join(__dirname, testFileName);

// 업로드를 테스트할 텍스트 파일 생성
fs.writeFileSync(testFilePath, 'Hello Google Drive! This file was uploaded by a Service Account.', 'utf8');

if (TARGET_FOLDER_ID === '여기에_폴더_ID를_입력하세요') {
    console.log(`
================================================================
⚠️ 실행 전 주의사항 ⚠️
1. 구글 드라이브에서 업로드할 폴더를 하나 만듭니다.
2. 해당 폴더를 우클릭하고 '공유'를 누릅니다.
3. 서비스 계정 이메일 주소를 붙여넣고 권한을 '편집자(Editor)'로 줍니다.
4. 폴더의 URL(웹 링크)에서 'folders/' 뒤에 나오는 영문/숫자 조합이 '폴더 ID'입니다.
5. 이 코드의 'TARGET_FOLDER_ID' 변수 값을 해당 폴더 ID로 변경하고 다시 실행하세요.
================================================================
    `);
} else {
    // 업로드 함수 호출
    uploadFileToDrive(testFileName, testFilePath, TARGET_FOLDER_ID).then(() => {
        // (선택) 로컬 테스트 파일 삭제
        // fs.unlinkSync(testFilePath);
    });
}
