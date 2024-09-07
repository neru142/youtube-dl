from googleapiclient.discovery import build
import subprocess
import re
from datetime import timedelta

# YouTube APIの設定
API_KEY = 'YourToken'  # 取得したAPIキー
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def parse_duration(duration):
    # ISO 8601形式の動画の長さを分単位に変換する関数
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if match:
        hours, minutes, seconds = match.groups(default='0')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        return total_seconds / 60  # 分単位で返す
    return 0

def search_videos(query, max_results=5, exclude_urls=None):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    
    # YouTubeでの検索
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        maxResults=max_results,
        type='video'
    ).execute()

    # 動画情報を保存
    videos = []
    exclude_urls = exclude_urls or set()
    for item in search_response['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_url = f'https://www.youtube.com/watch?v={video_id}'

        # 前回取得した動画を除外
        if video_url in exclude_urls:
            continue

        # 動画の詳細を取得（動画の長さを確認）
        video_details = youtube.videos().list(
            part='contentDetails',
            id=video_id
        ).execute()

        duration = video_details['items'][0]['contentDetails']['duration']
        duration_minutes = parse_duration(duration)

        # 5分未満の動画をフィルタリング
        if duration_minutes < 5:
            videos.append((video_title, video_url))

    return videos

def download_video(video_url, format_type):
    # yt-dlpを使って動画または音声をダウンロード
    if format_type == 'video':
        subprocess.run(['yt-dlp', '-f', 'mp4', video_url])
    elif format_type == 'audio':
        subprocess.run(['yt-dlp', '-x', '--audio-format', 'mp3', video_url])

def print_instructions():
    # スクリプトの説明と使い方を表示
    print("YouTube動画ダウンローダー")
    print("このスクリプトは、YouTubeから動画を検索またはURLを指定してダウンロードできます。")
    print("キーワードで検索した場合は5分未満の動画のみがリストアップされます。")
    print("\n使い方:")
    print("1. スクリプトを実行します。")
    print("2. 検索キーワードを入力するか、URLを指定してダウンロードします。")
    print("3. 検索結果からダウンロードしたい動画の番号を選択します。")
    print("4. 動画か音声のどちらでダウンロードするかを選択します。")
    print("5. 選択した形式で動画がダウンロードされます。")
    print("6. 結果を再取得したい場合は「再取得」、検索ワードを変更したい場合は「キーワードを変更する」、")
    print("   または検索を終了するには「終了」を選択できます。")

if __name__ == '__main__':
    print_instructions()  # スクリプトの説明を表示

    previous_urls = set()

    while True:
        # 検索キーワードを入力するか、URLを指定するかの選択
        choice = input('\n検索キーワードを入力しますか？ (keyword)\nそれともURLを指定しますか？(url)\nまたはスクリプトを終了しますか？(end): ').strip().lower()

        if choice == 'url':
            video_url = input('ダウンロードしたい動画のURLを入力してください: ').strip()
            format_type = input('ダウンロード形式を選んでください（video/audio）: ').strip().lower()

            if format_type in ['video', 'audio']:
                print(f'{video_url} を{format_type}としてダウンロード中...')
                download_video(video_url, format_type)
            else:
                print('無効な形式の選択です。')

        elif choice == 'keyword':
            query = input('\n検索キーワードを入力してください: ')

            while True:
                videos = search_videos(query, max_results=10, exclude_urls=previous_urls)

                # 検索結果を表示
                if not videos:
                    print("\n条件に合う動画が見つかりませんでした。検索ワードを変更して再検索します。")
                    break  # 検索ワードを変更するためにループを抜ける
                else:
                    print("\n検索結果:")
                    for i, (title, url) in enumerate(videos):
                        print(f'{i + 1}. {title} ({url})')

                    # ユーザーにダウンロードする動画を選ばせる
                    choice = input('\nダウンロードしたい動画の番号を選んでください (または「初めに戻る:reset」「再取得:reget」「終了:end」): ').strip()
                    if choice.lower() == 'reset':
                        break  # 検索ワードを変更するためにループを抜ける
                    elif choice.lower() == 'reget':
                        continue  # 検索結果を再取得するためにループを続ける
                    elif choice.lower() == 'end':
                        print('スクリプトを終了します。')
                        exit()  # スクリプトを終了する

                    try:
                        choice = int(choice) - 1
                        if 0 <= choice < len(videos):
                            selected_video_url = videos[choice][1]
                            format_type = input('\nダウンロード形式を選んでください（video/audio）: ').strip().lower()
                            if format_type in ['video', 'audio']:
                                print(f'\n{videos[choice][0]} を{format_type}としてダウンロード中...')
                                download_video(selected_video_url, format_type)
                                previous_urls.add(selected_video_url)  # ダウンロードした動画のURLを記録
                            else:
                                print('無効な形式の選択です。')
                        else:
                            print('無効な選択です。キーワードを変更してください。')
                            break  # 無効な選択の場合、検索ワードを変更するためにループを抜ける
                    except ValueError:
                        print('無効な番号が入力されました。キーワードを変更してください。')
                        break  # 無効な番号の場合、検索ワードを変更するためにループを抜ける

            # 再取得の選択肢を提供
            retry = input('\n初めに戻りますか？ (y/n): ').strip().lower()
            if retry != 'y':
                print('スクリプトを終了します。')
                break
        elif choice == 'end':
            print('スクリプトを終了します。')
            break
        else:
            print('無効な選択肢です。')
