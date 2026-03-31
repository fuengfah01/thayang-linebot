import anthropic
import json
from places import places
from info import info
from food import food
from questions import questions

client = anthropic.Anthropic()

# ── สร้าง context สรุปข้อมูลท่ายางให้ AI รู้จัก ──────────────────────────────
def _build_context() -> str:
    place_names = ", ".join(places.keys())
    food_savory = ", ".join(food.get("อาหารคาว", {}).keys())
    food_sweet = ", ".join(food.get("ขนม/ของหวาน", {}).keys())
    q_topics = ", ".join(list(questions.keys())[:20])

    return f"""คุณคือ "น้องเพชร" ผู้ช่วยท่องเที่ยวอำเภอท่ายาง จังหวัดเพชรบุรี
ตอบเป็นภาษาไทย สั้นกระชับ เป็นกันเอง ใช้ emoji ประกอบเล็กน้อย
ห้ามตอบเรื่องนอกเหนือจากท่ายาง/เพชรบุรี ถ้าถามนอกเรื่องให้บอกว่าไม่ทราบข้อมูลนั้นค่ะ

== ข้อมูลที่รู้จัก ==
สถานที่: {place_names}
อาหารคาว: {food_savory}
ขนม/ของหวาน: {food_sweet}
คำถามที่ตอบได้: {q_topics}

ข้อมูลสำคัญ:
- ท่ายางอยู่ห่างจาก กทม. ~150 กม. ใช้เวลา ~2 ชม.
- ของขึ้นชื่อ: ขนมหม้อแกง น้ำตาลโตนด ทองม้วน ข้าวแช่
- วัดท่าคอยมีอุโบสถ 100 ปี และอุทยานปลา
- ตลาดสดเปิด 04:00-12:00
- โครงการชั่งหัวมันอยู่ในท่ายาง
"""

SYSTEM_PROMPT = _build_context()


def ask_ai(user_message: str) -> str:
    """
    ส่งคำถามอิสระไปให้ Claude ตอบในบริบทท่ายาง
    คืนค่าเป็น string ข้อความตอบกลับ
    """
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"[AI Helper Error] {e}")
        return "ขอโทษค่ะ น้องเพชรไม่สามารถตอบได้ตอนนี้ กรุณาลองใหม่อีกครั้งนะคะ 🙏"