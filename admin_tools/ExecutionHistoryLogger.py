import os
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import csv
import re

# 設定
LOG_FOLDER = r"\\server\logs"
FACE_PHOTO_FOLDER = r"\\server\face_photos"
ARCHIVE_FOLDER = r"\\server\archives"
REPORTS_FOLDER = "レポート"
EXECUTION_SUMMARY = "実行サマリー.csv"
HISTORY_CSV = "実行履歴.csv"

# ログファイル名のパターン
LOG_PATTERN = re.compile(r"(.+)_(.+)_(\d{4}-\d{2}-\d{2})_(.+)\.json")
PHOTO_PATTERN = re.compile(r"(.+)_(.+)_(\d{8})_(\d{6})\.jpg")

def ensure_directory(path):
    """ディレクトリの存在を確認し、なければ作成"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"[作成完了] ディレクトリ: {path}")

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

def organize_files_by_date(src_folder, file_ext, archive_base):
    """ファイルを日付ごとに整理"""
    if not os.path.exists(src_folder):
        print(f"[エラー] フォルダが見つかりません: {src_folder}")
        return []
    
    # アーカイブベースフォルダの作成
    archive_path = os.path.join(ARCHIVE_FOLDER, archive_base)
    ensure_directory(archive_path)
    
    # ファイル情報を収集
    file_info = []
    
    for filename in os.listdir(src_folder):
        if not filename.endswith(file_ext):
            continue
        
        file_path = os.path.join(src_folder, filename)
        timestamp = parse_date_from_filename(filename)
        
        if not timestamp:
            print(f"[スキップ] 日付を解析できませんでした: {filename}")
            continue
        
        # 年月フォルダの作成
        year_month = timestamp.strftime("%Y-%m")
        year_month_folder = os.path.join(archive_path, year_month)
        ensure_directory(year_month_folder)
        
        # ファイル情報を記録
        file_info.append({
            "filename": filename,
            "original_path": file_path,
            "archive_path": os.path.join(year_month_folder, filename),
            "timestamp": timestamp,
            "year_month": year_month,
            "pc_name": filename.split("_")[0] if "_" in filename else "",
            "user_name": filename.split("_")[1] if "_" in filename and len(filename.split("_")) > 1 else ""
        })
    
    return file_info

def archive_old_files(file_info, days_threshold=90):
    """古いファイルをアーカイブ"""
    now = datetime.now()
    archive_count = 0
    
    for info in file_info:
        # ファイルの経過日数を計算
        days_old = (now - info["timestamp"]).days
        
        # 指定日数より古いファイルをアーカイブ
        if days_old > days_threshold:
            # アーカイブにコピー
            try:
                shutil.copy2(info["original_path"], info["archive_path"])
                archive_count += 1
            except Exception as e:
                print(f"[アーカイブ失敗] {info['filename']}: {e}")
    
    return archive_count

def check_extension_count(log_file_path):
    """JSONファイルから拡張機能の数を取得"""
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        extension_count = sum(len(profile.get("extensions", [])) for profile in data)
        return extension_count
    except Exception as e:
        print(f"[エラー] 拡張機能数の確認に失敗しました: {log_file_path}: {e}")
        return 0

def create_execution_trends_report():
    """実行傾向レポートの作成"""
    # レポートフォルダの作成
    ensure_directory(REPORTS_FOLDER)
    
    # 履歴CSVの読み込み
    if not os.path.exists(HISTORY_CSV):
        print(f"[エラー] 実行履歴が見つかりません: {HISTORY_CSV}")
        return
    
    try:
        history_df = pd.read_csv(HISTORY_CSV, encoding='utf-8')
    except Exception as e:
        print(f"[エラー] 実行履歴の読み込みに失敗しました: {e}")
        return
    
    # 日付列を日付型に変換
    for col in ["ブラウザ情報実行日時", "顔写真実行日時", "最終確認日"]:
        if col in history_df.columns:
            history_df[col] = pd.to_datetime(history_df[col], errors='coerce')
    
    # 月ごとの実行数を集計
    browser_monthly = history_df.groupby(history_df["ブラウザ情報実行日時"].dt.strftime("%Y-%m")).size()
    photo_monthly = history_df.groupby(history_df["顔写真実行日時"].dt.strftime("%Y-%m")).size()
    
    # 拡張機能数の統計
    extension_stats = {
        "平均": history_df["拡張機能数"].mean(),
        "最大": history_df["拡張機能数"].max(),
        "最小": history_df["拡張機能数"].min(),
        "中央値": history_df["拡張機能数"].median()
    }
    
    # グラフの作成
    plt.figure(figsize=(12, 8))
    
    # 月別実行数のグラフ
    plt.subplot(2, 1, 1)
    browser_monthly.plot(kind='bar', color='blue', alpha=0.6, label='ブラウザ情報')
    photo_monthly.plot(kind='bar', color='green', alpha=0.6, label='顔写真')
    plt.title('月別実行数')
    plt.xlabel('年月')
    plt.ylabel('実行数')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 拡張機能数の分布
    plt.subplot(2, 1, 2)
    history_df["拡張機能数"].plot(kind='hist', bins=20, color='orange', alpha=0.7)
    plt.title('拡張機能数の分布')
    plt.xlabel('拡張機能数')
    plt.ylabel('PC数')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # グラフを保存
    report_path = os.path.join(REPORTS_FOLDER, f"実行傾向レポート_{datetime.now().strftime('%Y%m%d')}.png")
    plt.savefig(report_path)
    plt.close()
    
    print(f"[作成完了] 実行傾向レポート: {report_path}")
    
    # 統計情報のCSV出力
    stats_path = os.path.join(REPORTS_FOLDER, f"拡張機能統計_{datetime.now().strftime('%Y%m%d')}.csv")
    
    with open(stats_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["統計項目", "値"])
        for key, value in extension_stats.items():
            writer.writerow([key, f"{value:.2f}"])
    
    print(f"[作成完了] 拡張機能統計: {stats_path}")
    
    return report_path, stats_path

def get_submission_status():
    """提出状況のサマリーを取得"""
    if not os.path.exists(EXECUTION_SUMMARY):
        print(f"[エラー] 実行サマリーが見つかりません: {EXECUTION_SUMMARY}")
        return None
    
    try:
        summary_df = pd.read_csv(EXECUTION_SUMMARY, encoding='utf-8')
        
        total = len(summary_df)
        completed = len(summary_df[summary_df["提出状況"] == "完了"])
        partial = len(summary_df[summary_df["提出状況"] == "一部完了"])
        not_completed = len(summary_df[summary_df["提出状況"] == "未完了"])
        
        return {
            "total": total,
            "completed": completed,
            "partial": partial,
            "not_completed": not_completed,
            "completion_rate": (completed / total) * 100 if total > 0 else 0
        }
    except Exception as e:
        print(f"[エラー] 実行サマリーの読み込みに失敗しました: {e}")
        return None

def create_overall_report():
    """総合レポートの作成"""
    # レポートフォルダの作成
    reports_path = os.path.join(REPORTS_FOLDER, "定期レポート")
    ensure_directory(reports_path)
    
    # 現在の日時
    now = datetime.now()
    report_date = now.strftime("%Y年%m月%d日")
    
    # 提出状況を取得
    status = get_submission_status()
    if not status:
        return
    
    # ブラウザログファイルの整理
    browser_logs = organize_files_by_date(LOG_FOLDER, ".json", "browser_logs")
    
    # 顔写真ファイルの整理
    face_photos = organize_files_by_date(FACE_PHOTO_FOLDER, ".jpg", "face_photos")
    
    # PC名ごとに最新の提出日を取得
    latest_submissions = {}
    
    for log in browser_logs:
        pc_name = log["pc_name"]
        if pc_name not in latest_submissions or log["timestamp"] > latest_submissions[pc_name]["browser_time"]:
            if pc_name not in latest_submissions:
                latest_submissions[pc_name] = {"browser_time": None, "photo_time": None}
            latest_submissions[pc_name]["browser_time"] = log["timestamp"]
    
    for photo in face_photos:
        pc_name = photo["pc_name"]
        if pc_name not in latest_submissions or photo["timestamp"] > latest_submissions[pc_name]["photo_time"]:
            if pc_name not in latest_submissions:
                latest_submissions[pc_name] = {"browser_time": None, "photo_time": None}
            latest_submissions[pc_name]["photo_time"] = photo["timestamp"]
    
    # 月別の提出数を集計
    browser_monthly = {}
    photo_monthly = {}
    
    for log in browser_logs:
        year_month = log["year_month"]
        if year_month not in browser_monthly:
            browser_monthly[year_month] = 0
        browser_monthly[year_month] += 1
    
    for photo in face_photos:
        year_month = photo["year_month"]
        if year_month not in photo_monthly:
            photo_monthly[year_month] = 0
        photo_monthly[year_month] += 1
    
    # レポートファイルを作成
    report_path = os.path.join(reports_path, f"ブラウザ情報収集_総合レポート_{now.strftime('%Y%m%d')}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# ブラウザ情報収集 総合レポート\n\n")
        f.write(f"**作成日時:** {report_date}\n\n")
        
        f.write("## 1. 提出状況サマリー\n\n")
        f.write(f"- **総端末数:** {status['total']}台\n")
        f.write(f"- **提出完了:** {status['completed']}台 ({status['completion_rate']:.1f}%)\n")
        f.write(f"- **一部提出:** {status['partial']}台\n")
        f.write(f"- **未提出:** {status['not_completed']}台\n\n")
        
        f.write("## 2. 月別提出数\n\n")
        f.write("### ブラウザ情報\n\n")
        f.write("| 年月 | 提出数 |\n")
        f.write("|------|-------|\n")
        for year_month in sorted(browser_monthly.keys(), reverse=True):
            f.write(f"| {year_month} | {browser_monthly[year_month]} |\n")
        
        f.write("\n### 顔写真\n\n")
        f.write("| 年月 | 提出数 |\n")
        f.write("|------|-------|\n")
        for year_month in sorted(photo_monthly.keys(), reverse=True):
            f.write(f"| {year_month} | {photo_monthly[year_month]} |\n")
        
        f.write("\n## 3. ファイル管理状況\n\n")
        f.write(f"- **ブラウザ情報ファイル総数:** {len(browser_logs)}件\n")
        f.write(f"- **顔写真ファイル総数:** {len(face_photos)}件\n\n")
        
        # 今月と先月の提出状況
        current_month = now.strftime("%Y-%m")
        last_month = (now - timedelta(days=30)).strftime("%Y-%m")
        
        current_month_browser = browser_monthly.get(current_month, 0)
        last_month_browser = browser_monthly.get(last_month, 0)
        current_month_photo = photo_monthly.get(current_month, 0)
        last_month_photo = photo_monthly.get(last_month, 0)
        
        f.write("## 4. 今月と先月の提出状況\n\n")
        f.write("| 項目 | 今月 | 先月 | 増減 |\n")
        f.write("|------|------|------|------|\n")
        f.write(f"| ブラウザ情報 | {current_month_browser} | {last_month_browser} | {current_month_browser - last_month_browser} |\n")
        f.write(f"| 顔写真 | {current_month_photo} | {last_month_photo} | {current_month_photo - last_month_photo} |\n\n")
        
        f.write("## 5. 提出遅延状況\n\n")
        
        # 30日以上提出のないPCをカウント
        browser_delay_count = 0
        photo_delay_count = 0
        
        for pc_name, times in latest_submissions.items():
            if times["browser_time"] and (now - times["browser_time"]).days > 30:
                browser_delay_count += 1
            if times["photo_time"] and (now - times["photo_time"]).days > 30:
                photo_delay_count += 1
        
        f.write("### 30日以上提出のないPC数\n\n")
        f.write(f"- **ブラウザ情報:** {browser_delay_count}台\n")
        f.write(f"- **顔写真:** {photo_delay_count}台\n\n")
        
        f.write("## 6. 次回のアクション\n\n")
        f.write("- [ ] 未提出PCへのリマインダー送信\n")
        f.write("- [ ] 30日以上提出のないPCの確認\n")
        f.write("- [ ] 古いファイルのアーカイブ処理\n")
    
    print(f"[作成完了] 総合レポート: {report_path}")
    return report_path

def archive_files_by_period(days_threshold=90):
    """一定期間経過したファイルをアーカイブ"""
    print("\n====== ファイルアーカイブ処理 ======")
    
    # ブラウザログファイルの整理
    print("\n[処理開始] ブラウザログファイルの整理...")
    browser_logs = organize_files_by_date(LOG_FOLDER, ".json", "browser_logs")
    browser_archive_count = archive_old_files(browser_logs, days_threshold)
    print(f"[処理完了] {browser_archive_count}件のブラウザログファイルをアーカイブしました。")
    
    # 顔写真ファイルの整理
    print("\n[処理開始] 顔写真ファイルの整理...")
    face_photos = organize_files_by_date(FACE_PHOTO_FOLDER, ".jpg", "face_photos")
    photo_archive_count = archive_old_files(face_photos, days_threshold)
    print(f"[処理完了] {photo_archive_count}件の顔写真ファイルをアーカイブしました。")
    
    return browser_archive_count, photo_archive_count

def main():
    """メイン処理"""
    print("====== ブラウザ情報収集 履歴管理ツール ======")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # アーカイブフォルダの作成
    ensure_directory(ARCHIVE_FOLDER)
    ensure_directory(REPORTS_FOLDER)
    
    while True:
        print("\n以下の操作から選択してください:")
        print("1. 実行傾向レポートの作成")
        print("2. 総合レポートの作成")
        print("3. ファイルのアーカイブ処理（90日以上経過したファイル）")
        print("4. ファイルのアーカイブ処理（期間指定）")
        print("5. すべての処理を実行")
        print("0. 終了")
        
        choice = input("\n選択（0-5）: ")
        
        if choice == "1":
            print("\n[処理開始] 実行傾向レポートの作成...")
            create_execution_trends_report()
        
        elif choice == "2":
            print("\n[処理開始] 総合レポートの作成...")
            create_overall_report()
        
        elif choice == "3":
            print("\n[処理開始] ファイルのアーカイブ処理（90日）...")
            archive_files_by_period(90)
        
        elif choice == "4":
            try:
                days = int(input("アーカイブする日数を入力してください（例: 30）: "))
                print(f"\n[処理開始] ファイルのアーカイブ処理（{days}日）...")
                archive_files_by_period(days)
            except ValueError:
                print("[エラー] 有効な数値を入力してください。")
        
        elif choice == "5":
            print("\n[処理開始] すべての処理を実行...")
            create_execution_trends_report()
            create_overall_report()
            archive_files_by_period(90)
            print("[処理完了] すべての処理が完了しました。")
        
        elif choice == "0":
            print("\n処理を終了します。")
            break
        
        else:
            print("[エラー] 0から5の数字を入力してください。")

if __name__ == "__main__":
    main()