# Java Security — OWASP Showcase

> Security guidance and examples based on the supplied **OWASP Java Security Cheat Sheet** material.

## 1. Log Injection

### Symptom

Log Injection occurs when an application includes untrusted data in an application log message. An attacker may inject CRLF characters into untrusted data and create an additional log entry that appears to come from a different user.

### Prevention

Recommended defenses include:

- Use structured log formats such as **JSON** instead of unstructured text.
- Limit the size of user input used to create log messages.
- Apply XSS defenses when viewing log files in a web browser.
- Use parameterized logging instead of string concatenation.

### Example — Parameterized Logging

```java
logger.warn("Login failed for user {}.", username);
```

Avoid mixing string concatenation with logging parameters:

```java
logger.warn("Failure for user " + username + " and role {}.", role, ex);
```

### Log4j / Logback

The supplied material recommends structured JSON logging and limiting string lengths in production environments. It also provides examples using **Log4j Core** and **Logback**.

---

## 2. NoSQL Injection

The supplied material demonstrates using an API query builder with MongoDB rather than constructing database expressions directly from untrusted input.

Example approach:

```java
Bson expression = eq("borough", userInput);

FindIterable<org.bson.Document> restaurants =
    db.getCollection("restaurants").find(expression);
```

The example also verifies that returned data matches the expected value.

---

## 3. Cryptography

### General Guidance

- **Never write your own cryptographic functions.**
- Prefer established secret-management solutions where possible.
- If a cryptographic library is required, use a trusted and well-known implementation.
- Design applications so cryptographic algorithms can be changed in the future.
- Keep dependencies and development packages up to date.
- Use expert-reviewed libraries such as **Google Tink** where appropriate.

### Encryption for Storage

Follow the algorithm guidance provided by the OWASP Cryptographic Storage Cheat Sheet.

### AES-GCM Example

The supplied material demonstrates AES-GCM encryption using Java cryptographic APIs.

Important considerations include:

- Use a unique nonce for every encryption operation.
- A 12-byte / 96-bit nonce is used in the example.
- The encryption key must be stored securely.
- Key rotation and key management must be considered in a production design.

Example configuration from the supplied material:

```java
public static final String CIPHER_ALGORITHM = "AES/GCM/NoPadding";
public static final int KEY_SIZE = 256;
public static final int TAG_LENGTH = 128;
public static final int IV_LENGTH = 12;
```

---

## 4. Encryption for Transmission

The supplied material recommends following OWASP's cryptographic guidance for transmission and provides an example of hybrid/asymmetric encryption using Google Tink.

The example describes a scenario where two parties, such as Alice and Bob, exchange protected data using asymmetric key pairs.

---

## 5. Security Takeaways

| Area | Recommended Practice |
|---|---|
| Log Injection | Use structured logging and parameterized log messages |
| User Input | Validate and limit untrusted input |
| NoSQL Injection | Use safe API/query builders |
| Cryptography | Avoid custom cryptographic implementations |
| Encryption | Use trusted algorithms and libraries |
| Nonces | Use a unique nonce for every AES-GCM operation |
| Secrets | Store keys and secrets securely |
| Dependencies | Keep security-related packages updated |

## References

- OWASP Java Security Cheat Sheet
- OWASP Log Injection guidance
- OWASP Cryptographic Storage Cheat Sheet
- Google Tink documentation
- Log4j documentation
- Logback documentation

---

### Source Note

This showcase was generated from the uploaded source material and keeps its main topics: **Log Injection, NoSQL Injection, Cryptography, encryption for storage, and encryption for transmission**. fileciteturn0file0L5-L17
