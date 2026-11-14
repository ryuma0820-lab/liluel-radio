# Liluel Morning Radio 🎙️

東京ディズニーリゾート・ツイステ専門の毎朝ラジオです。AI音声キャスター「リルエル」が読み上げます。

**このZIPは、[monoradio102/myradio](https://github.com/monoradio102/myradio) の上に重ねる「追加・置換ファイル集」です。これだけではWebラジオのプレーヤーは入っていません。**

- プレーヤー・アニメーション・公開ツール：元テンプレートを利用（MIT）
- 毎朝のニュースWeb検索・出典確認：OpenAI Responses APIのweb_search
- 原稿JSONの作成：OpenAI API
- 読み上げ：ElevenLabs（設定した Voice ID）
- 再生時の口パク：元テンプレートのWeb Audio機能
- 公開：GitHub Actions + GitHub Pages

## 1. 局を作る（Windowsの操作）

1. https://github.com/monoradio102/myradio を開いて **Use this template → Create a new repository**。
2. リポジトリ名は例として `liluel-radio`。GitHub Pagesを簡単に公開するなら `Public` を選択。
3. GitHub Desktopで作ったリポジトリを `Clone` する（または `git clone`）。
4. このZIPを展開し、中身を**フォルダー構造ごと**新リポジトリの直下にコピーして、上書きしてください。隠しフォルダー `.github` を忘れずに。
5. テンプレートに残っている `episodes/` 内のサンプル放送JSONは全部消してください（`episodes/`フォルダー自体は残しても大丈夫）。`episodes.json` はこのZIPの `[]` に置換されます。
6. `character/` はひとまず元テンプレートの仮キャラを残します。専用リルエル画像と差分は後日置換します。
7. GitHub Desktopから変更を **Commit → Push** します。

## 2. 外部APIを設定する（秘密鍵を公開しない）

GitHubのリポジトリを開く → **Settings → Secrets and variables → Actions**。

**Repository secrets**（暗号化して保管）:

| 名前 | 値 |
|---|---|
| `OPENAI_API_KEY` | OpenAI Platformで発行したAPIキー |
| `ELEVENLABS_API_KEY` | ElevenLabsで発行したAPIキー |

**Repository variables**（秘密でない設定）:

| 名前 | 値 |
|---|---|
| `ELEVENLABS_VOICE_ID` | ElevenLabsで選んだ声のVoice ID |
| `OPENAI_MODEL` | 任意。既定 `gpt-5.4-mini` |

**注意**：ChatGPT Plus料金とOpenAI API料金は別です。ElevenLabsの利用量にも上限や料金がある場合があります。キーをコードやチャット、READMEに書き込まないでください。

## 3. 初回放送を実行

1. リポジトリの **Settings → Actions → General** でワークフロー実行権限を確認。必要ならWorkflow permissionsをRead and write permissionsに設定。
2. **Actions → Liluel Daily Radio → Run workflow** を押します。
3. 実行に成功すると `gh-pages` というブランチに公開用ファイルが作成されます。
4. **Settings → Pages → Build and deployment** を `Deploy from a branch` にし、`gh-pages` と `/(root)` を選択。
5. 表示先：`https://<GitHubユーザー名>.github.io/<リポジトリ名>/`

### 毎朝の予定

GitHub Actionsのスケジュールを **07:27（日本時間）** に設定しています。音声生成と公開処理が順調なら **8:00までの配信を目標**にしていますが、GitHub Actionsの開始が遅延することがあります。時刻保証ではありません。手動実行も可能です。

## 4. 放送内容と品質管理

理想の構成は**公式・一次情報3件＋Xの確認可能な話題2件**。Xの投稿がWeb検索で確認できない場合は、無理にXの人気投稿を捏造せず、確認できる公式・報道ソースで置き換えます。

ニュースは原則 **直近72時間** に絞り、音声前にWeb検索引用元URLに存在するものをチェックします。有効なニュースが3件未満の場合は、**新しい放送を作らず処理を失敗**させ、前回の公開を維持します。ただし、URLの存在チェックだけで記事本文の完全な事実検証ができるわけではありません。重要情報は出典を確認してください。

放送は公開URLで誰でも聴ける可能性があるため、**個人名・プライベート情報は原稿に含めない**設計にしています。ニュースの画像は無断保存せず、原則出典リンクを載せます。

## 5. リルエルのキャラクター素材

元テンプレートの `character/character.json` は、透明背景の `base.png` と、口の半開き・開き、目の半目・閉じ差分を使用します。このZIPには専用キャラクターの画像はまだ含まれていません。画像を用意できたら、既存テンプレートの `docs/formats.md` の座標形式に合わせて `character/` を丸ごと置換してください。

キャスターの設定イメージ：成人男性の可愛らしい小悪魔系。甘く透明感のある少年声。表情・衣装・髪色の最終確認後に専用絵へ差し替える予定です。

## 6. 開発者向け

```powershell
python -m pip install -r requirements-radio.txt
python tools/liluel_daily.py --check
python -m unittest discover -s tests -v
```

音声の合成にはPC上に `ffmpeg` も必要です（GitHub ActionsのUbuntu runnerには通常同梱）。ローカル本番実行では環境変数にAPIキーとVoice IDを設定してください。

主なファイル：
- `.github/workflows/liluel-radio.yml`：毎朝のスケジュール・公開
- `tools/liluel_daily.py`：Web検索・原稿・音声・字幕・インデックス
- `station.json`：番組設定
- `logo.svg`：新局のロゴ

## ライセンス・クレジット

本追加コードはMIT License（`LICENSE-LILUEL`）で提供。元のプレーヤー・`tools/publish.sh` 等は monoradio102 氏のMIT Licenseを維持してください。音声・キャラクター素材の利用条件は、それぞれの提供元の規約に従ってください。

GitHub原案：https://github.com/monoradio102/myradio
