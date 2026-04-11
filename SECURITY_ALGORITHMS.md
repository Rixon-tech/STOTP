# 🛡️ Security Algorithms & Standards: A Beginner's Guide

Welcome to the security heart of SmartLock Elite. This guide explains the complex "math and rules" (algorithms and standards) used to keep this system secure, presented in a way that is easy to understand if you are just starting out.

---

## 🏗️ The Layered Defense Strategy
Think of security not as a single door, but as a series of obstacles. If a burglar gets through one, the next one stops them. In this project, we use four main "obstacles":

1.  **Confidentiality**: Scrambling data so only we can read it.
2.  **Integrity**: Setting up "traps" to know if someone changed our messages.
3.  **Authentication**: Proving you are who you say you are.
4.  **Availability**: Making sure the lock works even without internet.

---

## 1. AES (Advanced Encryption Standard)
### *The Digital Vault*
AES is the gold standard for encrypting data. We use the **256-bit** version, which is so strong that even the world's most powerful supercomputers would take trillions of years to crack it.

*   **AES-256-GCM (The "Smart" Lock)**: We use this for the database.
    *   **Analogy**: It's like a vault that not only hides your gold but also has a "tamper seal." If someone even scrapes the paint on the vault, the system knows and rejects the key.
    *   **The "GCM" Part**: It provides "Authenticated Encryption," meaning it checks if the data was messed with *before* it tries to decrypt it.
*   **AES-256-ECB (The "Basic" Lock)**: We use this in the firmware.
    *   **Analogy**: A traditional lock. It's fast and light, perfect for the tiny brain of the ESP32 chip. It hides our secrets well enough for hardware storage.

---

## 2. TOTP (Time-based One-Time Password)
### *The Key that Self-Destructs*
Ever used an app like Google Authenticator? That’s TOTP. It's based on **RFC 6238**, a global rulebook for temporary keys.

*   **How it works**: Both the server and your lock share a "secret code." They both look at the current time (the same clock) and do a math problem involving that secret and the time.
*   **The 30-Second Rule**: The answer to the math problem changes every 30 seconds.
*   **Analogy**: Imagine a secret handshake that changes every minute based on the position of the sun. Even if a spy records you doing the handshake, they can't use it 5 minutes later because the sun has moved.

---

## 3. HMAC-SHA256 (Hash-based Message Authentication)
### *The Digital Wax Seal*
When the server tells the lock "Open the Door," we must be sure a hacker hasn't sent a fake message.

*   **The Signature**: The server takes the command (e.g., "UNLOCK") and signs it with a secret key.
*   **The Timestamp**: We include the current time in the message.
*   **Analogy**: It’s like a king sending a letter with a wax seal that only the knight knows how to verify. If the letter is 2 days old, the knight ignores it (this prevents **Replay Attacks**, where a hacker records an "Open" command and tries to play it back later).

---

## 4. Bcrypt
### *The One-Way Recipe*
We never store your actual password. If we did, and a hacker stole our database, they would have everyone's password. Instead, we store a "Hash."

*   **The "Hash" Concept**: Hashing is a one-way street. You can turn "Password123" into "x7y9z...", but you can't turn "x7y9z..." back into "Password123."
*   **Analogy**: Think of a cake recipe. You can see the cake (the hash), but you can't "un-bake" it to get the original eggs and flour (the password).
*   **The "Salt"**: We add random "extra ingredients" to your password before hashing it. This makes sure that even if two people have the same password, their hashes look completely different.

---

## 5. NTP and RTC (Time Synchronization)
### *Keeping the Clocks in Sync*
Since our TOTP "key" depends on the time, the Server and the Hardware must agree on what time it is.

*   **NTP (Network Time Protocol)**: The lock asks a super-accurate atomic clock on the internet for the time.
*   **RTC (Real-Time Clock)**: A small battery-powered clock chip (DS3231) on the lock that keeps time even if the power goes out.
*   **Why it matters**: If the lock is 2 minutes fast, your TOTP code from your phone won't work!

---

## 📜 Summary for Beginners

| If you want to... | Use this standard... | Because... |
| :--- | :--- | :--- |
| **Hide Data** | **AES-256** | It's uncrackable by today's computers. |
| **Prove Identity** | **TOTP** | It creates a new, temporary key every 30 seconds. |
| **Secure Messages**| **HMAC-SHA256** | it proves the message is authentic and hasn't been replayed. |
| **Save Passwords** | **Bcrypt** | It turns passwords into irreversible "fingerprints." |
| **Handle Offline** | **RTC Sync** | It ensures the lock knows the time even without internet. |

---

## 🚀 Pro-Tip
Security is only as strong as its weakest link. In this project, we ensure that **Physical Security** (the lock), **Cloud Security** (The API), and **Network Security** (HMAC) all work together as one team.
