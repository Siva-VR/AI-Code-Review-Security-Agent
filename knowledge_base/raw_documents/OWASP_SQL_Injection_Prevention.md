# OWASP SQL Injection Prevention — Security Showcase

> The OWASP SQL Injection Prevention Cheat Sheet provides guidance for preventing SQL injection vulnerabilities in applications. It explains what SQL injection is, where vulnerabilities occur, and defensive options for protecting database queries.

## 1. Introduction

SQL injection is a serious application-security problem because:

1. SQL injection vulnerabilities are common.
2. Application databases are frequent targets because they often contain sensitive or critical information.

The goal of SQL injection prevention is to ensure that **user-supplied input cannot alter the intended SQL query**.

---

## 2. What Is a SQL Injection Attack?

An application can become vulnerable to SQL injection when it creates **dynamic database queries using string concatenation together with user-supplied input**.

To avoid SQL injection flaws, developers should:

1. Stop writing dynamic queries using string concatenation.
2. Prevent malicious SQL input from being included as executable SQL code.

These prevention techniques can be applied across practically any programming language and database technology.

Similar injection problems can also occur in XML databases, such as **XPath and XQuery injection**.

---

## 3. Anatomy of a Typical SQL Injection Vulnerability

A common Java vulnerability occurs when an unvalidated `customerName` parameter is directly appended to a SQL query.

### Vulnerable Example

```java
String query =
    "SELECT account_balance FROM user_data WHERE user_name = "
    + request.getParameter("customerName");

try {
    Statement statement = connection.createStatement();
    ResultSet results = statement.executeQuery(query);
}
```

### Why This Is Dangerous

The application combines:

- SQL code
- User-controlled input

into a single dynamically constructed query.

An attacker may provide SQL syntax as part of the input, causing the database to interpret the attacker-controlled content as SQL code.

### Core Problem

```text
User Input
    ↓
String Concatenation
    ↓
Dynamic SQL Query
    ↓
Database Interprets Input as SQL
```

---

# 4. Primary Defenses

The OWASP SQL Injection Prevention Cheat Sheet presents four main options:

| Option | Defense |
|---|---|
| **Option 1** | Prepared Statements with Parameterized Queries |
| **Option 2** | Properly Constructed Stored Procedures |
| **Option 3** | Allow-list Input Validation |
| **Option 4** | Escaping All User-Supplied Input — Strongly Discouraged |

---

## 5. Option 1 — Prepared Statements

### Parameterized Queries

Developers should use **prepared statements with variable binding**, also known as parameterized queries.

Prepared statements separate SQL code from user-supplied data.

The developer defines the SQL structure first and supplies parameter values separately.

### Why Prepared Statements Work

With parameterized queries, the database distinguishes between:

- **SQL code**
- **Data**

Therefore, even if an attacker supplies SQL commands as input, those commands are treated as data rather than changing the intended query.

### Security Model

```text
SQL Structure
     +
User Parameter
     ↓
Prepared Statement
     ↓
Database Separates Code from Data
     ↓
SQL Injection Prevented
```

---

## 6. Safe Java Prepared Statement Example

A safe Java implementation uses `PreparedStatement`:

```java
// This should REALLY be validated too
String custname = request.getParameter("customerName");

// Perform input validation to detect attacks
String query =
    "SELECT account_balance FROM user_data WHERE user_name = ?";

PreparedStatement pstmt =
    connection.prepareStatement(query);

pstmt.setString(1, custname);

ResultSet results = pstmt.executeQuery();
```

### Important Point

The user value is supplied through:

```java
pstmt.setString(1, custname);
```

instead of being concatenated directly into the SQL statement.

If an attacker enters:

```text
tom' or '1'='1
```

the parameterized query treats the entire value as a username value rather than executable SQL.

---

## 7. Safe C# .NET Prepared Statement Example

The supplied OWASP material also demonstrates parameterized queries in .NET:

```csharp
String query =
    "SELECT account_balance FROM user_data WHERE user_name = ?";

try
{
    OleDbCommand command =
        new OleDbCommand(query, connection);

    command.Parameters.Add(
        new OleDbParameter(
            "customerName",
            CustomerNameName.Text
        )
    );

    OleDbDataReader reader =
        command.ExecuteReader();
}
```

The parameter is supplied separately through the command's parameter collection.

---

## 8. Option 2 — Properly Constructed Stored Procedures

**Stored procedures** can be used as another SQL injection defense when they are properly constructed.

