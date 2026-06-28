import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import requests

# --- Sayfa Ayarları ---
st.set_page_config(page_title="YKS Takip", page_icon="🎓", layout="centered")

# --- 1. Firebase Bağlantıları ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["firebase_key"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()
WEB_API_KEY = st.secrets["firebase_web_api_key"]

# --- 2. Oturum (Session) Yönetimi ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# --- 3. Kimlik Doğrulama Fonksiyonları ---
def kayit_ol(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

def giris_yap(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

# --- 4. Arayüz (UI) Yönetimi ---
if st.session_state.user_id is None:
    # GİRİŞ EKRANI
    st.title("👋 YKS Takip Uygulamasına Hoş Geldiniz")
    st.write("Lütfen devam etmek için giriş yapın veya hesap oluşturun.")
    
    islem_secimi = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    
    email = st.text_input("E-posta adresi")
    password = st.text_input("Şifre", type="password")
    
    if islem_secimi == "Kayıt Ol":
        if st.button("Hesap Oluştur", type="primary"):
            sonuc = kayit_ol(email, password)
            if "error" in sonuc:
                st.error(f"Kayıt Hatası: {sonuc['error']['message']}")
            else:
                st.success("Hesabınız başarıyla oluşturuldu! Şimdi 'Giriş Yap' sekmesinden sisteme girebilirsiniz.")
                
    elif islem_secimi == "Giriş Yap":
        if st.button("Sisteme Gir", type="primary"):
            sonuc = giris_yap(email, password)
            if "error" in sonuc:
                st.error("Giriş başarısız! E-posta veya şifrenizi kontrol edin.")
            else:
                st.session_state.user_id = sonuc["localId"]
                st.rerun()

else:
    # ANA UYGULAMA (Giriş Yapıldıktan Sonraki Ekran)
    
    # Sağ üste çıkış butonu ekleyelim
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("🎓 YKS Takip Uygulaması")
    with col2:
        if st.button("Çıkış Yap"):
            st.session_state.user_id = None
            st.rerun()
            
    st.divider()

    # Kullanıcının veritabanındaki (Firestore) dosyasını çağırıyoruz
    kullanici_ref = db.collection("kullanicilar").document(st.session_state.user_id)
    kullanici_belgesi = kullanici_ref.get()

    # Eğer kullanıcının alanı (Sayısal, EA vb.) henüz seçilmemişse
    if not kullanici_belgesi.exists or "alan" not in kullanici_belgesi.to_dict():
        st.subheader("Hoş Geldin! 🎉 Başlamadan önce alanını seçmelisin:")
        secilen_alan = st.selectbox("Hangi alandan sınava gireceksin?", 
                                    ["Seçiniz...", "Sayısal", "Eşit Ağırlık", "Sözel", "Dil"])
        
        if st.button("Alanımı Kaydet", type="primary") and secilen_alan != "Seçiniz...":
            # Seçimi Firebase'e kaydediyoruz
            kullanici_ref.set({"alan": secilen_alan}, merge=True)
            st.success("Alan seçimin başarıyla kaydedildi!")
            st.rerun() # Sayfayı yeniliyoruz ki dersler gelsin
            
    else:
        # Eğer alan seçilmişse dersleri getiriyoruz
        kullanici_verisi = kullanici_belgesi.to_dict()
        kullanicinin_alani = kullanici_verisi["alan"]
        
        st.success(f"**{kullanicinin_alani}** alanı için derslerin listeleniyor.")
        
        # TYT (Herkes için ortak)
        tyt_dersleri = ["TYT Türkçe", "TYT Matematik", "TYT Tarih", "TYT Coğrafya", "TYT Felsefe", "TYT Din", "TYT Fizik", "TYT Kimya", "TYT Biyoloji"]
        
        # Alana göre AYT/YDT Dersleri
        ayt_dersleri = []
        if kullanicinin_alani == "Sayısal":
            ayt_dersleri = ["AYT Matematik", "AYT Fizik", "AYT Kimya", "AYT Biyoloji"]
        elif kullanicinin_alani == "Eşit Ağırlık":
            ayt_dersleri = ["AYT Matematik", "AYT Edebiyat", "AYT Tarih-1", "AYT Coğrafya-1"]
        elif kullanicinin_alani == "Sözel":
            ayt_dersleri = ["AYT Edebiyat", "AYT Tarih-1", "AYT Coğrafya-1", "AYT Tarih-2", "AYT Coğrafya-2", "AYT Felsefe Grubu"]
        elif kullanicinin_alani == "Dil":
            ayt_dersleri = ["YDT (Yabancı Dil Testi)"]

        # Arayüze Dersleri Çıktı Olarak Basıyoruz
        st.write("### 📚 TYT Dersleri")
        for ders in tyt_dersleri:
            st.markdown(f"- {ders}")
            
        st.write("### 🎯 AYT / YDT Dersleri")
        for ders in ayt_dersleri:
            st.markdown(f"- {ders}")