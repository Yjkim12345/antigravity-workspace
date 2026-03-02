const { google } = require('googleapis');
const path = require('path');

const KEYFILEPATH = path.join(__dirname, 'drive-credentials.json');
const SCOPES = ['https://www.googleapis.com/auth/drive.readonly'];

async function checkDriveAccess() {
    try {
        const auth = new google.auth.GoogleAuth({
            keyFile: KEYFILEPATH,
            scopes: SCOPES,
        });

        const driveService = google.drive({ version: 'v3', auth });

        console.log('[Google Drive] 접근 가능한 파일 및 폴더 목록 조회 중...');

        const response = await driveService.files.list({
            pageSize: 10,
            fields: 'nextPageToken, files(id, name, mimeType, parents)',
            q: "trashed=false"
        });

        const files = response.data.files;
        if (files.length === 0) {
            console.log('🚨 이 서비스 계정이 접근할 수 있는 파일이나 폴더가 없습니다.');
            console.log('구글 드라이브에서 공유 폴더를 만들고 서비스 계정 이메일을 "편집자"로 추가했는지 확인해 주세요.');
        } else {
            console.log('✅ 접근 가능한 파일/폴더 목록:');
            files.map((file) => {
                const parents = file.parents ? `(부모 폴더 ID: ${file.parents.join(', ')})` : '';
                console.log(`- ${file.name} (${file.id}) ${parents}`);
            });
        }

        console.log('\n[참고] 서비스 계정 이메일 주소는 credentials.json의 client_email 값입니다.');
    } catch (error) {
        console.error('[Google Drive]조회 중 에러 발생:', error.message);
    }
}

checkDriveAccess();
