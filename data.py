import streamlit as st
from cryptography.fernet import Fernet
import hashlib
import os

# Custom CSS for mobile responsiveness
st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stButton > button {
            width: 100%;
            margin: 5px 0;
        }
        .stTextInput > div > div > input {
            width: 100%;
        }
        .stTextArea > div > div > textarea {
            width: 100%;
        }
        .column {
            padding: 0 5px;
        }
    }
    .main .block-container {
        padding: 2rem 1rem;
    }
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------- Setup --------------------
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = True
if 'attempts' not in st.session_state:
    st.session_state.attempts = 0
if 'stored_data' not in st.session_state:
    st.session_state.stored_data = {}

# Load or generate encryption key
KEY_FILE = 'encryption_key.key'
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as key_file:
        fernet_key = key_file.read()
else:
    fernet_key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as key_file:
        key_file.write(fernet_key)

cipher_suite = Fernet(fernet_key)

# -------------------- Utility Functions --------------------
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

def encrypt_text(text):
    try:
        return cipher_suite.encrypt(text.encode()).decode()
    except Exception as e:
        st.error(f"Encryption failed: {str(e)}")
        return None

def decrypt_text(ciphertext):
    try:
        return cipher_suite.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        st.error(f"Decryption failed: {str(e)}")
        return None

def reset_auth():
    st.session_state.authenticated = False
    st.session_state.attempts = 0

# -------------------- Styled Pages --------------------
def home():
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>🔐 Secure Data Encryption</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1rem; margin-bottom: 2rem;'>Store and retrieve your sensitive data securely</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ Store Data", use_container_width=True, key="store_btn"):
            st.session_state.page = 'store'
    with col2:
        if st.button("🔓 Retrieve Data", use_container_width=True, key="retrieve_btn"):
            st.session_state.page = 'retrieve'

def store_data():
    st.markdown("### ➕ Store New Encrypted Data")
    st.markdown("---")
    
    with st.form("store_form"):
        user_key = st.text_input("🆔 Unique Identifier", placeholder="e.g., username or note title")
        text = st.text_area("📝 Enter text to encrypt", height=150)
        passkey = st.text_input("🔑 Enter secure passkey", type="password")
        submitted = st.form_submit_button("🔐 Store Securely", use_container_width=True)
        
        if submitted:
            if user_key and text and passkey:
                encrypted = encrypt_text(text)
                if encrypted:
                    hashed = hash_passkey(passkey)
                    st.session_state.stored_data[user_key] = {
                        "encrypted_text": encrypted,
                        "passkey": hashed
                    }
                    st.success(f"✅ Data for **'{user_key}'** stored securely!")
            else:
                st.warning("⚠️ Please fill in all fields.")

def retrieve_data():
    st.markdown("### 🔓 Retrieve Encrypted Data")
    st.markdown("---")
    
    if st.session_state.attempts >= 3:
        st.error("❌ Too many failed attempts. Please log in again to retry.")
        st.session_state.authenticated = False
        return
    
    with st.form("retrieve_form"):
        user_key = st.text_input("🆔 Enter your identifier", placeholder="Enter your unique identifier")
        passkey = st.text_input("🔑 Enter your passkey", type="password")
        submitted = st.form_submit_button("🔍 Retrieve", use_container_width=True)
        
        if submitted:
            if user_key in st.session_state.stored_data:
                hashed_input = hash_passkey(passkey)
                actual_hash = st.session_state.stored_data[user_key]["passkey"]
                
                if hashed_input == actual_hash:
                    encrypted = st.session_state.stored_data[user_key]["encrypted_text"]
                    decrypted = decrypt_text(encrypted)
                    if decrypted:
                        st.success("✅ Decryption Successful!")
                        with st.expander("📄 View Decrypted Data", expanded=True):
                            st.code(decrypted)
                        st.session_state.attempts = 0
                else:
                    st.session_state.attempts += 1
                    st.error(f"❌ Incorrect passkey. Attempts left: {3 - st.session_state.attempts}")
            else:
                st.error("⚠️ Identifier not found!")

def login_page():
    st.markdown("### 🔐 Reauthorization Required")
    st.info("You've reached the maximum allowed attempts. Please log in to continue.")
    
    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔑 Password", type="password")
        submitted = st.form_submit_button("🔓 Login", use_container_width=True)
        
        if submitted:
            if username == "admin" and password == "admin123":
                st.success("✅ Login successful.")
                st.session_state.authenticated = True
                st.session_state.attempts = 0
                st.session_state.page = 'home'
            else:
                st.error("❌ Invalid credentials.")

# -------------------- Navigation --------------------
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Mobile-friendly sidebar
with st.sidebar:
    st.markdown("## 🔧 Navigation")
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'home'
    if st.button("🔐 Logout", use_container_width=True):
        reset_auth()
        st.session_state.page = 'login'

# Route pages
if not st.session_state.authenticated:
    login_page()
else:
    if st.session_state.page == 'home':
        home()
    elif st.session_state.page == 'store':
        store_data()
    elif st.session_state.page == 'retrieve':
        retrieve_data()

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center; font-size:14px; padding: 1rem 0;'>Built with ❤️ using <b>Streamlit</b></div>", unsafe_allow_html=True)
