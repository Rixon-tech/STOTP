# 🛡️ SmartLock Elite: Hybrid Hybrid Authentication Gateway

### **Architecture: Enterprise Security with Hardware Resilience**

SmartLock Elite is a hybrid smart lock ecosystem designed for low-connectivity environments. It combines high-level **OAuth 2.0 (Google Identity)** and **Cloud Firestore** for online monitoring with a robust **AES-encrypted TOTP fallback** for true offline functionality.

---

## ⚡ **Key Features**
- **Hybrid Core**: Dynamically switches between **Online Mode** (REST API) and **Offline Mode** (Local Hardware Keypad + TOTP).
- **Server Heartbeat**: ESP32 continuously monitors the server’s health (every 5 seconds) to trigger the fallback mode.
- **Tri-Factor Auth**: 
  1. Google Single Sign-On (SSO).
  2. Enterprise Administrator Password.
  3. Time-Based One-Time Password (TOTP) MFA.
- **Hardware Security**:
  - **AES-128 Encryption**: Local TOTP secrets are stored encrypted (ECB) in the firmware.
  - **HMAC Signatures**: Every command between the portal and ESP32 is SHA-256 signed to prevent replay attacks.
- **Real-Time Auditing**: Detailed audit logs exported in CSV format, available to managers via a premium dashboard.

---

## 🏗️ **Technology Stack**
- **Microcontroller**: ESP32 (SDA/SCL on 21/22).
- **Firmware**: C++ (Arduino/ESP-IDF) with mbedtls (AES/HMAC).
- **Backend API**: Python (FastAPI).
- **Database**: Google Cloud Firestore.
- **Frontend UI**: Vanilla JS + CSS (Rich Premium Aesthetics).
- **MFA Protocol**: TOTP (SHA1, 30s step).

---

## 📂 **Project Structure**
```text
├── app/                  # FastAPI Backend (Python)
├── frontend/             # High-End Auth Portal (HTML/JS)
├── esp scripts/          # ESP32 hybrid.ino Firmware
├── tools/                # Encryption & Sync Utility Scripts
├── requirements.txt      # Python Dependencies
├── .env.example          # Template for Environment Variables
└── service_account.json  # (Excluded) Firebase credentials
```

---

## 🛠️ **Installation & Setup**

### **1. Hardware Setup**
- Connect your ESP32 to a **16x2 LCD** (I2C) and a **4x4 Keypad**.
- Servo control on **Pin 15**.
- Ensure both Server and ESP32 are on the same local subnet.

### **2. Cloud & Backend**
1. **Firebase**: Create a project and download `service_account.json`.
2. **Environment**: Copy `.env.example` to `.env` and configure your `DEVICE_SECRET` and `ESP_URL`.
3. **Run Server**:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### **3. ESP32 Firmware**
1. Open `esp scripts/hybrid.ino` in Arduino IDE.
2. If changing secrets, use `tools/encrypt_esp_secrets.py` to generate the AES-encrypted hex arrays.
3. Flash the device.

---
