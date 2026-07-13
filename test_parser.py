"""Test the log parser to verify it can parse the log format"""
import re
import sys
sys.path.insert(0, '.')

from app.services.log_parser import parse_log_line

# Test with actual lines from the log file
test_lines = [
    "05-02 12:45:04.534   852   697 E libc  : abort message: \"sh: can't execute: No such file or directory\"",
    "05-02 12:45:16.500   852   721 I chatty  :Expiry log because 75% rate limit",
    "01-15 10:30:45.123  1234  5678 E AndroidRuntime: FATAL EXCEPTION: main",
    "E/testtag: Simple error message",
]

for line in test_lines:
    result = parse_log_line(line)
    print(f"Line: {line[:60]}...")
    if result:
        print(f"  Level: {result['level']}, Tag: {result['tag']}, Message: {result['message'][:40]}...")
    else:
        print(f"  PARSE FAILED")
    print()
