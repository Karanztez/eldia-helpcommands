# Eldia HelpCommands (`endstone-eldia-helpcommands`)

ปลั๊กอินรวมคำสั่งพื้นฐานสำหรับเซิร์ฟเวอร์ Minecraft Bedrock (Endstone) รองรับระบบจุดเกิดหลักข้ามโลก (`/setspawn`, `/spawn`, `/hub`) ระบบบ้านส่วนตัว 3 หลังพร้อมหน้าต่างเมนู GUI (`/sethome`, `/home`) ระบบจุดวาร์ปข้ามโลกสำหรับแอดมิน (`/setwarp`, `/warp`) และระบบป้องกันการวาร์ปหนีขณะต่อสู้หรือทำกิจกรรม (Combat & Active Event Guard) รองรับการทำงานร่วมกับ `eldia-worlds` เต็มรูปแบบ

---

## ฟีเจอร์หลัก (Overview)

1. **ระบบ Spawn หลัก & เตียงนอน (`/setspawn`, `/spawn`, `/hub`)**
   - ใช้ `/setspawn` ในโลกไหน โลกและมิตินั้นจะกลายเป็นจุดเกิดหลัก (Main Server Spawn) ของเซิร์ฟเวอร์ทันที (รองรับโลกจาก `eldia-worlds`)
   - เมื่อผู้เล่นเสียชีวิต จะกลับมาเกิดใหม่ที่จุด Spawn หลักของเซิร์ฟเวอร์เสมอ **ยกเว้น** ผู้เล่นได้กดบันทึกเตียงนอนไว้ จะเกิดที่เตียงนอนของตัวเอง (หากเตียงถูกทุบทำลาย ระบบจะส่งกลับไปเกิดที่จุด Spawn หลักอัตโนมัติ)
   - เมื่อพิมพ์ `/spawn` หรือ `/hub` จะวาร์ปกลับไปยังจุด Spawn หลักเสมอ
2. **ระบบบ้าน 3 หลัง พร้อมหน้าต่าง GUI (`/sethome 1-3`, `/home 1-3`, `/home`)**
   - ผู้เล่นทุกคนสามารถบันทึกบ้านได้สูงสุด **3 หลัง** (`1`, `2`, `3`) ข้ามโลกได้
   - พิมพ์ `/home` (หรือ `/home gui`) เพื่อเปิดหน้าต่างเมนู **Home GUI** สำหรับกดวาร์ป บันทึกทับ หรือลบบ้านทั้ง 3 หลังได้ในคลิกเดียว
3. **ระบบวาร์ปข้ามโลก (`/setwarp`, `/warp`)**
   - `/setwarp <ชื่อ>` และ `/delwarp <ชื่อ>` รองรับการเซ็ตจุดวาร์ปข้ามโลกและข้ามมิติของ `eldia-worlds`
   - คำสั่ง `/warp <ชื่อ>` (หรือ `/warp` เพื่อเปิดเมนู GUI) **สงวนสิทธิ์ให้เฉพาะ OP เท่านั้น** หากผู้เล่นทั่วไปที่ไม่มี OP พิมพ์ `/warp` ระบบจะแจ้งเตือนให้ใช้ `/home` หรือ `/spawn` แทน
4. **ระบบป้องกันการวาร์ปขณะต่อสู้และทำกิจกรรม (Combat & Event Guard)**
   - ห้ามใช้คำสั่งเคลื่อนย้ายทุกชนิด (`/spawn`, `/hub`, `/home`, `/sethome`, `/warp`) ขณะติดสถานะต่อสู้ (Combat Tag ทั้งผู้โจมตีและผู้ถูกโจมตี รวมถึงธนู/โปรเจกไทล์)
   - ห้ามวาร์ปขณะตัวละครเสียชีวิต ขณะนอนบนเตียง ขณะอยู่ในลาวา/กำลังร่อน หรือขณะติดสถานะกิจกรรม (`in_event`, `arena`, `duel`, `minigame` หรือ `/ehc eventlock`)
