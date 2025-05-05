import os
import sys
import cv2
import datetime
import socket
import getpass

# 📁 写真保存先（共有ネットワークドライブ）
def get_shared_folder_path():
    return r"\\server\face_photos"

# 🖥 実行中のPC名を取得
def get_pc_name():
    return socket.gethostname()

# 👤 ログインユーザー名を取得
def get_user_name():
    return getpass.getuser()

# 📅 現在の日時を"YYYYMMDD_HHMMSS"形式で取得
def get_current_datetime_formatted():
    now = datetime.datetime.now()
    formatted_datetime = now.strftime("%Y%m%d_%H%M%S")
    return formatted_datetime

# 📂 保存先フォルダの存在を保証（なければ作成）
def ensure_output_path(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            print(f"[エラー] 保存先の作成に失敗しました: {e}")
            return False
    return True

# 📸 カメラから1枚だけ画像取得
def capture_image_from_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[エラー] カメラを起動できませんでした。")
        return None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("[エラー] 画像のキャプチャに失敗しました。")
        return None
    return frame

# 💾 画像を指定パスに保存
def save_image(image, path):
    try:
        cv2.imwrite(path, image)
        print(f"[保存完了] {path}")
    except Exception as e:
        print(f"[エラー] 画像保存に失敗しました: {e}")

# 📎 保存ファイル名を構築（PC名_ユーザー名_日時.jpg）
def build_filename():
    pc = get_pc_name()
    user = get_user_name()
    dt = get_current_datetime_formatted()
    return f"{pc}_{user}_{dt}.jpg"

# 📍 実行ファイルのあるディレクトリを取得（未使用だが保持）
def get_executable_directory():
    if getattr(sys, 'frozen', False):
        executable_path = sys.executable
    else:
        executable_path = __file__
    return os.path.dirname(os.path.abspath(executable_path))

# 🚀 メイン処理
def main():
    save_folder = get_shared_folder_path()
    if not ensure_output_path(save_folder):
        return
    filename = build_filename()
    full_save_path = os.path.join(save_folder, filename)
    frame = capture_image_from_camera()
    if frame is not None:
        save_image(frame, full_save_path)

if __name__ == "__main__":
    main()
