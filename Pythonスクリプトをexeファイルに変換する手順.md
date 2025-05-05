# Pythonスクリプトをexeファイルに変換する手順

## 必要なもの
- Python 3.6以上がインストールされた環境
- pip（Pythonのパッケージマネージャ）

## 手順

### 1. 必要なパッケージのインストール

管理者権限でコマンドプロンプトを開き、以下のコマンドを実行します：

```bash
pip install pyinstaller
pip install opencv-python
pip install requests
```

### 2. ビルドスクリプトの作成

ビルド用のバッチファイル `build_exes.bat` を作成します：

```batch
@echo off
echo === ブラウザ情報収集ツールのビルド開始 ===

echo 1. collect_browser_info.exeをビルド中...
pyinstaller --noconfirm --onefile --windowed --icon=browser_icon.ico --name="collect_browser_info" collect_browser_info.py

echo 2. capture_face_photo.exeをビルド中...
pyinstaller --noconfirm --onefile --windowed --icon=camera_icon.ico --name="capture_face_photo" capture_face_photo.py

echo === ビルド完了 ===
echo 実行ファイルは dist フォルダ内に作成されました。

pause
```

### 3. アイコンの用意（任意）

`browser_icon.ico`と`camera_icon.ico`を用意してください。アイコンが不要な場合は、ビルドスクリプトから`--icon=xxx.ico`のオプションを削除してください。

### 4. ビルドの実行

1. 以下のファイルを同じフォルダに配置します:
   - collect_browser_info.py
   - capture_face_photo.py
   - build_exes.bat
   - browser_icon.ico (任意)
   - camera_icon.ico (任意)

2. `build_exes.bat`をダブルクリックして実行します。

3. ビルドが完了すると、`dist`フォルダ内に以下のファイルが作成されます：
   - collect_browser_info.exe
   - capture_face_photo.exe

### 5. 配布用パッケージの作成

1. 新しいフォルダ「BrowserLogCollector_v1.0」を作成します。

2. 以下のファイルをこのフォルダにコピーします：
   - dist/collect_browser_info.exe
   - dist/capture_face_photo.exe
   - run_all_tasks.bat (別途作成)
   - README_使い方.txt (別途作成)

3. フォルダをZIP形式で圧縮して配布します。

### トラブルシューティング

- ビルド中にエラーが発生した場合は、必要なライブラリがすべてインストールされているか確認してください。
- 特定のライブラリがEXEに含まれない場合は、以下のようにhidden importを指定します：
  ```
  pyinstaller --hidden-import=xxx --onefile collect_browser_info.py
  ```
- OpenCVを使用する場合は、以下のhidden importを追加すると良いことがあります：
  ```
  --hidden-import=cv2.cv2
  ```

### 作成されたEXEのテスト方法

1. 別のコンピュータでEXEファイルをテストして、すべての依存関係が正しく含まれていることを確認します。
2. テスト中にエラーが発生した場合は、適切なhidden importを追加してから再ビルドします。