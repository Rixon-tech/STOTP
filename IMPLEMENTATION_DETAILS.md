# 📂 Project Implementation Details: SmartLock Elite

This document provides a technical breakdown of the SmartLock Elite ecosystem, including module functionalities, architectural decisions, and the cryptographic algorithms employed across the stack.

---

## 🏗️ System Architecture Overview
The system utilizes a **Hybrid Authentication Gateway** model. It primarily operates via cloud-based validation but maintains high-security operational status during network outages through local hardware-level verification.

1.  **Backend (FastAPI)**: Serves as the central authority for OAuth identity, state management, and command orchestration.
2.  **Frontend (Vanilla SPA)**: Provides an enterprise-grade UI for user authentication and system auditing.
3.  **Hardware (ESP32)**: The physical execution layer, performing local TOTP validation and servo actuation.

---

## 💻 Backend Implementation

### **Core Functionalities**
- **Multi-Factor Orchestration**: Coordinates Google Sign-In, secondary password verification, and TOTP-based MFA.
- **Secure Heartbeat**: A background thread that pings the hardware every 5 seconds to announce server health, triggering the offline fallback if missed.
- **HMAC Command Signing**: Every manual unlock or system command is signed with SHA-256 to prevent replay attacks and unauthorized injection.
- **Security Monitoring**: Threshold-based tracking of failed login attempts with automatic security alerts.

### **Key Modules**
- `app/main.py`: The entry point managing FastAPI routes, middleware, and the heartbeat daemon.
- `app/security.py`: The central security provider for password hashing (Bcrypt) and payload encryption (AES-256-GCM).
- `app/auth_otp.py`: Manages the TOTP lifecycle, including QR code generation via `pyotp` and deep-drift synchronization logic.
- `app/audit_logs.py`: Handles event persistence in Google Cloud Firestore and historical log retrieval.

---

## 🌐 Frontend Implementation

### **Core Functionalities**
- **SPA View Management**: Uses a custom JavaScript routing system to switch between Landing, Authentication, and Manager dashboards without reloads.
- **Adaptive UI**: The interface dynamically changes based on the user's role (Manager vs. Employee) and authentication step.
- **Log Management Dashboard**: A high-fidelity interface for managers to review system access logs and export them to CSV/Excel formats.

### **Design Aesthetics**
- **Modern Typography**: Utilizes *Inter* for body text and *Outfit* for headings.
- **Premium Styling**: Implements linear gradients, glassmorphic card effects, and subtle CSS transitions for a high-end feel.
- **Component Based**: Built using semantic HTML5 and Vanilla CSS variables for easy theme management.

---

## 🔌 ESP32 Firmware Implementation

### **Core Functionalities**
- **Hybrid Failover**: Continuously monitors the backend heartbeat. If the heartbeat fails, the device automatically enters "Offline Mode" or "Fully Off Mode".
- **Hardware Time Sync**: Synchronizes the internal system clock from NTP when online; falls back to a hardware DS3231 RTC for timekeeping during offline TOTP validation.
- **Local OTP Entry**: Users can select their profile (1-5) and input their 6-digit MFA code directly via a 4x4 membrane keypad.
- **Real-time Feedback**: Logic for displaying system status, IP addresses, and access results on a 16x2 I2C LCD.

### **Key Libraries**
- `mbedtls`: Provides hardware-accelerated AES decryption for local secrets.
- `RTClib`: Interface for the high-precision DS3231 RTC.
- `ArduinoJson`: Used for parsing signed payloads from the backend.

---

## 🔐 Cryptographic Standards & Algorithms

| Layer | Algorithm / Standard | Implementation Purpose |
| :--- | :--- | :--- |
| **Data Encryption** | **AES-256-GCM** | Authenticated encryption for storage of TOTP secrets in Firestore. |
| **Password Security** | **Bcrypt** | One-way hashing with salt to protect system passwords. |
| **MFA Protocol** | **TOTP (SHA-1)** | 30-second window Time-based One Time Passwords (RFC 6238). |
| **Message Integrity** | **HMAC-SHA256** | Cryptographic signature for all backend-to-hardware commands. |
| **Local Protection** | **AES-256-ECB** | Hardcoded secrets in the ESP32 code are stored in encrypted format. |
| **Time Precision** | **NTP + RTC Sync** | Ensures hardware and server stay within the 30s TOTP drift window. |


---

## 🔬 In-Depth Algorithm Analysis

### **1. AES-256-GCM (Authenticated Encryption)**
- **Role**: Securing TOTP secrets in the Firestore database.
- **Mechanism**: Galois/Counter Mode (GCM) provides both confidentiality and data integrity (AEAD). 
- **Implementation**:
  - **Key**: Derived from the system `ENCRYPTION_KEY` using SHA-256.
  - **Nonce**: A unique 96-bit (12-byte) initialization vector is generated for every encryption event.
  - **Tag**: A 16-byte authentication tag is appended to the ciphertext to detect any tampering during storage.
- **Why GCM?**: Unlike ECB or CBC, it prevents bit-flipping attacks and ensures that the backend knows with absolute certainty that the secret has not been modified.

### **2. TOTP (Time-based One-Time Password - RFC 6238)**
- **Role**: Multi-factor authentication layer.
- **Mechanism**: 
  - Uses the **HMAC-SHA1** algorithm.
  - **Time Step**: 30 seconds. The "moving factor" is derived from the Unix epoch divided by 30.
- **Drift Compensation**: 
  - High-latency environments or hardware clock drift can cause verification failures.
  - The backend implements a **Deep Drift Search** algorithm: it iterates through +/- 240 seconds (8 time windows) to find a match if the initial check fails, ensuring user-friendly access even if the ESP32 clock is slightly out of sync.

### **3. HMAC-SHA256 (Hash-based Message Authentication Code)**
- **Role**: Secure command transmission between Server and Hardware.
- **Mechanism**: Combines a secret key (`DEVICE_SECRET`) with the message payload (`cmd:user:ts`) through the SHA-256 hashing function.
- **Security Utility**:
  - **Integrity**: Ensures the command (e.g., `OTP_GRANTED`) wasn't changed to something else.
  - **Authentication**: Proves the command came from the authorized server.
  - **Anti-Replay**: The inclusion of a timestamp (`ts`) allows the hardware to reject old, "replayed" commands if they are outside a valid time window (default 120s).

### **4. Bcrypt (Blowfish-based Password Hashing)**
- **Role**: Protecting administrator and manager passwords.
- **Mechanism**: An adaptive hashing function that incorporates a "Cost Factor" (Work Factor).
- **Features**:
  - **Salt**: Automatically generates and stores a unique salt for every password, rendering Rainbow Table attacks impossible.
  - **Work Factor**: Designed to be slow; it exponentially increases the computation required for brute-force attacks while remaining efficient for single verification events.

### **5. AES-256-ECB (Electronic Codebook)**
- **Role**: Obfuscating hardcoded secrets within the ESP32 firmware.
- **Mechanism**: Standard 256-bit block cipher without chaining.
- **Context**: While ECB is generally less secure than GCM/CBC for long messages due to pattern visibility, it is used here for its low memory footprint and high speed on the ESP32 mbedtls library, providing a significant upgrade over plain-text storage for fixed-length hex arrays.

---

## 🛠️ Performance & Benchmarking
The system has been benchmarked for cryptographic latency on the ESP32:
- **AES-256 Decryption**: < 1ms
- **SHA-256 HMAC Verification**: ~2ms
- **TOTP Generation**: < 1ms

*For a full visual analysis, refer to `esp scripts/crypto_analysis_results.png`.*
