import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

def get_video_id(url):
    """สกัด Video ID จาก URL ของ YouTube ในรูปแบบต่างๆ"""
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

def clean_text(text):
    #ทำ Data Cleaning เบื้องต้น
    if not text:
        return ""
    # ลบช่องว่างส่วนเกินหน้า-หลัง และลบบรรทัดว่างที่ติดกันเกินไป
    text = text.strip()
    text = re.sub(r'\n\s*\n', '\n', text) 
    return text

def Fetch(api_key, youtube_url, file_name="youtube_comments.csv"):
    video_id = get_video_id(youtube_url)
    if not video_id:
        print("Error: รูปแบบ URL ไม่ถูกต้อง")
        return

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        # 1. ดึงสถิติวิดีโอเพื่อดูจำนวนคอมเมนต์ทั้งหมด (Target Count)
        video_response = youtube.videos().list(
            part="statistics",
            id=video_id
        ).execute()

        if not video_response["items"]:
            print("Error: ไม่พบวิดีโอ")
            return

        total_expected = int(video_response["items"][0]["statistics"].get("commentCount", 0))
        print(f"เป้าหมาย: วิดีโอนี้มีประมาณ {total_expected} คอมเมนต์")

        comments_data = []
        next_page_token = None

        print("กำลังเริ่มดึงข้อมูลคอมเมนต์...")

        # 2. Loop ดึงคอมเมนต์หลัก (Top-level) และคอมเมนต์ตอบกลับ (Replies)
        while True:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()

            for item in response.get("items", []):
                # ดึงคอมเมนต์หลัก
                top_comment = item["snippet"]["topLevelComment"]["snippet"]
                comments_data.append({
                    "author": top_comment["authorDisplayName"],
                    "comment": clean_text(top_comment["textDisplay"]),
                    "likes": top_comment["likeCount"],
                    "type": "main"
                })

                # ดึงคอมเมนต์ตอบกลับ (ถ้ามี)
                if "replies" in item:
                    for reply in item["replies"]["comments"]:
                        reply_snippet = reply["snippet"]
                        comments_data.append({
                            "author": reply_snippet["authorDisplayName"],
                            "comment": clean_text(reply_snippet["textDisplay"]),
                            "likes": reply_snippet["likeCount"],
                            "type": "reply"
                        })

            print(f"ดึงมาได้แล้ว {len(comments_data)} รายการ...")

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        # 3. สรุปผลการทำงาน (Integrity Check)
        actual_count = len(comments_data)
        print(f"\nดึงข้อมูลเสร็จสิ้น!")
        print(f"จำนวนที่ดึงได้จริง: {actual_count} รายการ")
        print(f"คิดเป็น {(actual_count/total_expected)*100:.2f}% ของคอมเมนต์ทั้งหมดบน YouTube (ส่วนต่างอาจเกิดจากสแปมที่ถูกซ่อนไว้)")

        # 4. Data Cleaning ก่อน Save (ลบแถวที่คอมเมนต์ว่าง)
        df = pd.DataFrame(comments_data)
        df = df[df['comment'] != ""] # ลบคอมเมนต์ที่เป็นค่าว่าง

        # 5. บันทึกเป็น CSV (ใช้ utf-8-sig เพื่อให้ Excel อ่านภาษาไทยออก)
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        print(f"บันทึกไฟล์เรียบร้อย: {file_name}")
        return file_name,total_expected

    except HttpError as e:
        print(f"API Error: {e.reason}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    API_KEY = ""
    Youtube_Link = "https://www.youtube.com/watch?v=sDwC-D0S7M0"
    print(Fetch(API_KEY,Youtube_Link))