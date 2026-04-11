# 🎓 The Beginner's Guide to SmartLock Cryptography

Welcome! If you're new to cybersecurity, the terms "AES-256-GCM" or "HMAC-SHA256" might seem like alphabet soup. This guide breaks down exactly how SmartLock Elite protects your data, using simple analogies and technical depth.

---

## 🔑 1. Encryption vs. Hashing: The Golden Rule
Before we dive in, remember this:
- **Encryption** is a two-way street. You lock (encrypt) data so you can unlock (decrypt) it later using a key.
- **Hashing** is a one-way street. You turn data into a unique "fingerprint." You can't turn the fingerprint back into the original data.

---

## 🛡️ 2. Symmetric Encryption: AES-256
SmartLock Elite uses **AES (Advanced Encryption Standard)**. 
- **The Analogy**: Imagine a high-security physical safe. Both you and the person you're sending the safe to have the *exact same key*. 
- **"256-bit"**: This refers to the key length. A 256-bit key has $2^{256}$ combinations. To put that in perspective, there are more combinations than atoms in the observable universe. It is currently considered "unbreakable" by brute force.

### **In this Project:**
- **AES-256-GCM (Cloud Side)**: 
    - The **GCM** (Galois/Counter Mode) part is special. It doesn't just hide the data; it adds a "seal" (Authentication Tag). If someone changes even one bit of the encrypted data, the seal breaks, and the system rejects it. 
    - We use a **Nonce** (Number used Once). It’s a random code added to every encryption so that even if you encrypt the word "Secret" twice, the result looks completely different both times.
- **AES-256-ECB (Hardware Side)**: 
    - Used on the ESP32 to protect hardcoded secrets. It's faster for small bits of data on microcontrollers.

---

## 🕒 3. TOTP: The "Golden Ticket"
**TOTP** stands for **Time-based One-Time Password**. This is what apps like Google Authenticator use.

- **How it works**: 
    1. Both the server and your app share a secret code (The "Seed").
    2. They both look at the current time (rounded to the nearest 30 seconds).
    3. They combine the Secret + Time to create a 6-digit code.
- **Why it's secure**: Even if a hacker steals your 6-digit code, it expires in 30 seconds.

### **Advanced Concept: Drift Compensation**
Hardware clocks (like the one in an ESP32) aren't perfect—they can run a few seconds fast or slow. 
- **Our Solution**: If you enter a code and it fails, our server doesn't just give up. it checks the windows *before* and *after* the current time (up to 4 minutes) to see if your hardware clock just drifted. We call this **Deep Drift Search**.

---

## ✍️ 4. HMAC: The Digital Notary
**HMAC** (Hash-based Message Authentication Code) is used to sign commands.

- **The Problem**: If the server sends a message to the lock saying "UNLOCK", how does the lock know it's really the server and not a hacker?
- **The Solution**: 
    1. The server takes the command ("UNLOCK") + a Secret Key.
    2. It runs them through a hash function (SHA-256) to get a signature.
    3. The lock receives the command + the signature.
    4. The lock tries to create the same signature using its own copy of the Secret Key. If they match, the command is valid.

---

## 🧂 5. Bcrypt: Future-Proof Passwords
We use **Bcrypt** for management passwords.

- **Salting**: Every time you save a password, Bcrypt adds a random string called a "salt." This means if two people have the same password ("Password123"), their hashes in the database will look completely different.
- **Key Stretching**: Bcrypt is designed to be *intentionally slow*. It makes the computer do thousands of calculations before giving the result. This doesn't bother a human (it takes 0.1 seconds), but it makes it impossible for a hacker to try millions of guesses per second.

---

## 🚀 Summary Table for Beginners

| Term | What it is | Why it's cool |
| :--- | :--- | :--- |
| **Nonce** | Random number | Makes the same input look different every time. |
| **Salt** | Random password prefix | Stops hackers from using pre-computed "Rainbow Tables." |
| **SHA-256** | Secure Hashing | A way to turn any data into a fixed-size unique ID. |
| **mbedtls** | Library | The specific "toolbox" the ESP32 uses to do math. |

---

## 📖 Glossary
- **Ciphertext**: The "scrambled" data that comes out of encryption.
- **Plaintext**: The readable data you start with.
- **IV (Initialization Vector)**: Another word for a Nonce.
- **MFA/2FA**: Multi-Factor Authentication (Using more than just a password).

*This guide is part of the SmartLock Elite documentation suite. For implementation details, see `IMPLEMENTATION_DETAILS.md`.*
