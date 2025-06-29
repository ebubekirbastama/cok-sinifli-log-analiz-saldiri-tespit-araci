
# 🚨 Çok Sınıflı Log Analiz ve Saldırı Tespit Aracı 🚨

Bu proje, çok sınıflı makine öğrenmesi modeli kullanarak log dosyalarındaki normal ve çeşitli saldırı türlerini tespit etmeyi sağlar. Python ve Tkinter kullanılarak geliştirilmiş, grafik arayüzü olan gelişmiş bir araçtır.

---

## ✨ Özellikler

- 🔍 Çok sınıflı Naive Bayes tabanlı saldırı tespiti
- 🧹 Log satırlarını ön işleme ile temizleme ve normalize etme
- 🌍 IP adreslerinden konum, ISP, proxy ve hosting bilgilerini API üzerinden çekme (cache destekli)
- 📂 Kolay ve hızlı dosya seçimi, çok sayıda log satırını hızlı analiz etme
- 🎨 Analiz sonuçlarını tablo görünümünde renkli olarak gösterme (tehdit kırmızı, normal yeşil)
- 🖱️ IP adresi üzerinde fare ile üzerine gelindiğinde detaylı bilgi gösterme (tooltip)
- 🔎 Arama ve filtreleme özelliği
- 💾 Analiz sonuçlarını CSV dosyası olarak dışa aktarabilme

---

## 🛠️ Gereksinimler

- Python 3.x
- Gerekli paketler:

pip install scikit-learn joblib requests

---

## 🚀 Kullanım

1. `egitim_verisi.txt` dosyasını hazırlayın. Her satırda analiz edilecek log satırı ve tab ile ayrılmış etiketi olmalıdır.

   Örnek satır:

   GET /index.html HTTP/1.1	normal
   POST /admin/login.php?_method=delete	komut_injection

2. Programı çalıştırın:

   python log_analiz_araci.py

3. Açılan arayüzde "Log Dosyası Seç ve Analiz Et" butonundan analiz yapmak istediğiniz log dosyasını seçin.

4. Loglar analiz edilip sonuçlar tabloya yansıtılacaktır.

5. Arama kutusunu kullanarak filtreleme yapabilir, "CSV Olarak Dışa Aktar" ile sonuçları kaydedebilirsiniz.

---

## 📝 Notlar

- Eğitim verisi dosyası proje ile aynı klasörde olmalıdır.
- IP bilgileri `ip-api.com` servisi kullanılarak çekilmektedir.
- Çok büyük dosyalar için analiz biraz zaman alabilir, arka planda çalışmaktadır.

---

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır.

