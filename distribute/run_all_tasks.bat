@echo off
echo ====================================================
echo    �u���E�U�����W�c�[�� ���s�J�n
echo    ���V�X�e����
echo ====================================================
echo.

echo [�����J�n] �u���E�U�������W���Ă��܂�...
"%~dp0collect_browser_info.exe"
if %ERRORLEVEL% NEQ 0 (
    echo [�G���[] �u���E�U���̎��W�Ɏ��s���܂����B
    echo ���V�X�e�����܂ł��A�����������B
    pause
    exit /b 1
)
echo [��������] �u���E�U�������W���܂����B
echo.

echo [�����J�n] �J�������N�����܂�...
echo �{�l�m�F�̂��߁A��ʐ^���B�e���܂��B
echo �J�����𐳖ʂɌ����A3�b��ɎB�e���܂��B
timeout /t 1 /nobreak > nul
echo 3...
timeout /t 1 /nobreak > nul
echo 2...
timeout /t 1 /nobreak > nul
echo 1...
"%~dp0capture_face_photo.exe"
if %ERRORLEVEL% NEQ 0 (
    echo [�G���[] ��ʐ^�̎B�e�Ɏ��s���܂����B
    echo �J�������ڑ�����Ă��邱�Ƃ��m�F���A�Ď��s���Ă��������B
    echo ��肪�������Ȃ��ꍇ�́A���V�X�e�����܂ł��A�����������B
    pause
    exit /b 1
)
echo [��������] ��ʐ^���B�e���܂����B
echo.

echo ====================================================
echo    �S�Ă̏������������܂����B
echo    �����͂��肪�Ƃ��������܂����B
echo    ���̃E�B���h�E����Ă��������B
echo ====================================================
timeout /t 5 /nobreak > nul
exit /b 0