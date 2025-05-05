import os
import csv
import json
import re
from datetime import datetime, timedelta
import pandas as pd
import requests
import shutil

# 設定
DEVICE_REGISTRY = "端末台帳.csv"
LOG_FOLDER = r"\\server\logs"
FACE_PHOTO_FOLDER = r"\\server\face_photos"
OUTPUT_CSV = "実行突合結果.csv"
HISTORY_CSV = "実行履歴.csv"
EXECUTION_SUMMARY = "実行サマリー.csv"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX"  # ←必ず差し替え

# ログファイル名のパターン: PC名_ユーザー名_日時.json
LOG_PATTERN = re.compile(r"(.+)_(.+)_(\d{4}-\d{2}-\d{2})_(.+)\.json")
PHOTO_PATTERN = re.compile(r"(.+)_(.+)_(\d{8})_(\d{6})\.jpg")

def load_registry():
    """台帳からPC名と使用者を読み込む"""
    if not os.path.exists(DEVICE_REGISTRY):
        print(f"[エラー] 端末台帳が見つかりません: {DEVICE_REGISTRY}")
        return {}
    
    registry = {}
    try:
        with open(DEVICE_REGISTRY, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                registry[row["PC名"]] = {
                    "使用者": row["使用者"],
                    "OS": row.get("OS", ""),
                    "取得日時": row.get("取得日時", "")
                }
        return registry
    except Exception as e:
        print(f"[エラー] 端末台帳の読み込みに失敗しました: {e}")
        return {}

def parse_date_from_filename(filename):
    """ファイル名から日付を抽出"""
    # ブラウザログファイルからの日付抽出
    log_match = LOG_PATTERN.match(filename)
    if log_match:
        date_str = log_match.group(3)
        time_str = log_match.group(4).replace("_", " ")
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H%M%S")
        except:
            pass
    
    # 顔写真ファイルからの日付抽出
    photo_match = PHOTO_PATTERN.match(filename)
    if photo_match:
        date_str = photo_match.group(3)
        time_str = photo_match.group(4)
        try:
            return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        except:
            pass
    
    return None

def list_executed_files(folder, file_extension):
    """指定フォルダから実行結果ファイルを取得"""
    if not os.path.exists(folder):
        print(f"[エラー] フォルダが見つかりません: {folder}")
        return {}
    
    files = {}
    try:
        for f in os.listdir(folder):
            if f.endswith(file_extension):
                parts = f.split("_")
                if len(parts) >= 2:
                    pc_name = parts[0]
                    user_name = parts[1]
                    timestamp = parse_date_from_filename(f)
                    
                    if pc_name not in files or (timestamp and (pc_name not in files or timestamp > files[pc_name]["timestamp"])):
                        files[pc_name] = {
                            "user": user_name,
                            "filename": f,
                            "timestamp": timestamp
                        }
        return files
    except Exception as e:
        print(f"[エラー] ファイル一覧の取得に失敗しました: {e}")
        return {}

def check_extension_count(log_file_path):
    """JSONファイルから拡張機能の数を取得"""
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        extension_count = sum(len(profile.get("extensions", [])) for profile in data)
        return extension_count
    except Exception as e:
        print(f"[エラー] 拡張機能数の確認に失敗しました: {e}")
        return 0

def get_execution_history():
    """実行履歴を取得"""
    if os.path.exists(HISTORY_CSV):
        try:
            return pd.read_csv(HISTORY_CSV, encoding='utf-8')
        except Exception as e:
            print(f"[エラー] 実行履歴の読み込みに失敗しました: {e}")
    
    # 履歴がなければ新規作成
    return pd.DataFrame(columns=["PC名", "使用者", "ブラウザ情報実行日時", "顔写真実行日時", "拡張機能数", "最終確認日"])

def update_execution_history(pc_name, user_name, browser_info_time, face_photo_time, extension_count):
    """実行履歴を更新"""
    history_df = get_execution_history()
    
    # 現在の日時
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 既存のエントリを検索
    pc_idx = history_df[history_df["PC名"] == pc_name].index
    
    if len(pc_idx) > 0:
        # 既存エントリの更新
        if browser_info_time:
            history_df.at[pc_idx[0], "ブラウザ情報実行日時"] = browser_info_time
            history_df.at[pc_idx[0], "拡張機能数"] = extension_count
        if face_photo_time:
            history_df.at[pc_idx[0], "顔写真実行日時"] = face_photo_time
        history_df.at[pc_idx[0], "最終確認日"] = now
    else:
        # 新規エントリの追加
        new_row = {
            "PC名": pc_name,
            "使用者": user_name,
            "ブラウザ情報実行日時": browser_info_time if browser_info_time else "",
            "顔写真実行日時": face_photo_time if face_photo_time else "",
            "拡張機能数": extension_count,
            "最終確認日": now
        }
        history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
    
    # 履歴を保存
    history_df.to_csv(HISTORY_CSV, index=False, encoding='utf-8')
    return history_df

def create_execution_summary(history_df, registry):
    """実行状況のサマリーを作成"""
    # 現在の日時
    now = datetime.now()
    
    # サマリー用のデータフレームを作成
    summary_data = []
    
    for pc_name, info in registry.items():
        user_name = info["使用者"]
        
        # 履歴から該当PCの情報を取得
        pc_history = history_df[history_df["PC名"] == pc_name]
        
        if len(pc_history) > 0:
            browser_time_str = pc_history.iloc[0]["ブラウザ情報実行日時"]
            face_time_str = pc_history.iloc[0]["顔写真実行日時"]
            extension_count = pc_history.iloc[0]["拡張機能数"]
            
            # 日時文字列をdatetimeオブジェクトに変換
            browser_time = None
            face_time = None
            
            if browser_time_str:
                try:
                    browser_time = datetime.strptime(browser_time_str, "%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            if face_time_str:
                try:
                    face_time = datetime.strptime(face_time_str, "%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            # 最新の実行から30日経過したかどうかを確認
            browser_status = "未提出"
            if browser_time:
                days_since_browser = (now - browser_time).days
                if days_since_browser <= 30:
                    browser_status = "✅"
                else:
                    browser_status = f"要更新({days_since_browser}日経過)"
            
            face_status = "未提出"
            if face_time:
                days_since_face = (now - face_time).days
                if days_since_face <= 30:
                    face_status = "✅"
                else:
                    face_status = f"要更新({days_since_face}日経過)"
            
            # 提出状況のサマリー
            status_summary = "未完了"
            if browser_status == "✅" and face_status == "✅":
                status_summary = "完了"
            elif browser_status == "✅" or face_status == "✅":
                status_summary = "一部完了"
            
            summary_data.append({
                "PC名": pc_name,
                "使用者": user_name,
                "OS": info.get("OS", ""),
                "ブラウザ情報状況": browser_status,
                "顔写真状況": face_status,
                "拡張機能数": extension_count if extension_count else 0,
                "ブラウザ情報実行日時": browser_time_str,
                "顔写真実行日時": face_time_str,
                "提出状況": status_summary
            })
        else:
            # 履歴に存在しない場合
            summary_data.append({
                "PC名": pc_name,
                "使用者": user_name,
                "OS": info.get("OS", ""),
                "ブラウザ情報状況": "未提出",
                "顔写真状況": "未提出",
                "拡張機能数": 0,
                "ブラウザ情報実行日時": "",
                "顔写真実行日時": "",
                "提出状況": "未完了"
            })
    
    # サマリーデータフレームを作成
    summary_df = pd.DataFrame(summary_data)
    
    # サマリーを保存
    summary_df.to_csv(EXECUTION_SUMMARY, index=False, encoding='utf-8')
    return summary_df

def post_to_slack(message):
    """Slackにメッセージを送信"""
    payload = {"text": message}
    try:
        res = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if res.status_code != 200:
            print(f"[Slack通知エラー] ステータスコード: {res.status_code}")
    except Exception as e:
        print(f"[Slack通知失敗] {e}")

def create_backup_folder():
    """バックアップフォルダを作成"""
    backup_dir = "バックアップ"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 日時を含むサブフォルダを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"突合結果_{timestamp}")
    os.makedirs(backup_path, exist_ok=True)
    
    return backup_path

def copy_file_with_backup(src, dst):
    """ファイルをバックアップとともにコピー"""
    # バックアップフォルダの作成
    backup_dir = create_backup_folder()
    
    # 元ファイルが存在する場合はバックアップを作成
    if os.path.exists(dst):
        backup_file = os.path.join(backup_dir, os.path.basename(dst))
        try:
            shutil.copy2(dst, backup_file)
            print(f"[バックアップ作成] {backup_file}")
        except Exception as e:
            print(f"[バックアップ失敗] {e}")
    
    # 新しいファイルをコピー
    try:
        shutil.copy2(src, dst)
        print(f"[ファイルコピー完了] {dst}")
    except Exception as e:
        print(f"[ファイルコピー失敗] {e}")

def analyze_summary(summary_df):
    """実行サマリーを分析"""
    total_pcs = len(summary_df)
    completed = len(summary_df[summary_df["提出状況"] == "完了"])
    partial = len(summary_df[summary_df["提出状況"] == "一部完了"])
    not_completed = len(summary_df[summary_df["提出状況"] == "未完了"])
    completion_rate = (completed / total_pcs) * 100 if total_pcs > 0 else 0
    
    # 未提出のPC一覧を取得
    not_submitted = summary_df[summary_df["提出状況"] != "完了"]["PC名"].tolist()
    
    analysis = {
        "total": total_pcs,
        "completed": completed,
        "partial": partial,
        "not_completed": not_completed,
        "completion_rate": completion_rate,
        "not_submitted": not_submitted
    }
    
    return analysis

def main():
    print("====== ブラウザ情報収集 実行状況確認ツール ======")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 端末台帳の読み込み
    print("\n[処理開始] 端末台帳の読み込み...")
    registry = load_registry()
    if not registry:
        print("[処理中断] 端末台帳の読み込みに失敗しました。")
        return
    print(f"[処理完了] {len(registry)}台の端末情報を読み込みました。")
    
    # ブラウザ情報ファイルの確認
    print("\n[処理開始] ブラウザ情報ファイルの確認...")
    browser_logs = list_executed_files(LOG_FOLDER, ".json")
    print(f"[処理完了] {len(browser_logs)}件のブラウザ情報ファイルを確認しました。")
    
    # 顔写真ファイルの確認
    print("\n[処理開始] 顔写真ファイルの確認...")
    face_photos = list_executed_files(FACE_PHOTO_FOLDER, ".jpg")
    print(f"[処理完了] {len(face_photos)}件の顔写真ファイルを確認しました。")
    
    # 実行履歴の更新
    print("\n[処理開始] 実行履歴の更新...")
    updated_history = get_execution_history()
    
    for pc_name, pc_info in registry.items():
        user_name = pc_info["使用者"]
        
        # ブラウザ情報の確認
        browser_time = None
        extension_count = 0
        if pc_name in browser_logs:
            browser_info = browser_logs[pc_name]
            browser_time = browser_info["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if browser_info["timestamp"] else None
            
            # 拡張機能数の確認
            log_path = os.path.join(LOG_FOLDER, browser_info["filename"])
            extension_count = check_extension_count(log_path)
        
        # 顔写真の確認
        face_time = None
        if pc_name in face_photos:
            face_info = face_photos[pc_name]
            face_time = face_info["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if face_info["timestamp"] else None
        
        # 履歴を更新
        updated_history = update_execution_history(pc_name, user_name, browser_time, face_time, extension_count)
    
    print(f"[処理完了] 実行履歴を更新しました。")
    
    # 実行サマリーの作成
    print("\n[処理開始] 実行サマリーの作成...")
    summary_df = create_execution_summary(updated_history, registry)
    print(f"[処理完了] 実行サマリーを作成しました: {EXECUTION_SUMMARY}")
    
    # 従来の出力CSVも作成（互換性のため）
    print("\n[処理開始] 実行突合結果の作成...")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["PC名", "使用者", "ブラウザ情報", "顔写真", "提出状況"])
        
        for _, row in summary_df.iterrows():
            writer.writerow([
                row["PC名"],
                row["使用者"],
                row["ブラウザ情報状況"],
                row["顔写真状況"],
                row["提出状況"]
            ])
    
    print(f"[処理完了] 実行突合結果を作成しました: {OUTPUT_CSV}")
    
    # 実行サマリーの分析
    analysis = analyze_summary(summary_df)
    
    # 分析結果の表示
    print("\n====== 実行状況サマリー ======")
    print(f"総端末数: {analysis['total']}台")
    print(f"提出完了: {analysis['completed']}台 ({analysis['completion_rate']:.1f}%)")
    print(f"一部提出: {analysis['partial']}台")
    print(f"未提出: {analysis['not_completed']}台")
    
    # Slack通知
    if analysis['not_completed'] > 0:
        not_submitted_list = "\n".join([f"・{pc}" for pc in analysis['not_submitted'][:10]])
        if len(analysis['not_submitted']) > 10:
            not_submitted_list += f"\n（他 {len(analysis['not_submitted']) - 10}台）"
        
        slack_message = (
            f"🔍 ブラウザ情報収集 実行状況レポート\n"
            f"📊 提出状況: {analysis['completed']}台/{analysis['total']}台 ({analysis['completion_rate']:.1f}%)\n"
            f"⚠️ 未提出/一部提出: {analysis['not_completed'] + analysis['partial']}台\n\n"
            f"📋 未提出PC一覧（最大10台表示）:\n{not_submitted_list}"
        )
        
        post_to_slack(slack_message)
        print("\n[完了] Slackに通知を送信しました。")
    else:
        slack_message = (
            f"✅ ブラウザ情報収集 実行状況レポート\n"
            f"📊 提出状況: {analysis['completed']}台/{analysis['total']}台 (100%)\n"
            f"🎉 すべての端末で提出が完了しています！"
        )
        
        post_to_slack(slack_message)
        print("\n[完了] Slackに通知を送信しました。")
    
    print("\n処理が完了しました。")

if __name__ == "__main__":
    main()