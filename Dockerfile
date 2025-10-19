# 1. เลือก Python เวอร์ชั่นที่ต้องการเป็นพื้นฐาน
FROM python:3.11-slim

# 2. ติดตั้ง Dependencies ที่จำเป็นบน Linux (เพิ่ม 'locales')
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    locales \
    && rm -rf /var/lib/apt/lists/*

# 3. สร้างและตั้งค่า Locale ภาษาไทย
RUN sed -i -e 's/# th_TH.UTF-8 UTF-8/th_TH.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

# 4. ตั้งค่า Environment Variables ให้ทั้งระบบใช้ภาษาไทยเป็นหลัก
ENV LANG th_TH.UTF-8
ENV LANGUAGE th_TH:en
ENV LC_ALL th_TH.UTF-8

# 5. ตั้งค่า Working Directory
WORKDIR /app

# 6. คัดลอกไฟล์ requirements.txt
COPY requirements.txt requirements.txt

# 7. ติดตั้ง Libraries ของ Python
RUN pip install --no-cache-dir -r requirements.txt

# 8. คัดลอกไฟล์โปรเจคทั้งหมด
COPY . .

# 9. บอกว่าแอปทำงานที่ Port 5000
EXPOSE 5000

# 10. คำสั่งสำหรับรันแอป
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]