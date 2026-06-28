import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Sayfa ayarları
st.set_page_config(page_title="YKS Takip", page_icon="🎓", layout="centered")

# Firebase bağlantısı (Streamlit Secrets üzerinden okuma)
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # Streamlit ayarlarına gireceğimiz şifreli metni okuyoruz
        key_dict = json.loads(st.secrets["firebase_key"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Veritabanını çağırıyoruz
db = init_firebase()

# Arayüz Tasarımı
st.title("🎓 YKS Takip Uygulaması")
st.success("Harika! Firebase bağlantısı Streamlit Cloud üzerinden güvenle kuruldu. 🚀")
st.write("Veritabanı altyapımız hazır, artık üyelik sistemini kodlamaya geçebiliriz.")