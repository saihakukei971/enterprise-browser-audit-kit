@echo off
echo ====================================================
echo    ブラウザ情報収集ツール 実行開始
echo    情報システム部
echo ====================================================
echo.

echo [処理開始] ブラウザ情報を収集しています...
"%~dp0collect_browser_info.exe"
if %ERRORLEVEL% NEQ 0 (
    echo [エラー] ブラウザ情報の収集に失敗しました。
    echo 情報システム部までご連絡ください。
    pause
    exit /b 1
)
echo [処理完了] ブラウザ情報を収集しました。
echo.

echo [処理開始] カメラを起動します...
echo 本人確認のため、顔写真を撮影します。
echo カメラを正面に向け、3秒後に撮影します。
timeout /t 1 /nobreak > nul
echo 3...
timeout /t 1 /nobreak > nul
echo 2...
timeout /t 1 /nobreak > nul
echo 1...
"%~dp0capture_face_photo.exe"
if %ERRORLEVEL% NEQ 0 (
    echo [エラー] 顔写真の撮影に失敗しました。
    echo カメラが接続されていることを確認し、再実行してください。
    echo 問題が解決しない場合は、情報システム部までご連絡ください。
    pause
    exit /b 1
)
echo [処理完了] 顔写真を撮影しました。
echo.

echo ====================================================
echo    全ての処理が完了しました。
echo    ご協力ありがとうございました。
echo    このウィンドウを閉じてください。
echo ====================================================
timeout /t 5 /nobreak > nul
exit /b 0