"""Localization table for Eldia HelpCommands (Thai `th` and English `en`)."""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "th": {
        "no_permission": "§cคุณไม่มีสิทธิ์ใช้งานคำสั่งนี้ (เฉพาะ OP เท่านั้น)",
        "warp_op_only": "§cคำสั่ง /warp สงวนไว้สำหรับ OP เท่านั้น ผู้เล่นทั่วไปกรุณาใช้ §e/home §cหรือ §e/spawn",
        "combat_blocked": "§cไม่สามารถวาร์ปหรือใช้คำสั่งเคลื่อนย้ายได้ขณะกำลังต่อสู้! (รออีก {seconds} วินาที)",
        "combat_tagged": "§cคุณเข้าสู่สถานะต่อสู้ ห้ามใช้คำสั่งวาร์ปเป็นเวลา {seconds} วินาที",
        "combat_Cancelled_move": "§cยกเลิกการวาร์ปเนื่องจากมีการเคลื่อนที่หรือต่อสู้",
        "event_blocked": "§cไม่สามารถวาร์ปได้ขณะกำลังทำกิจกรรมหรือติดสถานะพิเศษ ({reason})",
        "dead_blocked": "§cไม่สามารถใช้คำสั่งวาร์ปขณะตัวละครเสียชีวิตได้",
        "sleeping_blocked": "§cไม่สามารถใช้คำสั่งวาร์ปขณะกำลังนอนบนเตียงได้",
        "hazard_blocked": "§cไม่สามารถใช้คำสั่งวาร์ปขณะอยู่ในลาวาหรือกำลังร่อนกลางอากาศได้",
        "cooldown_blocked": "§cกรุณารออีก {seconds} วินาที ก่อนใช้คำสั่งวาร์ปอีกครั้ง",
        "spawn_not_set": "§cยังไม่ได้กำหนดจุด Spawn หลักของเซิร์ฟเวอร์ (OP ใช้ /setspawn)",
        "spawn_set": "§aกำหนดจุด Spawn หลักของเซิร์ฟเวอร์ที่โลก §e{world} §7({dimension}) §fพิกัด ({x}, {y}, {z}) เรียบร้อยแล้ว",
        "spawn_teleported": "§aวาร์ปกลับมายังจุด Spawn หลัก (§e{world}§a) เรียบร้อยแล้ว",
        "respawn_at_bed": "§aคุณเกิดใหม่ที่เตียงนอนของคุณในโลก §e{world}",
        "respawn_bed_missing": "§eเตียงนอนของคุณถูกทำลายหรือไม่พบระบบจึงส่งคุณกลับไปยังจุด Spawn หลัก (§f{world}§e)",
        "respawn_at_spawn": "§aคุณเกิดใหม่ที่จุด Spawn หลักของเซิร์ฟเวอร์ (§e{world}§a)",
        "bed_saved": "§aบันทึกจุดเกิดเตียงนอนของคุณที่โลก §e{world} §f({x}, {y}, {z}) เรียบร้อยแล้ว",
        "home_invalid_slot": "§cกรุณาระบุหมายเลขบ้าน 1, 2 หรือ 3 เท่านั้น (ตัวอย่าง: /sethome 1 หรือ /home 1)",
        "home_set": "§aบันทึกบ้านหลังที่ §e{slot} §aในโลก §e{world} §f({x}, {y}, {z}) เรียบร้อยแล้ว",
        "home_deleted": "§aลบบ้านหลังที่ §e{slot} §aเรียบร้อยแล้ว",
        "home_not_set": "§cคุณยังไม่ได้บันทึกบ้านหลังที่ §e{slot} §c(ใช้ /sethome {slot} เพื่อบันทึก)",
        "home_teleported": "§aวาร์ปไปยังบ้านหลังที่ §e{slot} §aในโลก §e{world} §aเรียบร้อยแล้ว",
        "home_list_header": "§6=== รายการบ้านของคุณ (สูงสุด 3 หลัง) ===",
        "home_list_entry_set": "§eบ้าน {slot}: §a{world} §7({dimension}) §f[{x}, {y}, {z}]",
        "home_list_entry_empty": "§eบ้าน {slot}: §7(ยังไม่ได้บันทึก - ใช้ /sethome {slot})",
        "home_gui_title": "ระบบจัดการบ้าน (Home 1 - 3)",
        "home_gui_content": "เลือกบ้านที่ต้องการวาร์ป หรือบันทึกทับตำแหน่งปัจจุบัน:",
        "home_gui_btn_tp": "วาร์ปไป บ้าน {slot} [{world}] ({x}, {y}, {z})",
        "home_gui_btn_empty": "บ้าน {slot} (ว่าง - กดเพื่อบันทึกจุดนี้)",
        "home_gui_btn_set": "บันทึกทับ บ้าน {slot} ณ จุดปัจจุบัน",
        "home_gui_btn_del": "ลบ บ้าน {slot}",
        "warp_invalid_name": "§cชื่อจุดวาร์ปไม่ถูกต้อง (ใช้ตัวอักษร a-z, 0-9, _, - ความยาว 1-32 ตัวอักษร)",
        "warp_usage_set": "§cการใช้งาน: /setwarp <ชื่อจุดวาร์ป>",
        "warp_usage_del": "§cการใช้งาน: /delwarp <ชื่อจุดวาร์ป>",
        "warp_set": "§aกำหนดจุดวาร์ป §e{name} §aที่โลก §e{world} §7({dimension}) §f({x}, {y}, {z}) เรียบร้อยแล้ว",
        "warp_deleted": "§aลบจุดวาร์ป §e{name} §aเรียบร้อยแล้ว",
        "warp_not_found": "§cไม่พบจุดวาร์ปชื่อ §e{name}",
        "warp_teleported": "§aวาร์ปไปยัง §e{name} §a(โลก §f{world}§a) เรียบร้อยแล้ว",
        "warp_empty": "§eยังไม่มีจุดวาร์ปที่ถูกตั้งค่าไว้ในเซิร์ฟเวอร์ (ใช้ /setwarp <ชื่อ>)",
        "warp_list_header": "§6=== รายการจุดวาร์ปทั้งหมด ({count}) ===",
        "warp_list_entry": "§e- {name}: §a{world} §7({dimension}) §f[{x}, {y}, {z}]",
        "warp_gui_title": "รายการจุดวาร์ป (เฉพาะ OP)",
        "warp_gui_content": "เลือกจุดวาร์ปข้ามโลกที่ต้องการเดินทาง:",
        "warp_gui_btn": "{name} [{world}] ({x}, {y}, {z})",
        "world_not_loaded": "§cไม่พบมิติหรือโลกปลายทาง ({world} / {dimension}) บนเซิร์ฟเวอร์",
        "config_reloaded": "§aรีโหลดการตั้งค่า Eldia HelpCommands เรียบร้อยแล้ว (ภาษา: {lang})",
        "lang_changed": "§aเปลี่ยนภาษาข้อความเป็น §e{lang} §aเรียบร้อยแล้ว",
        "lang_invalid": "§cรองรับเฉพาะภาษา th หรือ en เท่านั้น (/ehc lang <th|en>)",
        "eventlock_set": "§aตั้งค่าสถานะล็อกกิจกรรมของ §e{player} §aเป็น §f{state} §7({reason})",
        "status_info": "§aสถานะ: ภาษา={lang}, ต่อสู้={combat_sec}s, บ้านสูงสุด=3, จุดวาร์ป={warps}, สปาวหลัก={spawn}",
    },
    "en": {
        "no_permission": "§cYou do not have permission to use this command (OP only).",
        "warp_op_only": "§cThe /warp command is restricted to OP only. Please use §e/home §cor §e/spawn §cinstead.",
        "combat_blocked": "§cYou cannot teleport while in combat! ({seconds}s remaining)",
        "combat_tagged": "§cYou are now in combat! Teleport commands are disabled for {seconds}s.",
        "combat_Cancelled_move": "§cTeleport cancelled due to movement or combat.",
        "event_blocked": "§cYou cannot teleport while participating in an active event ({reason}).",
        "dead_blocked": "§cYou cannot use teleport commands while dead.",
        "sleeping_blocked": "§cYou cannot use teleport commands while sleeping in a bed.",
        "hazard_blocked": "§cYou cannot teleport while in lava or gliding.",
        "cooldown_blocked": "§cPlease wait {seconds}s before using another teleport command.",
        "spawn_not_set": "§cMain server spawn has not been set yet (OP: use /setspawn).",
        "spawn_set": "§aMain server spawn set in world §e{world} §7({dimension}) §fat ({x}, {y}, {z}).",
        "spawn_teleported": "§aTeleported to main server spawn (§e{world}§a).",
        "respawn_at_bed": "§aRespawned at your saved bed in world §e{world}§a.",
        "respawn_bed_missing": "§eYour bed was missing or obstructed; respawned at main server spawn (§f{world}§e).",
        "respawn_at_spawn": "§aRespawned at main server spawn (§e{world}§a).",
        "bed_saved": "§aBed respawn location saved in world §e{world} §f({x}, {y}, {z}).",
        "home_invalid_slot": "§cPlease specify a valid home number: 1, 2, or 3 (e.g. /sethome 1 or /home 1).",
        "home_set": "§aHome §e#{slot} §asaved in world §e{world} §fat ({x}, {y}, {z}).",
        "home_deleted": "§aHome §e#{slot} §adeleted.",
        "home_not_set": "§cHome §e#{slot} §cis not set yet (use /sethome {slot}).",
        "home_teleported": "§aTeleported to Home §e#{slot} §ain world §e{world}§a.",
        "home_list_header": "§6=== Your Homes (Max 3) ===",
        "home_list_entry_set": "§eHome {slot}: §a{world} §7({dimension}) §f[{x}, {y}, {z}]",
        "home_list_entry_empty": "§eHome {slot}: §7(Empty - use /sethome {slot})",
        "home_gui_title": "Home Menu (Slots 1 - 3)",
        "home_gui_content": "Select a home slot to teleport or overwrite:",
        "home_gui_btn_tp": "Teleport Home {slot} [{world}] ({x}, {y}, {z})",
        "home_gui_btn_empty": "Home {slot} (Empty - Tap to Save Here)",
        "home_gui_btn_set": "Overwrite Home {slot} at Current Position",
        "home_gui_btn_del": "Delete Home {slot}",
        "warp_invalid_name": "§cInvalid warp name (use a-z, 0-9, _, - up to 32 chars).",
        "warp_usage_set": "§cUsage: /setwarp <name>",
        "warp_usage_del": "§cUsage: /delwarp <name>",
        "warp_set": "§aWarp §e{name} §aset in world §e{world} §7({dimension}) §fat ({x}, {y}, {z}).",
        "warp_deleted": "§aWarp §e{name} §adeleted.",
        "warp_not_found": "§cWarp §e{name} §cnot found.",
        "warp_teleported": "§aTeleported to warp §e{name} §a(world §f{world}§a).",
        "warp_empty": "§eNo warps have been created yet (use /setwarp <name>).",
        "warp_list_header": "§6=== Server Warps ({count}) ===",
        "warp_list_entry": "§e- {name}: §a{world} §7({dimension}) §f[{x}, {y}, {z}]",
        "warp_gui_title": "Server Warps (OP Only)",
        "warp_gui_content": "Select a warp destination:",
        "warp_gui_btn": "{name} [{world}] ({x}, {y}, {z})",
        "world_not_loaded": "§cTarget world or dimension ({world} / {dimension}) is not available.",
        "config_reloaded": "§aEldia HelpCommands configuration reloaded (lang: {lang}).",
        "lang_changed": "§aLanguage changed to §e{lang}§a.",
        "lang_invalid": "§cSupported languages are th and en (/ehc lang <th|en>).",
        "eventlock_set": "§aSet event lock for §e{player} §ato §f{state} §7({reason}).",
        "status_info": "§aStatus: lang={lang}, combat={combat_sec}s, max_homes=3, warps={warps}, main_spawn={spawn}",
    },
}


class LangManager:
    """Formats localized chat and GUI strings with prefix."""

    def __init__(self, language: str = "th", prefix: str = "[EHC]") -> None:
        self.language = language if language in MESSAGES else "th"
        self.prefix = prefix

    def set_language(self, language: str) -> bool:
        norm = language.strip().lower()
        if norm not in MESSAGES:
            return False
        self.language = norm
        return True

    def raw(self, key: str, **kwargs: object) -> str:
        """Return localized text without chat prefix (used for GUI titles/buttons)."""
        table = MESSAGES.get(self.language, MESSAGES["th"])
        template = table.get(key) or MESSAGES["en"].get(key) or key
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError:
                return template
        return template

    def msg(self, key: str, **kwargs: object) -> str:
        """Return localized chat message with `[EHC]` prefix."""
        body = self.raw(key, **kwargs)
        return f"§b{self.prefix} §r{body}"
