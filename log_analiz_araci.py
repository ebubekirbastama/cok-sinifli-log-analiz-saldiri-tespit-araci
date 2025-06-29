import re
import urllib.parse
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import requests
import csv

# ----------- ÖN İŞLEM: Log satırını temizle, decode et ve normalize et -----------

def temizle_ve_normalize_et(log_satiri):
    decoded = urllib.parse.unquote(log_satiri)
    cleaned = re.sub(r'/\*.*?\*/', '', decoded)  # /* ... */ yorumları kaldır
    cleaned = re.sub(r'//.*', '', cleaned)       # // ile başlayan yorum satırı kaldır
    cleaned = re.sub(r'\s+', ' ', cleaned)       # fazla boşlukları tek boşluk yap
    normalized = cleaned.lower().strip()
    return normalized

# ------------------ EĞİTİM VERİSİ DOSYADAN OKU ------------------

def egitim_verisi_oku(dosya_yolu):
    loglar = []
    etiketler = []
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            for satir in f:
                if not satir.strip():
                    continue
                if '\t' not in satir:
                    continue
                log, etiket = satir.strip().split('\t', 1)
                loglar.append(temizle_ve_normalize_et(log))
                etiketler.append(etiket)
    except Exception as e:
        messagebox.showerror("Hata", f"Eğitim verisi okunurken hata: {e}")
        exit()
    return loglar, etiketler

# ------------------ MODEL EĞİT VE KAYDET ------------------

def egitim_yap_ve_kaydet(dosya_yolu):
    loglar, etiketler = egitim_verisi_oku(dosya_yolu)
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(loglar)
    model = MultinomialNB()
    model.fit(X, etiketler)
    joblib.dump(model, "saldiri_modeli.pkl")
    joblib.dump(vectorizer, "vektorizer.pkl")

# ------------------ MODEL VE VEKTORIZER YÜKLE ------------------

def model_ve_vektor_yukle():
    try:
        model = joblib.load("saldiri_modeli.pkl")
        vectorizer = joblib.load("vektorizer.pkl")
        return model, vectorizer
    except Exception as e:
        messagebox.showerror("Hata", f"Model veya vektörizer dosyası yüklenemedi:\n{e}")
        exit()

# ------------------ IP ADRESİ ÇEKME ------------------

ip_regex = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

def ip_adresi_cek(log_satiri):
    match = ip_regex.search(log_satiri)
    return match.group(0) if match else "Bulunamadı"

# ------------------ SALDIRI TESPİT (ÇOK SINIFLI) ------------------

def log_analiz_et(satir, model, vectorizer):
    temizlenmis = temizle_ve_normalize_et(satir)
    X_new = vectorizer.transform([temizlenmis])
    tahmin = model.predict(X_new)[0]
    if tahmin == "normal":
        return "NORMAL", "-"
    else:
        return "TEHDİT", tahmin.replace("_", " ").capitalize()

# ------------------ IP BİLGİ ÇEKME & CACHE ------------------

ip_bilgi_cache = {}

def ip_bilgisi_getir(ip):
    if ip in ip_bilgi_cache:
        return ip_bilgi_cache[ip]
    try:
        cevap = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,proxy,mobile,hosting,message", timeout=5)
        data = cevap.json()
        if data["status"] == "success":
            bilgi = (
                f"Ülke: {data.get('country','-')}\n"
                f"Bölge: {data.get('regionName','-')}\n"
                f"Şehir: {data.get('city','-')}\n"
                f"ISP: {data.get('isp','-')}\n"
                f"Proxy: {'Evet' if data.get('proxy',False) else 'Hayır'}\n"
                f"Mobil Ağ: {'Evet' if data.get('mobile',False) else 'Hayır'}\n"
                f"Hosting: {'Evet' if data.get('hosting',False) else 'Hayır'}"
            )
        else:
            bilgi = f"Hata: {data.get('message','Bilinmeyen hata')}"
    except Exception as e:
        bilgi = f"API Hatası: {str(e)}"
    ip_bilgi_cache[ip] = bilgi
    return bilgi

# ------------------ TOOLTIP SINIFI ------------------

class CreateToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.widget.bind("<Motion>", self.motion)
        self.widget.bind("<Leave>", self.hide_tip)

    def motion(self, event):
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            rowid = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            if rowid and col == "#2":  # IP sütunu
                ip = tree.set(rowid, "IP Adresi")
                if ip and ip != "Bulunamadı":
                    self.show_tip(ip, event.x_root + 20, event.y_root + 10)
                else:
                    self.hide_tip()
            else:
                self.hide_tip()
        else:
            self.hide_tip()

    def show_tip(self, ip, x, y):
        if self.tipwindow:
            return
        bilgi = ip_bilgisi_getir(ip)
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=bilgi, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Consolas", 10))
        label.pack(ipadx=5, ipady=5)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# ------------------ GLOBAL ANALİZ SONUÇ LİSTESİ ------------------

analiz_sonuc_listesi = []

# ------------------ DOSYA ANALİZ ------------------