5. **รองรับภาษาไทย (`th`) และภาษาอังกฤษ (`en`)**
   - ตั้งค่าภาษาเริ่มต้นเป็นภาษาไทย (`language: th`) ใน `config.yml` พร้อมข้อความแจ้งเตือนภายใต้แท็ก `[EHC]`

---

## คำสั่งการใช้งาน (Commands)

### คำสั่งสำหรับผู้เล่นทั่วไป
| คำสั่ง | คำอธิบาย |
| :--- | :--- |
| `/spawn` หรือ `/hub` | วาร์ปกลับไปยังจุด Spawn หลักของเซิร์ฟเวอร์ |
| `/home` หรือ `/home gui` | เปิดหน้าต่างเมนู GUI จัดการและวาร์ปบ้านทั้ง 3 หลัง |
| `/home <1\|2\|3>` | วาร์ปไปยังบ้านหลังที่ `1`, `2` หรือ `3` ทันที |
| `/sethome <1\|2\|3>` | บันทึกตำแหน่งปัจจุบันเป็นบ้านหลังที่ `1`, `2` หรือ `3` |
| `/delhome <1\|2\|3>` | ลบบ้านหลังที่ `1`, `2` หรือ `3` |

### คำสั่งสำหรับแอดมิน (เฉพาะ OP)
| คำสั่ง | คำอธิบาย |
| :--- | :--- |
| `/setspawn` | กำหนดตำแหน่งและโลกปัจจุบันเป็นจุด Spawn หลักของเซิร์ฟเวอร์ |
| `/setwarp <ชื่อ>` | สร้างจุดวาร์ปข้ามโลก ณ ตำแหน่งและโลกปัจจุบัน |
| `/delwarp <ชื่อ>` | ลบจุดวาร์ปที่ระบุ |
| `/warp` หรือ `/warp <ชื่อ>` | เปิดหน้าต่าง GUI รายการวาร์ป หรือวาร์ปไปยังจุดที่ระบุ (เฉพาะ OP) |
| `/ehc reload` | รีโหลดไฟล์ตั้งค่า `config.yml` |
| `/ehc lang <th\|en>` | เปลี่ยนภาษาข้อความแจ้งเตือน (`th` หรือ `en`) |
| `/ehc eventlock <ผู้เล่น> <on\|off> [เหตุผล]` | ล็อกหรือปลดล็อกไม่ให้ผู้เล่นใช้คำสั่งวาร์ปขณะอยู่ในกิจกรรม |
| `/ehc status` | แสดงสถานะการตั้งค่าปัจจุบันของปลั๊กอิน |

---

## การตั้งค่า (`plugins/eldia_helpcommands/config.yml`)

```yaml
# Language: "th" (Thai) or "en" (English)
language: th

# Chat message prefix
prefix: "[EHC]"

# Combat tag duration in seconds after dealing or taking damage
combat_tag_seconds: 15.0

# Cooldown in seconds after an active event / interaction lock
event_cooldown_seconds: 3.0

# Cooldown in seconds between teleport commands (/spawn, /home, /warp)
teleport_cooldown_seconds: 3.0

# Maximum number of home slots per player (1, 2, 3)
max_homes: 3

# Tag players in combat on any damage (including mobs/fall/hazards), not only PvP
tag_all_damage: true

# If true, only player-vs-player damage activates combat lock
pvp_only: false

# Block teleport commands while in lava or gliding hazard
block_in_hazard: true
```

---

## การติดตั้ง (Installation)

```bash
pip install endstone-eldia-helpcommands
```

หรือนำไฟล์ `.whl` ไปวางในโฟลเดอร์ `plugins/` ของเซิร์ฟเวอร์ Endstone แล้วรีสตาร์ทเซิร์ฟเวอร์
