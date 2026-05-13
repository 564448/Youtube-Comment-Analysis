from googleapiclient.discovery import build
import pandas as pd

API_KEY = "AIzaSyARIbA6FhzK7Eg1rVWeI_pQM2VaiTdQc9o"

def Fetch(API_KEY,Youtube_Link,file_name="youtube_comments.csv"):
    
    if Youtube_Link[:32] == "https://www.youtube.com/watch?v=":
        VIDEO_ID = Youtube_Link[32:]
    elif Youtube_Link[:31] == "https://www.youtube.com/shorts/":
        VIDEO_ID = Youtube_Link[31:]

    youtube = build(
        "youtube",
        "v3",
        developerKey=API_KEY
    )

    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=VIDEO_ID,
        maxResults=100,
        textFormat="plainText"
    )

    response = request.execute()

    while request:
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "author": comment["authorDisplayName"],
                "comment": comment["textDisplay"],
                "likes": comment["likeCount"]
            })

        request = youtube.commentThreads().list_next(
            request,
            response
        )

        if request:
            response = request.execute()

    df = pd.DataFrame(comments)

    print(df.head())

    df.to_csv(f"{file_name}", index=False, encoding="utf-8-sig")
    return file_name 

if __name__ == "__main__":
    Youtube_Link = "https://www.youtube.com/watch?v=sDwC-D0S7M0"
    print(Fetch(API_KEY,Youtube_Link))