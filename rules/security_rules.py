import re

# SQL Injection patterns
SQL_PATTERNS = [
    r"SELECT\s+.*\+",
    r"INSERT\s+.*\+",
    r"UPDATE\s+.*\+",
    r"DELETE\s+.*\+",
]

# Hardcoded password
PASSWORD_PATTERNS = [
    r'password\s*=\s*["\'].*["\']',
    r'passwd\s*=\s*["\'].*["\']',
]

# Hardcoded API Key
API_KEY_PATTERNS = [
    r'api_key\s*=\s*["\'].*["\']',
    r'secret\s*=\s*["\'].*["\']',
]

# Dangerous functions
DANGEROUS_FUNCTIONS = [
    "eval(",
    "exec(",
]

# Dangerous subprocess
SUBPROCESS_PATTERN = r"subprocess\..*shell\s*=\s*True"

# Cross-site scripting patterns
XSS_PATTERNS = [
    r"print\(.*request\.",
    r"print\(.*input\(",
    r"out\.println\(.*getParameter\(",
    r"response\.getWriter\(\)\.write\(.*getParameter\(",
]

# Java command execution
JAVA_COMMAND_PATTERNS = [
    r"Runtime\.getRuntime\(\)\.exec",
    r"ProcessBuilder",
]