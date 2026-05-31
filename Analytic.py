import ollama
import json
import csv

with open("prompt.txt", "r", encoding="utf-8") as file:
    content = file.read()
defualt_instruction = content

def analyze_and_export_csv(comment_list, output_file="analysis_results.csv", batch_size=25, MODEL="qwen2.5:latest"):
    # 1. กำหนดกฎเหล็ก (System Prompt)
    system_instruction = f"""{defualt_instruction}
    ตอบกลับเป็น JSON เท่านั้น:
        {{ "groups": [ {{ "category": "ชื่อกลุ่มหลัก", "summary": "สรุปทิศทางและประเด็น", "count": จำนวน }} ] }}
        """

    # ตัวแปรสำหรับสะสมผลลัพธ์ใน Python (เพื่อความแม่นยำ)
    final_results = {} # โครงสร้าง: { "ชื่อหมวดหมู่": {"summaries": [], "total_count": 0} }

    print(f"เริ่มการวิเคราะห์ทั้งหมด {len(comment_list)} คอมเมนต์...")

    # 2. เริ่มประมวลผลทีละ Batch
    for i in range(0, len(comment_list), batch_size):
        batch = comment_list[i : i + batch_size]
        current_batch_num = i // batch_size + 1
        print(f"กำลังประมวลผล Batch ที่ {current_batch_num}...")

        # ดึงรายชื่อหมวดหมู่ที่มีอยู่แล้ว ณ ปัจจุบัน
        existing_categories = list(final_results.keys())
        categories_str = ", ".join(existing_categories) if existing_categories else "ยังไม่มี (เริ่มสร้างใหม่ได้เลย)"

        user_prompt = f"""หมวดหมู่ที่มีอยู่แล้วในขณะนี้: [{categories_str}]

คอมเมนต์ที่ต้องวิเคราะห์ในชุดนี้: 
{json.dumps(batch, ensure_ascii=False)}

จงวิเคราะห์และจัดกลุ่มคอมเมนต์ชุดนี้ตามกฎที่ให้ไว้ใน System Prompt"""

        try:
            response = ollama.chat(
                model=MODEL,
                messages=[
                    {'role': 'system', 'content': system_instruction},
                    {'role': 'user', 'content': user_prompt}
                ],
                format="json",
                options={"temperature": 0.1} # ใช้ Temp ต่ำเพื่อให้ AI ทำตามกฎเคร่งครัด
            )
            
            result_data = json.loads(response['message']['content'])
            
            # 3. นำคำตอบจาก AI มาสะสมใน Python Dictionary
            for group in result_data.get('groups', []):
                cat_name = group.get('category').strip()
                count = group.get('count', 0)
                summary = group.get('summary')

                if cat_name in final_results:
                    final_results[cat_name]['total_count'] += count
                    final_results[cat_name]['summaries'].append(summary)
                else:
                    final_results[cat_name] = {
                        'total_count': count,
                        'summaries': [summary]
                    }
                    
        except Exception as e:
            print(f"เกิดข้อผิดพลาดใน Batch {current_batch_num}: {e}")

    # 4. เขียนข้อมูลสรุปสุดท้ายลงไฟล์ CSV
    print(f"กำลังบันทึกผลลัพธ์ลงไฟล์ {output_file}...")
    with open(output_file, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Summary (Combined)', 'Count'])

        for category, data in final_results.items():
            # รวมสรุปของแต่ละ Batch เข้าด้วยกัน (ลบสรุปที่ซ้ำกันออกเพื่อความสะอาด)
            unique_summaries = list(set(data['summaries']))
            combined_summary = " | ".join(unique_summaries)
            
            writer.writerow([category, combined_summary, data['total_count']])

    print(f"\nวิเคราะห์เสร็จสิ้น! บันทึกไฟล์เรียบร้อยแล้ว")

if __name__ == "__main__":
    comments = [
    "กาแฟหอมมาก บาริสต้าแนะนำดีสุดๆ",
    "ร้านตกแต่งสวย ถ่ายรูปได้ทุกมุมเลย",
    "เค้กอร่อยเกินคาด โดยเฉพาะชีสเค้ก",
    "ราคาแรงไปนิด แต่บรรยากาศดีมาก",
    "มุมทำงานเงียบดี เหมาะนั่งยาว",
    "แอร์เย็น เพลงเพราะ นั่งเพลิน",
    "ชาไทยหวานไปหน่อยสำหรับเรา",
    "พนักงานบริการเร็ว ประทับใจ",
    "ที่จอดรถน้อย หาที่จอดยาก",
    "กาแฟเข้มดี คนชอบคั่วเข้มน่าจะถูกใจ",
    "วิวริมกระจกตอนเย็นสวยมาก",
    "ขนมหมดเร็ว ไปบ่ายๆแทบไม่เหลือ",
    "ร้านเล็กแต่บรรยากาศอบอุ่น",
    "มัทฉะเข้มข้นดี ไม่หวานเกิน",
    "โต๊ะนั่งค่อนข้างชิดกัน เสียงดังนิดนึง",
    "Wi-Fi เร็วดี เอามานั่งทำงานได้สบาย",
    "ครัวซองต์หอมเนยมาก อร่อยจริง",
    "เครื่องดื่มหน้าตาดี แต่รสชาติธรรมดา",
    "คาเฟ่สไตล์มินิมอล ถ่ายรูปขึ้นมาก",
    "พนักงานพูดจาดี ยิ้มแย้มตลอด",
    "คนเยอะมากช่วงวันหยุด รอคิวนาน",
    "Americano ดีมาก ดื่มง่ายไม่เปรี้ยว",
    "ราคากับปริมาณยังไม่ค่อยสมกัน",
    "ร้านสะอาด ห้องน้ำโอเค",
    "ชอบกลิ่นกาแฟตั้งแต่เดินเข้าร้าน",
    "เมนูมีให้เลือกเยอะดี ทั้งกาแฟและไม่กาแฟ",
    "เพลงในร้านดังไปหน่อย คุยกันลำบาก",
    "ชาเขียวลาเต้อร่อยกว่าที่คิด",
    "ถ่ายรูปออกมาสวยทุกมุม แสงดีมาก",
    "ขนมหวานหวานไปนิด แต่กาแฟดี",
    "พนักงานลืมออเดอร์ ต้องตามหลายรอบ",
    "ร้านเปิดเช้า เหมาะกับแวะก่อนทำงาน",
    "มุม outdoor ดี แต่ช่วงบ่ายร้อนมาก",
    "Signature coffee แปลกดี น่าลอง",
    "ราคาโอเคเมื่อเทียบกับโลเคชัน",
    "เค้กช็อกโกแลตเข้มข้นมาก ถูกใจสายหวาน",
    "ร้านเงียบสงบ เหมาะอ่านหนังสือ",
    "ที่นั่งมีปลั๊กไฟหลายจุด สะดวกมาก",
    "น้ำส้มกาแฟ surprisingly เข้ากันดี",
    "บรรยากาศเหมือนคาเฟ่เกาหลีเลย",
    "Latte art สวยมากจนไม่กล้าดื่ม",
    "ทางเข้าร้านแอบหายากนิดนึง",
    "เครื่องดื่มได้ช้าช่วงคนเยอะ",
    "ขนมปังปิ้งอร่อยเกินคาดมาก",
    "ร้านนี้ถ่ายฟิล์มออกมาสวยสุดๆ",
    "พนักงานดูเหนื่อยๆ แต่ยังบริการโอเค",
    "กาแฟติดเปรี้ยว ไม่ค่อยถูกปากเรา",
    "ราคาไม่แพงอย่างที่คิด",
    "มีมุมถ่ายรูปเยอะ เหมาะสายคอนเทนต์",
    "โดยรวมดี ไว้จะกลับมาอีกแน่นอน"
]
    analyze_and_export_csv(comments)
