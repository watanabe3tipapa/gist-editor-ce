![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-0.1.0-green.svg)


# gist-editor-ce

CLI + GUI融合型のGist専用マークダウンテキストエディタ。

Typerで構築されたCLIと、FastAPIベースのブラウザGUIを備え、Gistの作成・編集・管理をターミナルとブラウザの両方から行える。

## 主な機能

- **CLIモード**: `$EDITOR`（vim, nano, VS Codeなど）でGistを編集
- **GUIモード**: ブラウザでリアルタイムプレビューしながら編集可能
- **認証**: Personal Access Token（PAT）またはOAuth
- **複数ファイル対応**: 1つのGistに複数のファイルを追加・編集
- **エラーハンドリング**: ユーザーフレンドリーなエラーメッセージ
- **テスト**: 30以上のユニットテスト

## 対応コマンド

| コマンド | 説明 |
|---------|------|
| `auth-login` | PATまたはOAuthで認証 |
| `auth-status` | 認証状態を確認 |
| `auth-logout` | ログアウト |
| `list` | Gist一覧を表示（表形式） |
| `view` | Gistの内容を表示 |
| `create` | 新規Gistを作成 |
| `edit` | 既存Gistを編集（CLI） |
| `add` | Gistにファイルを追加 |
| `delete` | Gistまたはファイルを削除 |
| `fork` | Gistをフォーク |
| `star` | Gistにスターを付ける |
| `unstar` | スターを削除 |
| `serve` | GUIモードでブラウザ編集 |
| `embed` | 埋め込み用スクリプト出力 |
| `files` | Gist内ファイル一覧を表示 |

---

## 導入方法

### 前提条件

- Python 3.10以上
- uv（推奨）またはpip

### 手順

#### 1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/gist-editor-ce.git
cd gist-editor-ce
```

#### 2. 仮想環境を作成（uv使用）

```bash
uv venv .venv
source .venv/bin/activate  # Linux/macOS
# .\.venv\Scripts\activate  # Windows
```

または、pipを使用する場合：

```bash
python -m venv .venv
source .venv/bin/activate
```

#### 3. パッケージをインストール

```bash
uv pip install -e .
# または pip install -e .
```

#### 4. Personal Access Token（PAT）の取得

1. GitHubにログイン
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. `Generate new token (classic)`
4. `gist`スコープにチェック
5. Tokenをコピー

#### 5. 認証

環境変数として設定する方法：

```bash
export GISTMD_PAT="ghp_xxxxxxxxxxxx"
```

または、CLIから対話的に設定：

```bash
gist-editor-ce auth-login
# Personal Access Tokenを入力するよう求められます
```

または、OAuthを使用：

```bash
gist-editor-ce auth-login --oauth
```

---

## 使用方法

### 認証確認

```bash
# PATで認証
gist-editor-ce auth-login --pat ghp_xxxxxxxxxxxx

# OAuthで認証
gist-editor-ce auth-login --oauth

# 認証状態を確認
gist-editor-ce auth-status

# ログアウト
gist-editor-ce auth-logout
```

### Gist一覧表示

```bash
# 自分のGist一覧（表形式）
gist-editor-ce list

# ページ指定
gist-editor-ce list --page 2

# 公開Gist一覧（全員の）
gist-editor-ce list --public

# スター付きGist一覧
gist-editor-ce list --starred
```

### Gistの内容を表示

```bash
# 最初のファイルを表示
gist-editor-ce view <gist-id>

# 特定のファイルを表示
gist-editor-ce view <gist-id> --file filename.md

# 全ファイルを表示
gist-editor-ce view <gist-id> --all
```

### Gist内ファイル一覧

```bash
gist-editor-ce files <gist-id>
```

出力例：
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                         Files in abc123                        ┃
┣━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Filename       ┃ Language   ┃ Size       ┃ Type      ┃
┡━━━━━━━━━━━━━━━┩━━━━━━━━━━━━┩━━━━━━━━━━━┩━━━━━━━━━━━┩
│ test.py        │ Python     │ 15 bytes   │ file      │
│ readme.md      │ Markdown   │ 8 bytes    │ file      │
└────────────────┴────────────┴───────────┴───────────┘
```

