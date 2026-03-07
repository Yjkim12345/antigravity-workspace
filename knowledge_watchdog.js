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
        console.log(`[*] Created watch directory: ${WATCH_DIR}`);
    }
    if (!fs.existsSync(ARCHIVE_DIR)) {
        fs.mkdirSync(ARCHIVE_DIR, { recursive: true });
        console.log(`[*] Created archive directory: ${ARCHIVE_DIR}`);
    }
}

async function processFile(filepath) {
    const filename = path.basename(filepath);

    if (!(filename.toLowerCase().endsWith('.txt') || filename.toLowerCase().endsWith('.md'))) {
        return;
    }

    console.log(`\n[+] 새 파일 감지됨: ${filename}`);

    // Give it a short sleep to ensure file writing is done
    await new Promise(resolve => setTimeout(resolve, 1500));

    try {
        const text = fs.readFileSync(filepath, 'utf8');
        if (!text.trim()) {
            console.log("빈 파일입니다. 무시합니다.");
            return;
        }

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
        console.log(msg);

        notifier.notify({
            title: "노션 일괄 업로드 완료",
            message: msg,
            appID: "Antigravity Watchdog"
        });

        const newFilename = `${Math.floor(Date.now() / 1000)}_${filename}`;
        const newFilePath = path.join(ARCHIVE_DIR, newFilename);
        fs.renameSync(filepath, newFilePath);
        console.log(`[*] 처리 완료된 파일을 보관함으로 이동했습니다: ${newFilename}`);

    } catch (e) {
        console.error(`오류 발생: ${e.message}`);
        notifier.notify({
            title: "업로드 오류",
            message: `오류 발생: ${e.message}`,
            appID: "Antigravity Watchdog"
        });
    }
}

setupDirectories();

console.log("==========================================================");
console.log(" [안티그래비티 Zero-Click] 폴더 감시 봇 가동 ");
console.log("==========================================================");
console.log(`감시 폴더: ${WATCH_DIR}`);
console.log(`위 폴더에 .txt 나 .md 파일을 넣으면 자동으로 노션 DB로 전송됩니다.`);
console.log("종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.");
console.log("==========================================================");

const watcher = chokidar.watch(WATCH_DIR, {
    ignored: /(^|[\/\\])\../,
    persistent: true,
    depth: 0,
    ignoreInitial: true,
    awaitWriteFinish: {
        stabilityThreshold: 1000,
        pollInterval: 100
    }
});

watcher.on('add', (filepath) => {
    processFile(filepath).catch(e => console.error("Unhandled error processing file:", e));
});

process.on('SIGINT', () => {
    watcher.close().then(() => {
        console.log("폴더 감시 봇을 종료합니다.");
        process.exit(0);
    });
});
