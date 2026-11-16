# Tpadterrain

ข้อมูลความสูงภูมิประเทศ (Terrarium PNG) สำหรับชั้น TAWS และกราฟความสูงใน [Tpad Helicopter Planner](https://ow3652.github.io/Tpadhelicopterplanner/)
สร้างจาก Copernicus DEM GLO-30 ด้วย GitHub Actions แล้วเผยแพร่ที่ `https://ow3652.github.io/Tpadterrain/terrarium/{z}/{x}/{y}.png`

## สร้าง/อัปเดตข้อมูล
1. Settings → Pages → Source = **GitHub Actions** (ตั้งครั้งเดียว)
2. แท็บ **Actions** → **Build terrain tiles** → **Run workflow** (ใช้ค่าเริ่มต้นได้)
3. รอจนเสร็จ (ดาวน์โหลดและสร้างราว 30–90 นาที) ผลและขนาดดูได้ในหน้าสรุปของการรัน

แผ่นข้อมูลไม่ถูกเก็บในประวัติ git (อัปโหลดเป็นไฟล์ของหน้าเว็บโดยตรง) รีโปจึงเล็ก ถ้ารันใหม่ หน้าเว็บจะถูกแทนที่ด้วยชุดใหม่

## รายละเอียด
- ซูม 11 (~74 ม./พิกเซล) ทุกแผ่นบนบกในกรอบ 5.5–20.6N, 97.2–105.8E
- ซูม 12 (~37 ม./พิกเซล) เฉพาะใต้แผ่นซูม 11 ที่สูงสุด ≥ `thr` เมตร (ค่าเริ่มต้น 300)
- ซูม 5–10 ย่อจากซูม 11 ด้วยค่าสูงสุด 2×2 (ยอดเขาไม่หาย) ย่อจากต้นฉบับก็ใช้ค่าสูงสุด เผื่อไว้ฝั่งปลอดภัย
- ความสูงเป็นเมตรเต็ม `R*256 + G + B/256 - 32768` (B = 0) แผ่นที่ไม่มีคือทะเล/ไม่มีข้อมูล
- `coverage.json`: กรอบ ช่วงซูม รายชื่อแผ่นซูม 11 ที่มีซูม 12 (`z12parents`) จำนวนแผ่น
- เพดาน GitHub Pages 1 GB: การรันจะหยุดถ้าเกิน 950 MB ให้รันใหม่โดยเพิ่ม `thr`

## ข้อควรระวัง
Copernicus DEM เป็นแบบจำลองพื้นผิว (DSM) รวมต้นไม้และสิ่งก่อสร้างบางส่วน ไม่รวมเสา/สายไฟ ข้อมูลช่วง 2011–2015 ใช้ประกอบการวางแผนเท่านั้น ไม่ใช่ข้อมูลที่ผ่านการรับรองสำหรับการเดินอากาศ

## ที่มาและสัญญาอนุญาต
Copernicus DEM GLO-30 ใช้ได้ฟรีตามเงื่อนไขใบอนุญาตของ Copernicus (ESA) เข้าถึงผ่าน AWS Open Data (`copernicus-dem-30m`)

produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved
