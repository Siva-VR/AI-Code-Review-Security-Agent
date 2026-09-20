# OWASP Input Validation — Email Address Showcase

> Selected guidance from the OWASP **Input Validation Cheat Sheet** covering email ownership verification, disposable email addresses, and email sub-addressing.

## 1. Email Ownership Verification

When an application needs to prove that a user controls an email address, the ownership-verification link should contain a token with the following properties:

- **At least 32 characters long**
- **Generated using a secure source of randomness**
- **Single use**
- **Time limited**, for example, expiring after eight hours

After the email address has been successfully validated, the user should still be required to authenticate through the application's **usual authentication mechanism**.

### Recommended Token Properties

| Property | Requirement |
|---|---|
| Length | At least 32 characters |
| Randomness | Secure source of randomness |
| Usage | Single use |
| Expiration | Time limited |
| After verification | Require normal application authentication |

---

## 2. Disposable Email Addresses

Disposable email addresses are publicly available addresses that generally do not require users to authenticate. They are often used to reduce spam received by a user's primary email address.

### Challenges with Blocking Disposable Addresses

Blocking disposable email addresses is difficult because:

- Many websites provide disposable email services.
- New disposable-email domains can appear every day.
- Public and commercial lists of known disposable domains exist.
- These lists are always likely to be incomplete.

### If Blocking Is Required

If an application uses disposable-email-domain lists, the user should be shown a message explaining **why the address is blocked**.

If it is essential to prevent disposable email addresses, registrations should be restricted to **specifically allowed email providers**.

However, allowing public providers such as Google or Yahoo does not completely solve the problem because users may create additional disposable addresses through trusted providers.

### Security Consideration

There is therefore no simple, complete method for identifying and blocking every disposable email address.

---

## 3. Email Sub-Addressing

Sub-addressing allows users to add a tag to the local part of an email address, before the `@` symbol. The mail server may ignore this tag when delivering the message.

For example, if `example.org` supports sub-addressing:

```text
user@example.org
user+site1@example.org
user+site2@example.org
```

These addresses may be treated as equivalent by the mail server.

### Provider Support

Many mail providers do not support sub-addressing. The supplied OWASP material identifies **Gmail** as a notable provider that does, along with other providers.

### Why Users Use Sub-Addressing

Users may use a different tag for each website they register with.

For example:

```text
user+shopping@example.org
user+banking@example.org
user+social@example.org
```

This can help users identify which website may have leaked or sold their email address if they later receive spam at a particular sub-address.

---

## 4. Should Sub-Addressing Be Blocked?

Some websites may consider removing everything between the `+` and `@` characters so that multiple tagged addresses cannot be used to create multiple accounts.

For example:

```text
user+site1@example.org
        ↓
user@example.org
```

However, the supplied OWASP material **does not generally recommend this approach**.

Reasons include:

- It can indicate that the website is unaware of email sub-addressing.
- It may suggest that the website wants to prevent users from identifying where an email address was leaked or sold.
- It can be bypassed using disposable email addresses.
- Users can simply create multiple email accounts with a trusted provider.

---

## 5. Security Takeaways

| Area | Recommended Practice |
|---|---|
| Email verification tokens | Use tokens of at least 32 characters |
| Token generation | Use a secure source of randomness |
| Token usage | Make tokens single-use |
| Token lifetime | Make tokens time limited |
| Authentication | Require normal authentication after ownership verification |
| Disposable emails | Recognize that complete blocking is difficult |
| Domain lists | Understand that public/commercial lists are incomplete |
| Sub-addressing | Avoid automatically stripping `+` tags as a general rule |
| Account uniqueness | Do not rely only on removing sub-address tags |

---

## References

- **OWASP Top 10 Proactive Controls 2024:** C3 — Validate all Input & Handle Exceptions
- **CWE-20:** Improper Input Validation
- **OWASP Top 10 2021:** A03:2021 — Injection
- **Snyk:** Improper Input Validation
- **OWASP Input Validation Cheat Sheet**

### Source Note

This showcase was created from the supplied OWASP Input Validation Cheat Sheet excerpt. The source specifically covers email ownership-verification tokens, disposable email addresses, and sub-addressing. fileciteturn0file0L2-L13
