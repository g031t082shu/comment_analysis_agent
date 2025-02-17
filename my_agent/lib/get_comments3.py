import googleapiclient.discovery
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

dev = os.getenv('YOUTUBE_DEVELOPER_KEY')

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = dev

comment_count = 0

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY)

def get_reply_comments(parent_comment_id):
    request = youtube.comments().list(
        part="snippet",
        parentId=parent_comment_id,
        maxResults=100
    )

    comments = []
    global comment_count

    # Execute the request.
    response = request.execute()

    # Get the comments from the response.
    for item in response['items']:
        comment = item['snippet']
        comments.append([
            item['id'],
            parent_comment_id,
            comment['publishedAt'],
            comment['authorDisplayName'],
            comment['textOriginal'],
            comment['likeCount']
        ])

        comment_count += 1
        print(comment_count)

    while (1 == 1):
        try:
            nextPageToken = response['nextPageToken']
        except KeyError:
            break
        nextPageToken = response['nextPageToken']
        # Create a new request object with the next page token.
        nextRequest = youtube.comments().list(part="snippet", parentId=parent_comment_id, maxResults=100, pageToken=nextPageToken)
        # Execute the next request.
        response = nextRequest.execute()
        # Get the comments from the next response.
        for item in response['items']:
            comment = item['snippet']
            comments.append([
                item['id'],
                parent_comment_id,
                comment['publishedAt'],
                comment['authorDisplayName'],
                comment['textOriginal'],
                comment['likeCount']
            ])

            comment_count += 1
            print(comment_count)

    df2 = pd.DataFrame(comments, columns=['id','parent_id', 'published_at', 'author', 'text','like_count'])
    return comments

def get_comments(video_id):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100
    )

    comments = []
    global comment_count

    # Execute the request.
    response = request.execute()

    # Get the comments from the response.
    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']
        public = item['snippet']['isPublic']
        comments.append([
            item['id'],
            None,
            comment['publishedAt'],
            comment['authorDisplayName'],
            comment['textOriginal'],
            comment['likeCount']
        ])

        comment_count += 1
        print(comment_count)

        if item['snippet']['totalReplyCount'] > 0:
            reps = get_reply_comments(item['id'])
            comments += reps

    while (1 == 1):
        try:
            nextPageToken = response['nextPageToken']
        except KeyError:
            break
        nextPageToken = response['nextPageToken']
        # Create a new request object with the next page token.
        nextRequest = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=100, pageToken=nextPageToken)
        # Execute the next request.
        response = nextRequest.execute()
        # Get the comments from the next response.
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            public = item['snippet']['isPublic']
            comments.append([
                item['id'],
                None,
                comment['publishedAt'],
                comment['authorDisplayName'],
                comment['textOriginal'],
                comment['likeCount']
            ])

            comment_count += 1
            print(comment_count)

            if item['snippet']['totalReplyCount'] > 0:
                reps = get_reply_comments(item['id'])
                comments += reps

    df2 = pd.DataFrame(comments, columns=['id','parent_id', 'published_at', 'author', 'text','like_count'])
    return df2