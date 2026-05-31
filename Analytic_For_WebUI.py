import json
import ollama

PROMPT_FILE = "prompt.txt"

def analyze_with_progress(comment_list, progress_queue, batch_size=25, model="qwen2.5:latest"):
    """
    วิเคราะห์ comment แล้วส่ง progress event เข้า queue ระหว่างทาง
    Return: list ของ dict พร้อม render ใน UI
    """
    # ── โหลด system prompt จากไฟล์ ──────────────────────
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        base_prompt = f.read()

    system_instruction = f"""{base_prompt}
    ตอบกลับเป็น JSON เท่านั้น:
        {{ "groups": [ {{ "category": "ชื่อกลุ่มหลัก", "summary": "สรุปทิศทางและประเด็น", "count": จำนวน }} ] }}
        """

    # ── ตัวแปรสะสมผลลัพธ์ ────────────────────────────────
    final_results = {}  # { "ชื่อหมวดหมู่": { "total_count": int, "summaries": [str] } }
    total_batches = (len(comment_list) + batch_size - 1) // batch_size

    progress_queue.put({
        "type": "status",
        "message": f"เริ่มวิเคราะห์ {len(comment_list)} คอมเมนต์...",
    })

    # ── วนรันทีละ Batch ──────────────────────────────────
    for i in range(0, len(comment_list), batch_size):
        batch = comment_list[i : i + batch_size]
        batch_num = i // batch_size + 1

        progress_queue.put({
            "type": "progress",
            "message": f"วิเคราะห์ Batch {batch_num}/{total_batches}...",
            "percent": int((batch_num - 1) / total_batches * 80),  # 0–80%
        })

        existing_categories = list(final_results.keys())
        categories_str = (
            ", ".join(existing_categories)
            if existing_categories
            else "ยังไม่มี (เริ่มสร้างใหม่ได้เลย)"
        )

        user_prompt = f"""หมวดหมู่ที่มีอยู่แล้วในขณะนี้: [{categories_str}]

คอมเมนต์ที่ต้องวิเคราะห์ในชุดนี้:
{json.dumps(batch, ensure_ascii=False)}

จงวิเคราะห์และจัดกลุ่มคอมเมนต์ชุดนี้ตามกฎที่ให้ไว้ใน System Prompt"""

        try:
            response = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                format="json",
                options={"temperature": 0.1},
            )

            result_data = json.loads(response["message"]["content"])

            for group in result_data.get("groups", []):
                cat_name = group.get("category", "").strip()
                count    = group.get("count", 0)
                summary  = group.get("summary", "")

                if cat_name in final_results:
                    final_results[cat_name]["total_count"] += count
                    final_results[cat_name]["summaries"].append(summary)
                else:
                    final_results[cat_name] = {"total_count": count, "summaries": [summary]}

        except Exception as e:
            progress_queue.put({
                "type": "warning",
                "message": f"Batch {batch_num} มีปัญหา: {str(e)}",
            })

    # ── รวบรวมผลสุดท้าย ──────────────────────────────────
    progress_queue.put({
        "type": "status",
        "message": "กำลังรวบรวมผลลัพธ์...",
        "percent": 90,
    })

    output = []
    for category, data in final_results.items():
        unique_summaries = list(set(data["summaries"]))
        combined_summary = " | ".join(unique_summaries)
        output.append({
            "category": category,
            "summary":  combined_summary,
            "count":    data["total_count"],
        })

    output.sort(key=lambda x: x["count"], reverse=True)

    progress_queue.put({"type": "done", "percent": 100, "results": output})
    return output