The key security requirement is that stored procedures must not reintroduce unsafe dynamic SQL construction.

### Security Principle

```text
Application
    ↓
Properly Constructed Stored Procedure
    ↓
Database
```

The stored procedure should maintain the separation between SQL code and user-supplied data.

---

## 9. Option 3 — Allow-list Input Validation

**Allow-list input validation** can be used to restrict input to values that are explicitly permitted.

For example, an application may define an expected set of valid values rather than accepting arbitrary input.

### Security Principle

```text
User Input
    ↓
Allow-list Validation
    ↓
Valid Input?
   ↙     ↘
 Yes      No
 ↓        ↓
Process   Reject
```

The supplied material identifies allow-list validation as one of the primary SQL injection defenses.

---

## 10. Option 4 — Escaping User-Supplied Input

The fourth option is explicitly described as:

> **STRONGLY DISCOURAGED: Escaping All User Supplied Input**

Escaping user input should not be treated as the primary defense against SQL injection.

The preferred approach is to use **prepared statements / parameterized queries**, together with appropriate input validation.

---

# 11. Defense Comparison

| Defense | Recommendation |
|---|---|
| Prepared Statements | **Preferred primary defense** |
| Properly Constructed Stored Procedures | Appropriate when safely implemented |
| Allow-list Input Validation | Useful additional defense |
| Escaping All User Input | **Strongly discouraged as the primary defense** |

---

# 12. Secure vs. Insecure Query Construction

### ❌ Insecure

```java
String query =
    "SELECT account_balance FROM user_data WHERE user_name = "
    + request.getParameter("customerName");
```

**Problem:** User input is directly concatenated into SQL.

### ✅ Secure

```java
String query =
    "SELECT account_balance FROM user_data WHERE user_name = ?";

PreparedStatement pstmt =
    connection.prepareStatement(query);

pstmt.setString(1, custname);
```

**Advantage:** The SQL structure and user data are handled separately.

---

# 13. Secure Development Checklist

- [ ] Avoid dynamic SQL created through string concatenation.
- [ ] Use prepared statements with parameterized queries.
- [ ] Validate user input appropriately.
- [ ] Use allow-list validation where suitable.
- [ ] Construct stored procedures safely.
- [ ] Do not rely on escaping all user input as the main defense.
- [ ] Treat database input as untrusted until properly handled.
- [ ] Review database queries for injection risks.

---

# 14. SQL Injection Prevention Workflow

```text
User Input
    ↓
Input Validation
    ↓
Parameterized Query
    ↓
Prepared Statement
    ↓
Database
    ↓
Result
```

The most important principle is:

> **Keep SQL code separate from user-supplied data.**

---

# 15. Relevance to an AI Code Review & Security Analysis Project

The SQL Injection Prevention Cheat Sheet can be used as a security reference for an automated code-review system.

A security-analysis agent can detect patterns such as:

```java
"SELECT ... " + userInput
```

and identify them as potential SQL injection risks.

A remediation agent can then recommend a parameterized query:

```java
"SELECT ... WHERE column = ?"
```

followed by parameter binding.

### Example Analysis Flow

```text
Source Code
    ↓
Code Analysis Agent
    ↓
Detect Dynamic SQL / String Concatenation
    ↓
Security Vulnerability Agent
    ↓
SQL Injection Classification
    ↓
OWASP-Based Recommendation
    ↓
Remediation Agent
    ↓
Secure Parameterized Query
```

---

# 16. Key Takeaways

- SQL injection occurs when untrusted input can modify the intended SQL query.
- Dynamic SQL created through string concatenation is a major source of SQL injection vulnerabilities.
- **Prepared statements with parameterized queries** are a primary defense.
- Parameterized queries separate SQL code from user-supplied data.
- Properly constructed stored procedures can provide another defense.
- Allow-list input validation can provide additional protection.
- Escaping all user input is **strongly discouraged** as the primary defense.
- Input should still be appropriately validated even when parameterized queries are used.

---

## References

- OWASP SQL Injection Prevention Cheat Sheet
- OWASP Web Application Security guidance
- OWASP Injection security guidance

---

### Source Note

This Markdown showcase was created from the supplied OWASP SQL Injection Prevention Cheat Sheet excerpt. It preserves the source's organization around the definition of SQL injection, the typical Java vulnerability, and the four primary defense options, with emphasis on prepared statements and parameterized queries.
