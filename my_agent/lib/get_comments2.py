import pandas as pd
from googleapiclient.discovery import build
import time
from dotenv import load_dotenv
import os

load_dotenv()

# YouTube APIキーを設定
API_KEY = os.getenv('YOUTUBE_DEVELOPER_KEY') # ここにAPIキーを入力

# YouTube APIクライアントを作成
youtube = build("youtube", "v3", developerKey=API_KEY)

comment_cont = 0

def get_reply_comments(parent_comment_id):
    global comment_cont

    while 1:
        comments = []
        next_page_token = None

        req = youtube.comments().list(
                part="snippet",
                parentId=parent_comment_id,
                maxResults=100,
                pageToken=next_page_token
            )
        res = req.execute()
        for reply in res['items']:
            reply_snippet = reply["snippet"]
            comments.append({
                "comment_id": reply["id"],
                "parent_id": parent_comment_id,  # 親コメントのID
                "author": reply_snippet["authorDisplayName"],
                "text": reply_snippet["textOriginal"],
                "published_at": reply_snippet["publishedAt"],
                "like_count": reply_snippet["likeCount"]
            })

            comment_cont += 1
            print(comment_cont)

        # 次のページがあるか確認
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(1)  # API制限対策（1秒待機）

    return comments


def get_comments(video_id):
    """指定した動画の全コメントとリプライを取得し、pandas.DataFrameに格納"""
    comments = []
    global comment_cont

    # ページネーション用のトークン
    next_page_token = None

    while True:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,  # 1回のリクエストで最大100件取得
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "parent_id": None,  # 親なし（トップレベルコメント）
                "author": top_comment["authorDisplayName"],
                "text": top_comment["textOriginal"],
                "published_at": top_comment["publishedAt"],
                "like_count": top_comment["likeCount"]
            })

            comment_cont += 1
            print(comment_cont)

            # リプライがある場合
            if item['snippet']['totalReplyCount'] > 0:
               reps = get_reply_comments(item['id'])
               comments += reps

        # 次のページがあるか確認
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(1)  # API制限対策（1秒待機）

    # DataFrameに変換
    df = pd.DataFrame(comments)

    return df