### 新規Gistを作成

```bash
# 対話的にエディタが開く
gist-editor-ce create

# 説明文と公開設定を指定
gist-editor-ce create --description "My notes" --public

# ファイル名を指定
gist-editor-ce create --filename "readme.md"

# ローカルファイルを追加
gist-editor-ce create --file ./script.py --file ./config.json
```

### Gistを編集（CLI）

```bash
# エディタが開いて編集できる
gist-editor-ce edit <gist-id>

# 特定のファイルを編集
gist-editor-ce edit <gist-id> --file another.md

# 全ファイルを順次編集
gist-editor-ce edit <gist-id> --all
```

※ `$EDITOR`環境変数でエディタを指定可能：

```bash
export EDITOR="code --wait"   # VS Code
export EDITOR="cursor"       # Cursor
export EDITOR="zed"          # Zed Editor
export EDITOR="nvim"         # Neovim
export EDITOR="nano"         # Nano
```

### Gistにファイルを追加

```bash
# 対話的に内容を入力
gist-editor-ce add <gist-id> --filename "new_file.md"

# 内容を直接指定
gist-editor-ce add <gist-id> --filename "script.py" --content "print('hello')"

# ファイルから読み込み
gist-editor-ce add <gist-id> --filename "readme.md" --from-file ./readme.md
```

### Gistを編集（GUIブラウザ）

```bash
# ブラウザで編集GUIが起動
gist-editor-ce serve <gist-id>

# ポートを指定
gist-editor-ce serve <gist-id> --port 8080
```

GUIモードでは：
- 左側: Markdownエディタ + リアルタイムプレビュー
- 右側: gist.github.comのiframe表示（編集内容をリアルタイム確認）

### Gistを削除

```bash
# Gist全体を削除（確認あり）
gist-editor-ce delete <gist-id>

# 確認なしで削除
gist-editor-ce delete <gist-id> --force

# 特定のファイルのみ削除
gist-editor-ce delete <gist-id> --file old.md
```

### Gistをフォーク

```bash
gist-editor-ce fork <gist-id>
```

### スター機能

```bash
# スターを付ける
gist-editor-ce star <gist-id>

# スターを削除
gist-editor-ce unstar <gist-id>
```

### 埋め込み用スクリプト生成

```bash
# 埋め込み用<script>タグを出力
gist-editor-ce embed <gist-id>

# 特定のファイルを指定
gist-editor-ce embed <gist-id> --file script.js

# Raw URLを出力
gist-editor-ce embed <gist-id> --raw
```

---

## 設定ファイル

設定は `~/.config/gist-editor-ce/config.toml` に保存される。

手動で設定する場合：

```toml
token = "ghp_xxxxxxxxxxxx"
default_public = false
editor = "nano"
server_port = 0  # 0 = 自動選択
auth_method = "pat"  # "pat" または "oauth"
```

**セキュリティ注意**: `config.toml`のパーミッションは自動的に`600`に設定される。PATは絶対に共有しない。

---

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `GISTMD_PAT` | GitHub Personal Access Token |
| `EDITOR` | CLI編集で使用するエディタ（デフォルト: nano） |
| `XDG_CONFIG_HOME` | 設定ファイルのディレクトリ |

---

## テスト

```bash
# 全テストを実行
uv run python -m pytest tests/ -v

# カバレッジ付き
uv run python -m pytest tests/ --cov=gist_editor_ce --cov-report=term-missing
```

---

## トラブルシューティング

### `ModuleNotFoundError`エラー

```bash
uv pip install -e .
```

###認証エラー（401/403）

- PATが正しいか確認
- `gist`スコープがあるか確認
- Tokenが有効か確認
- `gist-editor-ce auth-status`で状態確認

### エディタが開かない

```bash
export EDITOR=nano
```

### ブラウザが開かない

GUI起動時にエラーが出る場合は、URLを直接ブラウザに入力：

```
http://127.0.0.1:XXXX/edit/<gist-id>
```

### Rate Limitエラー

GitHub APIのレート制限に達しました。数分待ってから再試行してください。

---

## アンインストール

```bash
pip uninstall gist-editor-ce
rm -rf ~/.config/gist-editor-ce
```

---

## License

MIT License