def dosya_analiz_et(dosya_yolu, model, vectorizer):
    try:
        with open(dosya_yolu, "r", encoding="utf-8", errors="ignore") as dosya:
            satirlar = dosya.readlines()
    except Exception as e:
        messagebox.showerror("Dosya Hatası", f"Dosya okunurken hata oluştu:\n{e}")
        return

    analiz_sonuc_listesi.clear()
    tree.delete(*tree.get_children())
    progress_var.set(0)
    progress_bar.update()

    toplam_satir = len(satirlar)

    for i, satir in enumerate(satirlar, 1):
        durum, tur = log_analiz_et(satir, model, vectorizer)
        ip = ip_adresi_cek(satir)
        analiz_sonuc_listesi.append({"Durum": durum, "IP": ip, "Tur": tur, "Log": satir.strip()})

        renk = "red" if durum == "TEHDİT" else "green"
        tree.insert("", "end", values=(durum, ip, tur, satir.strip()), tags=(renk,))
        progress_var.set(i / toplam_satir * 100)
        progress_bar.update()

    progress_var.set(100)
    progress_bar.update()
    messagebox.showinfo("Analiz Tamamlandı", f"{toplam_satir} satır analiz edildi.")

# ------------------ FILTRELEME ------------------

def filtrele(*args):
    filtre = arama_var.get().lower()
    tree.delete(*tree.get_children())

    for item in analiz_sonuc_listesi:
        if (filtre in item["Durum"].lower() or
            filtre in item["IP"] or
            filtre in item["Tur"].lower() or
            filtre in item["Log"].lower()):
            renk = "red" if item["Durum"] == "TEHDİT" else "green"
            tree.insert("", "end", values=(item["Durum"], item["IP"], item["Tur"], item["Log"]), tags=(renk,))

# ------------------ CSV DIŞA AKTAR ------------------

def disari_aktar():
    if not analiz_sonuc_listesi:
        messagebox.showwarning("Uyarı", "Dışa aktarılacak analiz sonucu yok!")
        return

    dosya_yolu = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Dosyası", "*.csv")],
        title="CSV Dosyası Olarak Kaydet"
    )
    if dosya_yolu:
        try:
            with open(dosya_yolu, mode='w', newline='', encoding='utf-8') as csvfile:
                alanlar = ["Durum", "IP", "Tur", "Log"]
                writer = csv.DictWriter(csvfile, fieldnames=alanlar)
                writer.writeheader()
                for satir in analiz_sonuc_listesi:
                    writer.writerow(satir)
            messagebox.showinfo("Başarılı", f"Analiz sonuçları {dosya_yolu} dosyasına kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilirken hata oluştu:\n{e}")

# ------------------ DOSYA SEÇ VE ANALİZ THREAD ------------------

def dosya_sec_ve_analiz():
    dosya_yolu = filedialog.askopenfilename(
        title="Log Dosyasını Seçin",
        filetypes=[("Log Dosyaları", "*.log *.txt"), ("Tüm Dosyalar", "*.*")]
    )
    if dosya_yolu:
        threading.Thread(target=dosya_analiz_et, args=(dosya_yolu, model, vectorizer), daemon=True).start()

# ------------------ ANA PROGRAM ------------------

# Burada "egitim_verisi.txt" adında eğitim verisi dosyan olacak.
# İçeriği şöyle olmalı: her satırda "log satırı TAB etiket"
# Örnek: GET / HTTP/1.1 Googlebot	normal

egitim_verisi_dosyasi = "egitim_verisi.txt"

egitim_yap_ve_kaydet(egitim_verisi_dosyasi)
model, vectorizer = model_ve_vektor_yukle()

pencere = tk.Tk()
pencere.title("Gelişmiş Çok Sınıflı Log Analiz ve Saldırı Tespit Aracı")
pencere.geometry("1100x700")
pencere.resizable(True, True)

stil = ttk.Style(pencere)
stil.theme_use("clam")
stil.configure("Treeview",
                background="white",
                foreground="black",
                rowheight=25,
                fieldbackground="white",
                font=("Consolas", 10))
stil.map('Treeview', background=[('selected', '#347083')])
stil.configure("TButton", font=("Arial", 12), padding=6)

arama_var = tk.StringVar()
arama_var.trace_add("write", filtrele)

arama_entry = ttk.Entry(pencere, textvariable=arama_var, font=("Arial", 12))
arama_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
arama_entry.insert(0, "Arama yap...")

btn_disari = ttk.Button(pencere, text="CSV Olarak Dışa Aktar", command=disari_aktar)
btn_disari.grid(row=0, column=1, sticky="ew", padx=10, pady=8)

btn_sec = ttk.Button(pencere, text="Log Dosyası Seç ve Analiz Et", command=dosya_sec_ve_analiz)
btn_sec.grid(row=0, column=2, sticky="ew", padx=10, pady=8)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(pencere, variable=progress_var, maximum=100)
progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10)

columns = ("Durum", "IP Adresi", "Saldırı Türü", "Log Satırı")
tree = ttk.Treeview(pencere, columns=columns, show="headings", selectmode="browse")
for col in columns:
    tree.heading(col, text=col)
    if col == "Durum":
        tree.column(col, width=100, anchor="center")
    elif col == "IP Adresi":
        tree.column(col, width=130, anchor="center")
    elif col == "Saldırı Türü":
        tree.column(col, width=180, anchor="center")
    else:
        tree.column(col, width=600, anchor="w")

tree.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10)

scrollbar = ttk.Scrollbar(pencere, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.grid(row=2, column=3, sticky="ns")

tree.tag_configure('red', foreground='red')
tree.tag_configure('green', foreground='green')

pencere.grid_rowconfigure(2, weight=1)
pencere.grid_columnconfigure(0, weight=1)
pencere.grid_columnconfigure(1, weight=0)
pencere.grid_columnconfigure(2, weight=0)

CreateToolTip(tree)

pencere.mainloop()
