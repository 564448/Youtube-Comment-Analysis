import csv
def get_comments_from_csv(file_path):
    comments_list = []
    try:
        # ใช้ utf-8-sig เพื่อรองรับไฟล์ที่เซฟมาจาก Excel ให้ภาษาไทยไม่เพี้ยน [cite: 116, 136]
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # ดึงเฉพาะคอลัมน์ 'comment' มาเก็บใน list
                if row['comment']:
                    comments_list.append(row['comment'])
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
        
    return comments_list

# การใช้งาน
if __name__ == "__main__":
    all_comments = get_comments_from_csv('youtube_comments.csv')
    print(f"ดึงข้อมูลมาได้ทั้งหมด {len(all_comments)} ข้อความ")