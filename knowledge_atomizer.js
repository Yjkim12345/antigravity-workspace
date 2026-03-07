import fs from 'fs';
import path from 'path';
import { Client } from '@notionhq/client';
import { GoogleGenAI } from '@google/genai';
import os from 'os';

const homeDir = process.env.USERPROFILE || os.homedir();
const configPath1 = path.join(homeDir, '.gemini', 'antigravity', 'mcp_settings.json');
const configPath2 = path.join(homeDir, '.gemini', 'antigravity', 'mcp_config.json');

let configPath = fs.existsSync(configPath1) ? configPath1 : (fs.existsSync(configPath2) ? configPath2 : null);

if (!configPath) {
    console.error(`Config file not found. Checked: \n${configPath1}\n${configPath2}`);
    process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

let NOTION_API_KEY = "";
let GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";

if (config.mcpServers && config.mcpServers["notion-mcp-server"]) {
    GEMINI_API_KEY = config.GEMINI_API_KEY || GEMINI_API_KEY;
    try {
        const headersStr = config.mcpServers["notion-mcp-server"].env.OPENAPI_MCP_HEADERS;
        const headersDict = JSON.parse(headersStr);
        NOTION_API_KEY = headersDict["Authorization"].replace("Bearer ", "");
    } catch (e) {
        console.error("Failed to parse Notion headers:", e);
    }
} else if (config.notionApiKey) {
    NOTION_API_KEY = config.notionApiKey;
    GEMINI_API_KEY = config.geminiApiKey || GEMINI_API_KEY;
}

const NOTION_DB_ID = "31b063a28bb180b1a135ebc3f6813a3c";

const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });
const notion = new Client({ auth: NOTION_API_KEY });

const SYSTEM_PROMPT = `당신은 대한민국의 최고참 파트너 변호사이자 제텔카스텐(Zettelkasten) 지식 아키텍트입니다.

[지시사항]
사용자가 판례나 법리를 제공하면, 이를 분석하여 '독립적으로 재활용 가능한 추상화된 법리'로 정리하십시오.

[원자화 3대 원칙 및 💥제한사항💥]
1. (중요) 과도한 쪼개기(Over-atomization)를 엄격히 금지합니다. 비슷한 맥락이나 같은 판례 안에서 도출되는 연관된 법리들은 억지로 분리하지 말고, 가장 핵심이 되는 1개의 카드로 통합하여 굵직하게 뽑아내십시오.
2. 입력된 텍스트가 A4 반 페이지 이하의 짧은 판결요지나 단일 단락이라면, 무조건 '단 1개의 지식 카드'만 생성하십시오.
3. 사안의 구체적 사실관계와 추상화된 법리를 분리하되, '한줄법리'에는 결론을, '상세내용'에는 그 결론을 뒷받침하는 원문 전체를 풍부하게 담으십시오.
`;

export async function atomizeText(text) {
    console.log(`[*] Analyzing and atomizing text with Gemini (Length: ${text.length} chars)...`);

    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: text,
            config: {
                systemInstruction: SYSTEM_PROMPT,
                responseMimeType: "application/json",
                responseSchema: {
                    type: "object",
                    properties: {
                        cards: {
                            type: "array",
                            description: "입력된 문서에서 추출된 핵심 법리 카드 목록",
                            items: {
                                type: "object",
                                properties: {
                                    title: { type: "string", description: "'~여부', '~요건' 등의 명사형 제목" },
                                    one_line_principle: { type: "string", description: "단 1~3줄의 초응축된 핵심 법칙 (한줄법리)" },
                                    related_laws: { type: "string", description: "관련 법령 (예: '민법 제1008조, 상속세법 제4조')" },
                                    keywords: { type: "string", description: "검색용 핵심 키워드 (예: '#상속회복청구 #가분채권')" },
                                    source: { type: "string", description: "원문 출처 또는 사건번호 (예: '대법원 2025다212863')" },
                                    card_type: { type: "string", description: "지식 유형. 다음 중 하나만 선택: '일반법리', '공격논리', '방어논리', '절차팁', '기재례', '소수설'" },
                                    detailed_text: { type: "string", description: "이 한줄법리를 도출해낸 원본 판결문/문서의 원문 발췌 단락 (상세 내용)" }
                                },
                                required: ["title", "one_line_principle", "related_laws", "keywords", "source", "card_type", "detailed_text"]
                            }
                        }
                    },
                    required: ["cards"]
                },
                temperature: 0.2
            }
        });

        return JSON.parse(response.text);
    } catch (e) {
        console.error("Gemini API Error:", e);
        return { cards: [] };
    }
}

export async function createNotionPage(card) {
    const oneLine = card.one_line_principle.substring(0, 2000);
    const laws = card.related_laws.substring(0, 2000);
    const tags = card.keywords.substring(0, 2000);
    const source = card.source.substring(0, 2000);
    const validTypes = ["일반법리", "공격논리", "방어논리", "절차팁", "기재례", "소수설"];
    const cardType = validTypes.includes(card.card_type) ? card.card_type : "일반법리";

    try {
        const response = await notion.pages.create({
            parent: { database_id: NOTION_DB_ID },
            properties: {
                "이름": { title: [{ text: { content: card.title.substring(0, 2000) } }] },
                "한줄법리": { rich_text: [{ text: { content: oneLine } }] },
                "관련 법령": { rich_text: [{ text: { content: laws } }] },
                "키워드": { rich_text: [{ text: { content: tags } }] },
                "사건번호/출처": { rich_text: [{ text: { content: source } }] },
                "Type": { select: { name: cardType } }
            },
            children: [
                {
                    heading_3: { rich_text: [{ text: { content: "📖 상세 내용 (원문 발췌)" } }] }
                },
                {
                    quote: { rich_text: [{ text: { content: card.detailed_text.substring(0, 2000) } }] }
                },
                { divider: {} },
                {
                    heading_3: { rich_text: [{ text: { content: "🧠 변호사 코멘트 / 실무 적용 메모" } }] }
                }
            ]
        });
        console.log(`[+] Successfully created Notion page: ${card.title}`);
        return response;
    } catch (e) {
        console.error(`[-] Failed to create Notion page. Error: ${e.message}`);
        return null;
    }
}

async function main() {
    const filePath = process.argv[2];
    if (!filePath) {
        console.log("Usage: node knowledge_atomizer.js <path_to_document.txt>");
        return;
    }

    if (!fs.existsSync(filePath)) {
        console.log(`File not found: ${filePath}`);
        return;
    }

    const text = fs.readFileSync(filePath, "utf-8");
    const result = await atomizeText(text);

    console.log(`\n[*] Extracted ${result.cards.length} knowledge cards.`);
    for (let i = 0; i < result.cards.length; i++) {
        const card = result.cards[i];
        console.log(`\n--- Card ${i + 1}: ${card.title} ---`);
        console.log(`Type: ${card.card_type} | Laws: ${card.related_laws}`);
        await createNotionPage(card);
    }
}

import { fileURLToPath } from 'url';
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    main();
}
