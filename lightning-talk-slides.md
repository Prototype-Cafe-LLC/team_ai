---
marp: true
---

# AIエージェントによる開発`半`自動化ワークフロー

## ～マルチエージェント開発システム 一回つくってみて学ぶ～

(LangChain を使って)

@PrototypeCafe / @yukilab222
2025/07

---

## Prototype Cafe とは

- 新潟市中央区 IT系勉強会などに場所貸し出しています
- 県内近郊の勉強会イベントまとめています
- 本業は IoTフルスタックエンジニアリングサービス

---

少なくとも毎日使ってる
Cursor, Claude Code, Gemini, ChatGPT

今日のアイディアはClaude app で要件まとめてみました。

---

## ここ数ヶ月で開発に使いながら解決したかった課題 (1/2)

### ソフトウェア開発の複雑性

- 要件定義からテストまでの一貫性確保が困難
- 各フェーズ間の情報伝達ロス
- 品質保証の属人化
- リアルタイムでの進捗把握の難しさ

### 開発プロセスの常

- 手戻りが多い
- ドキュメントと実装の乖離
- レビューの遅延

---

## 解決したかった課題 (2/2)

### AIモデルの使い分けの必要性

**現状**: モデルごとに得意分野が異なる

- 要件定義: ChatGPT（構造化が得意）
- 計画・実装: Claude（コード生成に強い）
- レビュー: Gemini（多角的な視点）

**課題**: 手動での情報の copy&paste が非効率

---

**目標**: 複数AIを統合し、高速・高品質な開発

---

## 考えたワークフロー

### 4フェーズ + レビューサイクル

```text
要件定義 → 設計 → 実装 → テスト
   ↓        ↓      ↓      ↓
レビュー  レビュー レビュー レビュー
```

- 各フェーズに専門エージェント配置
- メイン + レビューのペア構成（計(仮)8エージェント）
- (仮)最大3回のイテレーション
- いつでも人間が介入可能

---

## インターフェース設計

### リアルタイム監視と制御

#### Web UI

- 進捗の可視化
- エージェントの出力をライブストリーミング
- 一時停止/再開ボタン

#### WebSocket通信

- 双方向リアルタイム通信
- エージェントの思考過程を即座に表示

---

## AI駆動開発で学んだこと①

### テスト駆動の重要性

```python
# 最初にテストを書かせる
def test_hello_world():
    assert create_hello_world() == "Hello, World!"

# その後に実装
def create_hello_world():
    return "Hello, World!"
```

#### なぜ重要か？

- AIの生成コードの品質保証
- 仕様の明確化
- リファクタリング時の安全網

---

## AI駆動開発で学んだこと②

### 柔軟な方向修正の必要性

#### 実装中に起きたこと

- 要件の追加・変更
- 技術スタックの見直し
- アーキテクチャの再検討

#### 対策

- いつでも止められる設計
- 人間のフィードバックループ
- 段階的な承認プロセス

---

## 実装の成果

### 実装した機能

- フルスタックWebアプリケーション
- 8つのAIエージェントの協調動作
- リアルタイム監視システム
- Docker環境での動作

