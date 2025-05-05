import os
import json
import socket
import getpass
import datetime
import requests
from pathlib import Path

# ===== Slack設定 =====
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX"  # ←必ず差し替え

# ===== 保存先ネットワークフォルダ（管理者用）=====
LOG_DIR = r"\\server\logs"

# ===== 情報取得補助関数 =====
def get_user_data_path(browser):
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise EnvironmentError("LOCALAPPDATA 環境変数が取得できません。")
    if browser == "chrome":
        return Path(local) / "Google" / "Chrome" / "User Data"
    elif browser == "edge":
        return Path(local) / "Microsoft" / "Edge" / "User Data"
    else:
        raise ValueError("Unsupported browser")

def list_profiles(user_data_path):
    local_state_file = user_data_path / "Local State"
    with open(local_state_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    profiles = data["profile"]["profiles_order"]
    profile_info = data["profile"]["info_cache"]
    result = []
    for prof in profiles:
        info = profile_info.get(prof, {})
        result.append({
            "profile": prof,
            "user_name": info.get("user_name", ""),
            "gaia_name": info.get("gaia_name", "")
        })
    return result

def list_extensions(profile_path):
    ext_path = profile_path / "Extensions"
    if not ext_path.exists():
        return []
    extensions = []
    for ext_id in ext_path.iterdir():
        if ext_id.name == "Temp":
            continue
        for version_dir in ext_id.iterdir():
            manifest_file = version_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    extensions.append({
                        "id": ext_id.name,
                        "version": version_dir.name,
                        "name": manifest.get("name", "N/A"),
                        "description": manifest.get("description", ""),
                        "manifest_version": manifest.get("manifest_version", "")
                    })
                except:
                    continue
    return extensions

def scan_browser(browser):
    user_data_path = get_user_data_path(browser)
    profiles = list_profiles(user_data_path)
    results = []
    for prof in profiles:
        prof_info = {
            "browser": browser,
            "profile": prof['profile'],
            "user_name": prof['user_name'],
            "gaia_name": prof['gaia_name'],
            "extensions": list_extensions(user_data_path / prof["profile"])
        }
        results.append(prof_info)
    return results

# ===== Slack送信 =====
def post_to_slack(message):
    payload = {"text": message}
    try:
        res = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if res.status_code != 200:
            print(f"[Slack通知エラー] ステータスコード: {res.status_code}")
    except Exception as e:
        print(f"[Slack通知失敗] {e}")

# ===== JSON保存処理 =====
def save_log_to_network(data, pc_name, user_name, timestamp):
    filename = f"{pc_name}_{user_name}_{timestamp.replace(':', '').replace(' ', '_')}.json"
    os.makedirs(LOG_DIR, exist_ok=True)
    full_path = os.path.join(LOG_DIR, filename)
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[保存完了] ログ → {full_path}")
    except Exception as e:
        print(f"[保存失敗] {e}")

# ===== メイン =====
def main():
    pc_name = socket.gethostname()
    user_name = getpass.getuser()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_data = []

    for browser in ["chrome", "edge"]:
        try:
            result = scan_browser(browser)
            all_data.extend(result)
        except Exception as e:
            print(f"[{browser}] スキャン中にエラー: {e}")

    profile_count = len(all_data)
    extension_count = sum(len(p["extensions"]) for p in all_data)

    # Slack通知
    slack_message = (
        f"✅ 拡張機能収集完了\n"
        f"📌 PC名: {pc_name}\n"
        f"👤 ユーザー: {user_name}\n"
        f"🕒 実行時刻: {timestamp}\n"
        f"🌐 プロファイル数: {profile_count}件\n"
        f"🧩 拡張機能数: {extension_count}件"
    )
    post_to_slack(slack_message)

    # JSON保存
    save_log_to_network(all_data, pc_name, user_name, timestamp)

if __name__ == "__main__":
    main()
