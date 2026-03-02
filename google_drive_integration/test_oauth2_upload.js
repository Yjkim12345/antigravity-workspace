const fs = require('fs');
const readline = require('readline');
const { google } = require('googleapis');
const path = require('path');

// 권한 설정: 구글 드라이브 파일 읽기/쓰기 권한
const SCOPES = ['https://www.googleapis.com/auth/drive.file'];
// 토큰을 저장할 파일 경로 (재로그인 방지)
const TOKEN_PATH = path.join(__dirname, 'token.json');
// 다운로드 받은 OAuth 2.0 클라이언트 ID 파일 경로
const CREDENTIALS_PATH = path.join(__dirname, 'oauth2-credentials.json');

/**
 * 1. 인증 정보를 로드하고 Google API 클라이언트를 인증합니다.
 */
function authorize(credentials, callback) {
    const { client_secret, client_id, redirect_uris } = credentials.installed;
    const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

    // 예전에 저장해 둔 토큰이 있는지 확인
    fs.readFile(TOKEN_PATH, (err, token) => {
        if (err) return getAccessToken(oAuth2Client, callback);
        oAuth2Client.setCredentials(JSON.parse(token));
        callback(oAuth2Client);
    });
}

/**
 * 2. 토큰이 없을 경우, 사용자에게 브라우저 로그인을 요청하여 새 토큰을 받습니다.
 */
function getAccessToken(oAuth2Client, callback) {
    const authUrl = oAuth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES,
    });

    console.log('\n======================================================');
    console.log('🔗 아래 링크를 복사해서 인터넷 브라우저 주소창에 붙여넣고 엔터를 치세요:');
    console.log(authUrl);
    console.log('======================================================\n');
    console.log('💡 구글 로그인 후 "계속"을 누르고 나오는 코드를 복사해주세요.');

    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });

    rl.question('=> 복사한 인증 코드를 여기에 붙여넣고 엔터를 누르세요: ', (code) => {
        rl.close();
        oAuth2Client.getToken(code, (err, token) => {
            if (err) return console.error('토큰 발급 중 오류 발생:', err);
            oAuth2Client.setCredentials(token);
            // 나중을 위해 토큰을 파일로 저장
            fs.writeFile(TOKEN_PATH, JSON.stringify(token), (err) => {
                if (err) return console.error(err);
                console.log('✅ 토큰이 성공적으로 저장되었습니다:', TOKEN_PATH);
            });
            callback(oAuth2Client);
        });
    });
}

/**
 * 3. 파일을 구글 드라이브로 업로드합니다.
 */
async function uploadFile(auth) {
    const drive = google.drive({ version: 'v3', auth });

    const testFileName = 'oauth2_test_hello.txt';
    const testFilePath = path.join(__dirname, testFileName);

    // 테스트용 파일 생성
    fs.writeFileSync(testFilePath, 'Hello Google Drive! This file was uploaded using Node.js OAuth 2.0.', 'utf8');

    const fileMetadata = {
        name: testFileName,
        // 필요시 특정 폴더 ID를 지정할 수 있습니다.
        // parents: ['폴더ID_여기에_입력']
    };
    const media = {
        mimeType: 'text/plain',
        body: fs.createReadStream(testFilePath),
    };

    try {
        console.log(`\n[Google Drive] 업로드 시작: ${testFileName}...`);

        const file = await drive.files.create({
            resource: fileMetadata,
            media: media,
            fields: 'id, name, webViewLink',
        });

        console.log('\n🎉 업로드 완료!');
        console.log(`- 파일명: ${file.data.name}`);
        console.log(`- 파일 ID: ${file.data.id}`);
        console.log(`- 확인 링크: ${file.data.webViewLink}`);

    } catch (err) {
        console.error('\n🚨 API 오류 발생:', err.message);
    }
}

// ==========================================
// 메인 실행부
// ==========================================
fs.readFile(CREDENTIALS_PATH, (err, content) => {
    if (err) {
        console.log('🚨 oauth2-credentials.json 파일을 로드할 수 없습니다.');
        return console.log('에러 상세:', err.message);
    }
    // 인증 시작 -> 성공하면 uploadFile 함수 실행
    authorize(JSON.parse(content), uploadFile);
});