**公開リポジトリ**: [github.com/Prototype-Cafe-LLC/team_ai](https://github.com/Prototype-Cafe-LLC/team_ai)
**調べ物**: [https://deepwiki.com/Prototype-Cafe-LLC/team_ai](https://deepwiki.com/Prototype-Cafe-LLC/team_ai)

---

## デモ: Hello Worldプロジェクト

1. プロジェクト作成
2. 要件定義フェーズ
3. 設計・実装・テスト
4. 自動テスト実行

### 実際の動作をご覧ください

---

## まとめ

### AI駆動開発の可能性

- **課題**: より高品質のコードの生成
- **解決策**: マルチエージェント + エンジニアの協調
- **重要な学び**:
  - テスト駆動アプローチ
  - 柔軟な制御メカニズム
  - リアルタイムフィードバック

---

## 次回イベントのご案内

### AI CRAFT Hacks Niigata #4 x DERTA Gig

**テーマ**: 生成AIどう使ってる？  
**日時**: 2025年7月27日（日）13:00-16:00  
**場所**: WorkWith本町3F（新潟市中央区）

### 見どころ

- Claude Code実践活用術
- 複数AI連携テクニック
- 開発ワークフローの革新
- LT枠・学生枠あり！

詳細・申込: [https://ai-craft-hacks-niigata.connpass.com/event/360142/](https://ai-craft-hacks-niigata.connpass.com/event/360142/)

---

## ご清聴ありがとうございました

**質問・フィードバック大歓迎です！**

GitHub: [github.com/Prototype-Cafe-LLC/team_ai](https://github.com/Prototype-Cafe-LLC/team_ai)  
X/Twitter: [@PrototypeCafe](https://twitter.com/PrototypeCafe)  
Prototype Cafe: [https://www.prototype-cafe.space](https://www.prototype-cafe.space)

---

## 付録: 技術スタック詳解

### バックエンド構成

#### コアテクノロジー

- **Python 3.11** + **FastAPI**: 非同期処理とWebSocket対応
- **LangChain 0.1.4**: エージェントオーケストレーション
- **PostgreSQL 15** + **Redis 7**: データ永続化とリアルタイム状態管理

#### LLM統合

- **Anthropic Claude 3 Sonnet**: 全エージェントで統一
- **OpenAI GPT-4**: 代替オプション対応
- LangChain経由の統一インターフェース

---

## LangChainによるエージェント実装

### なぜLangflowではなくLangChain？

#### 直接的な制御の必要性

- 各エージェントの詳細な挙動制御
- カスタムツールの実装
- ワークフロー間の複雑な連携

#### 特徴

- コードベースでの完全な制御
- 非同期ストリーミング対応
- カスタムツールチェーンの構築

---

## LangChain実装例：要件定義エージェント

```python
class RequirementsAgent:
    def __init__(self):
        self.llm = ChatAnthropic(model="claude-3-sonnet")
        self.tools = [analyze_input, generate_requirements]
        self.memory = ConversationBufferMemory()
        
    async def process(self, user_input: str):
        # プロンプトテンプレート
        prompt = ChatPromptTemplate.from_messages([
            ("system", "要件分析エージェントとして動作"),
            ("human", "{input}")
        ])
        
        # ストリーミング対応
        chain = prompt | self.llm
        async for chunk in chain.astream({"input": user_input}):
            yield chunk.content
```

---

## フロントエンド技術選定

### React + TypeScript + Redux-Saga

#### なぜRedux-Saga？

- WebSocket通信の複雑な制御
- 非同期フローの可視化
- エラーハンドリングの一元化

#### Redux-Sagaの特徴

- Generator関数による読みやすい非同期処理
- テストが書きやすい
- タイムトラベルデバッグ対応

---

## Redux-Sagaによるリアルタイム通信

```typescript
function* watchWebSocket() {
  const channel = yield call(createWebSocketChannel)
  while (true) {
    try {
      const action = yield take(channel)
      yield put(action)
    } catch (error) {
      yield put({ type: 'WS_ERROR', payload: error })
      yield delay(1000)  // 再接続待機
    }
  }
}

function createWebSocketChannel(url: string) {
  return eventChannel(emit => {
    const ws = new WebSocket(url)
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      emit({ type: 'WS_MESSAGE', payload: data })
    }
    
    ws.onerror = (error) => {
      emit(new Error(error.toString()))
    }
    
    return () => ws.close()
  })
}
```

---

## インフラストラクチャ設計

### Docker Composeによる統合環境

```yaml
services:
  backend:
    build: ./backend
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
    
  frontend:
    build: ./frontend
    environment:
      - VITE_API_URL=http://backend:8000
      
  nginx:
    build: ./docker/nginx
    ports: ["80:80", "443:443"]
```

---

## 開発効率を高める工夫

### Makefileによるタスク自動化

```makefile
dev: ## 開発環境起動
    docker-compose up -d
    
test: ## テスト実行
    docker-compose exec backend pytest
    docker-compose exec frontend npm test
    
logs: ## ログ監視
    docker-compose logs -f
    
clean: ## クリーンアップ
    docker-compose down -v
```

### 開発者体験の向上

- ホットリロード対応
- 統一されたログフォーマット
- ワンコマンドでの環境構築

---

## まとめ：技術選定のポイント

### 重視した点

1. **リアルタイム性**: WebSocket + Redis
2. **拡張性**: LangChainの柔軟性
3. **開発効率**: TypeScript + FastAPI
4. **運用性**: Docker + 自動化

### 今後の展望

- 異なるLLMの役割別最適化
- マイクロサービス化
- Kubernetes対応
