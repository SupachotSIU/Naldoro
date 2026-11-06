# Naldoro

คลัง agent ของ Claude Code สำหรับงานคำนวณแผนประกัน (บริบทประเทศไทย)

## เริ่มใช้
เปิด repo นี้ด้วย Claude Code แล้วสั่งงานได้เลย เช่น

> ใช้ insurance-planner วางแผนให้ลูกค้า: ชาย 35 ปี เงินเดือน 80,000 มีลูก 2 คน ผ่อนบ้านเหลือ 2.5 ล้าน มีประกันชีวิตทุน 1 ล้าน

> ใช้ policy-analyst เทียบแบบสะสมทรัพย์ 2 แบบนี้ (แนบตารางผลประโยชน์) ที่ฐานภาษี 20%

agent ทั้งหมดอยู่ใน `.claude/agents/` และรายละเอียดอยู่ใน [`CLAUDE.md`](CLAUDE.md)

## เครื่องคำนวณ
agent ทุกตัวเรียกไลบรารี `naldoro_calc` (Python 3.10+ ไม่มี dependency) ซึ่งใช้เองได้:

```bash
python3 -m naldoro_calc needs examples/needs.json
python3 -m naldoro_calc tax examples/tax.json
python3 -m naldoro_calc compare examples/compare.json
python3 -m unittest discover -s tests
```

## ข้อจำกัดความรับผิดชอบ
ผลลัพธ์เป็นการประมาณการเพื่อการวางแผนเท่านั้น ไม่ใช่ใบเสนอราคาหรือคำแนะนำการลงทุน
ตรวจสอบเงื่อนไขกรมธรรม์กับบริษัทประกัน และสิทธิลดหย่อนกับกรมสรรพากรก่อนตัดสินใจทุกครั้ง
