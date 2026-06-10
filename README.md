# Knowledge RAG 鈥?浼佷笟绾ф櫤鑳界煡璇嗗簱绯荤粺

鍩轰簬 **FastAPI + Vue 3 + DeepSeek API + ChromaDB** 鐨勫叏鏍?RAG (妫€绱㈠寮虹敓鎴? 鐭ヨ瘑搴撳钩鍙般€傛敮鎸佹枃妗ｄ笂浼犱笌鑷姩瑙ｆ瀽銆佷袱绫诲垎绫荤鐞嗐€佹爣绛句綋绯汇€佹潵婧愬紩鐢ㄤ笌缃俊搴﹁瘎浼扮殑鏅鸿兘闂瓟锛屼互鍙婄煭鏈?闀挎湡鍙岃蹇嗘満鍒躲€?
## 鍔熻兘姒傝

| 妯″潡 | 鍔熻兘 |
|---|---|
| 鐭ヨ瘑搴撶鐞?| 鍒涘缓銆佺紪杈戙€佸垹闄ょ煡璇嗗簱锛涘叕寮€ / 绉佹湁鍙鎬ф帶鍒?|
| 鍒嗙被绠＄悊 | 涓ょ骇鍒嗙被鏍戯紝鏀寔鏂板缓銆佺紪杈戙€佸垹闄ゅ瓙鍒嗙被 |
| 鏂囨。绠￠亾 | 涓婁紶 PDF / DOCX / TXT / MD / 鍥剧墖锛涜嚜鍔ㄨВ鏋愩€佸垎鍧椼€佸悜閲忓寲 |
| 鏍囩绯荤粺 | 鑷敱鏍囩锛屾敮鎸佸瀵瑰鏂囨。鍏宠仈鍜屼氦鍙夌瓫閫?|
| 鏅鸿兘闂瓟 | 鍩轰簬鐭ヨ瘑搴撶殑 RAG 闂瓟锛岄檮甯︽潵婧愬紩鐢ㄥ拰缃俊搴﹁瘎浼?|
| 鐭湡璁板繂 | 浼氳瘽绐楀彛鍐呯殑涓婁笅鏂囧璇濊蹇嗭紙鍙厤缃疆鏁帮級 |
| 闀挎湡璁板繂 | 瀵硅瘽鍘嗗彶鎸佷箙鍖栧瓨鍌紝鏀寔 Markdown 瀵煎嚭 |
| 鐢ㄦ埛鍋忓ソ | 鍙厤缃殑璁板繂绐楀彛銆侀粯璁ょ煡璇嗗簱绛夊亸濂借缃?|
| 鏉冮檺鎺у埗 | 澶氱敤鎴枫€丄dmin / User 瑙掕壊銆佺煡璇嗗簱鍙鎬ч殧绂?|

## 绯荤粺鏋舵瀯

```mermaid
flowchart LR
    subgraph Frontend["鍓嶇 (Vue 3 + Vite + Element Plus)"]
        UI[Web 鐣岄潰]
    end

    subgraph Backend["鍚庣 (FastAPI)"]
        Auth[JWT 璁よ瘉]
        API[REST API]
        DocSvc[鏂囨。鏈嶅姟]
        QASvc[闂瓟鏈嶅姟]
        MemSvc[璁板繂鏈嶅姟]
    end

    subgraph Storage[瀛樺偍灞俔
        SQLite[(SQLite 鍏崇郴鏁版嵁搴?]
        Chroma[(ChromaDB 鍚戦噺鏁版嵁搴?]
        Files[鏂囦欢瀛樺偍]
    end

    subgraph External[澶栭儴鏈嶅姟]
        DeepSeek[DeepSeek API]
    end

    UI --> Auth
    Auth --> API
    API --> DocSvc
    API --> QASvc
    API --> MemSvc
    DocSvc --> Files
    DocSvc --> Chroma
    DocSvc --> DeepSeek
    QASvc --> Chroma
    QASvc --> DeepSeek
    QASvc --> MemSvc
    MemSvc --> SQLite
    API --> SQLite
```

## 鎶€鏈爤

| 灞傜骇 | 鎶€鏈€夊瀷 |
|---|---|
| 鍚庣妗嗘灦 | FastAPI + Uvicorn |
| 鍓嶇妗嗘灦 | Vue 3 + TypeScript + Vite |
| UI 缁勪欢搴?| Element Plus + Pinia 鐘舵€佺鐞?|
| 澶фā鍨?| DeepSeek API (chat + embedding) |
| 鍚戦噺鏁版嵁搴?| ChromaDB (宓屽叆寮忔ā寮忥紝闆堕厤缃儴缃? |
| 鍏崇郴鏁版嵁搴?| SQLite (鍙€氳繃 DATABASE_URL 涓€閿垏鎹?PostgreSQL) |
| 璁よ瘉 | JWT (python-jose + bcrypt) |
| 鏂囨。瑙ｆ瀽 | pdfplumber / python-docx / pytesseract (OCR) |

## 蹇€熷紑濮?
### 鐜瑕佹眰

- Python 3.11+
- Node.js 18+
- DeepSeek API Key (鍙€?鈥?鏃?API Key 鏃剁郴缁熻嚜鍔ㄥ垏鎹负鍏抽敭璇嶆绱㈡ā寮?

### 1. 鍏嬮殕椤圭洰

```bash
git clone https://github.com/Zcj04/knowledge-rag.git
cd knowledge-rag
```

### 2. 鍚庣閰嶇疆

```bash
# 鍒涘缓铏氭嫙鐜
python -m venv .venv

# 婵€娲昏櫄鎷熺幆澧?(Windows)
.venv\Scripts\activate
# 婵€娲昏櫄鎷熺幆澧?(macOS / Linux)
source .venv/bin/activate

# 瀹夎渚濊禆
pip install -r backend/requirements.txt

# 閰嶇疆鐜鍙橀噺
cp .env.example .env
# 缂栬緫 .env锛屽～鍐?DEEPSEEK_API_KEY锛堝彲閫夛紝寮€鍙戞ā寮忎笅涓嶅～涔熻兘鐢級
```

### 3. 鍓嶇閰嶇疆

```bash
cd frontend
npm install
cd ..
```

### 4. 鍚姩

```bash
# 缁堢 1 鈥?鍚姩鍚庣 (绔彛 8000)
cd backend
uvicorn app.main:app --reload --port 8000

# 缁堢 2 鈥?鍚姩鍓嶇 (绔彛 5173)
cd frontend
npm run dev
```

### 5. 浣跨敤

鎵撳紑娴忚鍣ㄨ闂?**http://localhost:5173** 鈫?娉ㄥ唽璐﹀彿 鈫?鍒涘缓鐭ヨ瘑搴?鈫?涓婁紶鏂囨。 鈫?寮€濮嬫彁闂€?
## 椤圭洰缁撴瀯

```
knowledge-rag/
鈹溾攢鈹€ backend/
鈹?  鈹溾攢鈹€ app/
鈹?  鈹?  鈹溾攢鈹€ main.py                  # FastAPI 鍏ュ彛锛孋ORS锛岃矾鐢辨敞鍐?鈹?  鈹?  鈹溾攢鈹€ config.py                # 鐜鍙橀噺涓庨厤缃鐞?鈹?  鈹?  鈹溾攢鈹€ database.py              # SQLAlchemy 寮曟搸涓庝細璇?鈹?  鈹?  鈹溾攢鈹€ api/                     # 璺敱妯″潡
鈹?  鈹?  鈹?  鈹溾攢鈹€ auth.py              # 娉ㄥ唽銆佺櫥褰曘€佸綋鍓嶇敤鎴?鈹?  鈹?  鈹?  鈹溾攢鈹€ kb.py                # 鐭ヨ瘑搴?CRUD + 鍒嗙被绠＄悊
鈹?  鈹?  鈹?  鈹溾攢鈹€ document.py          # 鏂囨。涓婁紶銆佸垪琛ㄣ€佸垹闄ゃ€佹爣绛俱€佸垎绫?鈹?  鈹?  鈹?  鈹斺攢鈹€ qa.py                # 鏅鸿兘闂瓟銆佸璇濈鐞?鈹?  鈹?  鈹溾攢鈹€ core/
鈹?  鈹?  鈹?  鈹溾攢鈹€ security.py          # JWT 鐢熸垚/鏍￠獙銆佸瘑鐮佸搱甯?鈹?  鈹?  鈹?  鈹斺攢鈹€ deps.py              # 渚濊禆娉ㄥ叆 (褰撳墠鐢ㄦ埛銆佺鐞嗗憳瀹堝崼)
鈹?  鈹?  鈹溾攢鈹€ models/                  # SQLAlchemy ORM 妯″瀷
鈹?  鈹?  鈹?  鈹溾攢鈹€ user.py              # 鐢ㄦ埛
鈹?  鈹?  鈹?  鈹溾攢鈹€ knowledge_base.py    # 鐭ヨ瘑搴?鈹?  鈹?  鈹?  鈹溾攢鈹€ document.py          # 鏂囨。銆佹爣绛惧叧鑱?鈹?  鈹?  鈹?  鈹斺攢鈹€ conversation.py      # 浼氳瘽銆佹秷鎭?鈹?  鈹?  鈹溾攢鈹€ schemas/                 # Pydantic 璇锋眰/鍝嶅簲妯″瀷
鈹?  鈹?  鈹斺攢鈹€ services/               # 涓氬姟閫昏緫灞?鈹?  鈹?      鈹溾攢鈹€ auth_service.py      # 璁よ瘉鏈嶅姟
鈹?  鈹?      鈹溾攢鈹€ kb_service.py        # 鐭ヨ瘑搴撴湇鍔?鈹?  鈹?      鈹溾攢鈹€ document_service.py  # 鏂囨。瑙ｆ瀽銆佸垎鍧椼€佸悜閲忓寲銆佸叧閿瘝妫€绱?鈹?  鈹?      鈹溾攢鈹€ qa_service.py        # 妫€绱€佺敓鎴愩€佸紩鐢ㄧ粍瑁?鈹?  鈹?      鈹斺攢鈹€ memory_service.py    # 鐭湡/闀挎湡璁板繂绠＄悊
鈹?  鈹溾攢鈹€ uploads/                     # 涓婁紶鏂囦欢瀛樺偍
鈹?  鈹溾攢鈹€ chroma_data/                 # ChromaDB 鍚戦噺鎸佷箙鍖?鈹?  鈹斺攢鈹€ requirements.txt
鈹溾攢鈹€ frontend/
鈹?  鈹溾攢鈹€ src/
鈹?  鈹?  鈹溾攢鈹€ views/
鈹?  鈹?  鈹?  鈹溾攢鈹€ LoginView.vue             # 鐧诲綍/娉ㄥ唽椤?鈹?  鈹?  鈹?  鈹溾攢鈹€ DashboardView.vue         # 鐭ヨ瘑搴撳垪琛?(鍗＄墖缃戞牸)
鈹?  鈹?  鈹?  鈹溾攢鈹€ KnowledgeBaseView.vue     # 鐭ヨ瘑搴撹鎯?(鏂囨。銆佸垎绫汇€佷笂浼?
鈹?  鈹?  鈹?  鈹溾攢鈹€ QAChatView.vue            # 闂瓟瀵硅瘽椤?(鍚紩鐢ㄩ潰鏉?
鈹?  鈹?  鈹?  鈹斺攢鈹€ HistoryView.vue           # 瀵硅瘽鍘嗗彶
鈹?  鈹?  鈹溾攢鈹€ components/
鈹?  鈹?  鈹?  鈹斺攢鈹€ layout/AppLayout.vue      # 渚ц竟鏍?+ 涓诲竷灞€
鈹?  鈹?  鈹溾攢鈹€ stores/                       # Pinia 鐘舵€佺鐞?鈹?  鈹?  鈹?  鈹溾攢鈹€ auth.ts                   # 璁よ瘉鐘舵€?鈹?  鈹?  鈹?  鈹溾攢鈹€ kb.ts                     # 鐭ヨ瘑搴撶姸鎬?鈹?  鈹?  鈹?  鈹斺攢鈹€ chat.ts                   # 瀵硅瘽鐘舵€?鈹?  鈹?  鈹溾攢鈹€ api/client.ts                 # Axios 灏佽 (JWT 鎷︽埅鍣?
鈹?  鈹?  鈹斺攢鈹€ router/index.ts              # Vue Router 璺敱閰嶇疆
鈹?  鈹溾攢鈹€ package.json
鈹?  鈹斺攢鈹€ vite.config.ts
鈹溾攢鈹€ .env.example
鈹溾攢鈹€ .gitignore
鈹斺攢鈹€ README.md
```

## API 姒傝

| 鏂规硶 | 璺緞 | 璇存槑 |
|---|---|---|
| POST | `/api/auth/register` | 娉ㄥ唽鏂扮敤鎴?|
| POST | `/api/auth/login` | 鐧诲綍锛岃繑鍥?JWT Token |
| GET | `/api/auth/me` | 鑾峰彇褰撳墠鐢ㄦ埛淇℃伅 |
| GET | `/api/kb` | 鑾峰彇鐭ヨ瘑搴撳垪琛?|
| POST | `/api/kb` | 鍒涘缓鐭ヨ瘑搴?|
| GET | `/api/kb/{id}` | 鑾峰彇鐭ヨ瘑搴撹鎯?(鍚垎绫绘爲) |
| PUT | `/api/kb/{id}` | 鏇存柊鐭ヨ瘑搴?|
| DELETE | `/api/kb/{id}` | 鍒犻櫎鐭ヨ瘑搴?|
| GET | `/api/kb/{id}/categories` | 鑾峰彇鍒嗙被鍒楄〃 (鏍戝舰) |
| POST | `/api/kb/{id}/categories` | 鍒涘缓鍒嗙被 |
| POST | `/api/kb/{id}/documents/upload` | 涓婁紶鏂囨。 |
| GET | `/api/kb/{id}/documents` | 鏂囨。鍒楄〃 (鏀寔绛涢€? |
| PUT | `/api/kb/{id}/documents/{did}/category` | 鏇存柊鏂囨。鍒嗙被 |
| PUT | `/api/kb/{id}/documents/{did}/tags` | 鏇存柊鏂囨。鏍囩 |
| POST | `/api/qa/ask` | 鎻愰棶 (RAG 闂瓟) |
| GET | `/api/qa/conversations` | 鑾峰彇瀵硅瘽鍘嗗彶鍒楄〃 |
| GET | `/api/qa/conversations/{id}` | 鑾峰彇瀵硅瘽娑堟伅 |
| DELETE | `/api/qa/conversations/{id}` | 鍒犻櫎瀵硅瘽 |
| GET | `/api/qa/conversations/{id}/export` | 瀵煎嚭瀵硅瘽涓?Markdown |

## 璁捐瑕佺偣

- **ChromaDB 宓屽叆寮忔ā寮?*锛氶浂閰嶇疆鍚戦噺瀛樺偍锛屾棤闇€鍗曠嫭閮ㄧ讲鍚戦噺鏁版嵁搴撴湇鍔★紝鏁版嵁鐩存帴鎸佷箙鍖栧埌 `backend/chroma_data/`銆?- **鍏抽敭璇嶆绱㈤檷绾?*锛氭湭閰嶇疆 DeepSeek API Key 鏃讹紝绯荤粺鑷姩鍒囨崲涓?CJK 浜屽厓缁?+ 鍗曡瘝閲嶅彔鐨勫叧閿瘝妫€绱㈡柟妗堬紝纭繚寮€鍙戞ā寮忎笅闂瓟鍔熻兘浠嶇劧鍙敤銆?- **纭畾鎬у搱甯屽悜閲?*锛堥檷绾ф柟妗堬級锛氭棤 Embedding API 鏃讹紝瀵规枃鏈潡杩涜 SHA-256 鍝堝笇鐢熸垚纭畾鎬у悜閲忥紝涓嶄緷璧栧閮ㄦ湇鍔″嵆鍙畬鎴愬熀鏈绱€?- **璺緞鑴辩 CWD**锛氭暟鎹簱銆丆hromaDB 鍜屼笂浼犵洰褰曠殑璺緞鍧囦互 `config.py` 鎵€鍦ㄤ綅缃В鏋愶紝涓嶅彈 `uvicorn` 鍚姩鐩綍褰卞搷銆?- **SQLite 榛樿锛孭ostgreSQL 鍙垏鎹?*锛氫慨鏀?`DATABASE_URL` 鍗冲彲鍒囨崲鑷充换浣?SQLAlchemy 鏀寔鐨勬暟鎹簱锛岃〃缁撴瀯瀹屽叏鐢?ORM 瀹氫箟锛屾棤鎵嬪啓 SQL銆?
## 鐜鍙橀噺

| 鍙橀噺 | 蹇呭～ | 榛樿鍊?| 璇存槑 |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | 鍚?| (绌? | DeepSeek API 瀵嗛挜锛岀敤浜?LLM 瀵硅瘽鍜屽悜閲忓祵鍏?|
| `SECRET_KEY` | 鍚?| `change-me-...` | JWT 绛惧悕瀵嗛挜 (鐢熶骇鐜鍔″繀淇敼) |
| `DATABASE_URL` | 鍚?| `sqlite:///./knowledge_rag.db` | 鏁版嵁搴撹繛鎺ュ瓧绗︿覆 |
| `CORS_ORIGINS` | 鍚?| `["http://localhost:5173"]` | 鍏佽鐨勮法鍩熸潵婧?|
| `CHUNK_SIZE` | 鍚?| `512` | 鏂囨。鍒嗗潡澶у皬 |
| `RETRIEVAL_TOP_K` | 鍚?| `5` | 姣忔妫€绱㈣繑鍥炵殑鐗囨鏁伴噺 |

## 寮€婧愬崗璁?
MIT
