import clipboardy from 'clipboardy';
import notifier from 'node-notifier';
import { GlobalKeyboardListener } from 'node-global-key-listener';
import { atomizeText, createNotionPage } from './knowledge_atomizer.js';

let isProcessing = false;

async function runAtomization(text) {
    if (isProcessing) return;
    isProcessing = true;

    try {
        notifier.notify({
            title: "노션 자동업로드 동작 중",
            message: "Gemini AI가 원자화를 진행하고 있습니다...",
            appID: "Antigravity Automation"
        });

        const result = await atomizeText(text);
        const cardCount = result?.cards?.length || 0;

        if (cardCount > 0) {
            for (const card of result.cards) {
                await createNotionPage(card);
            }
        }

        const msg = cardCount > 0 ? `노션 '법리모음'에 ${cardCount}개의 카드가 추가되었습니다.` : "추출된 지식 카드가 없습니다.";

        notifier.notify({
            title: "노션 자동업로드 완료",
            message: msg,
            appID: "Antigravity Automation"
        });
    } catch (e) {
        notifier.notify({
            title: "노션 자동업로드 오류",
            message: `오류가 발생했습니다: ${e.message}`,
            appID: "Antigravity Automation"
        });
        console.error(`Error during atomization: ${e}`);
    } finally {
        isProcessing = false;
    }
}

async function onHotkeyPressed() {
    console.log("단축키 감지! 클립보드 텍스트를 읽어옵니다...");
    try {
        const text = clipboardy.readSync();
        if (!text || text.trim().length < 10) {
            console.log("클립보드에 충분한 텍스트가 없습니다.");
            notifier.notify({
                title: "노션 자동업로드 실패",
                message: "클립보드에 충분한 텍스트가 복사되지 않았습니다.",
                appID: "Antigravity Automation"
            });
            return;
        }

        console.log(`클립보드 텍스트 확인 완료 (길이: ${text.length}자). 백그라운드 처리를 시작합니다.`);
        runAtomization(text).catch(console.error);
    } catch (e) {
        console.log(`클립보드 접근 중 오류 발생: ${e}`);
    }
}

console.log("==========================================================");
console.log(" [안티그래비티 Zero-Click 자동화] 단축키 스크립트 가동 ");
console.log("==========================================================");
console.log("엘박스나 웹 등에서 텍스트를 복사(Ctrl+C)한 후,");
console.log("Ctrl+Alt+N 단축키를 누르면 자동으로 노션에 전송됩니다.");
console.log("종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.");
console.log("==========================================================");

const listener = new GlobalKeyboardListener();

listener.addListener(function (e, down) {
    // Detect Ctrl + Alt + N
    if (e.state === "DOWN" && e.name === "N" && (down["LEFT CTRL"] || down["RIGHT CTRL"]) && (down["LEFT ALT"] || down["RIGHT ALT"])) {
        onHotkeyPressed();
    }
});
