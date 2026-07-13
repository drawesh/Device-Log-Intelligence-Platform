"""
Error Detection Module for Android logcat logs.

This module enhances the log parser to:
- Detect error patterns like "FATAL EXCEPTION", "ANR", "NullPointerException"
- Count frequency of each error
- Return summary report

Use clean modular Python code.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Error patterns to detect
ERROR_PATTERNS = [
    (r"FATAL EXCEPTION", "FATAL EXCEPTION"),
    (r"ANR", "ANR"),  # Application Not Responding
    (r"NullPointerException", "NullPointerException"),
    (r"IllegalStateException", "IllegalStateException"),
    (r"IllegalArgumentException", "IllegalArgumentException"),
    (r"RuntimeException", "RuntimeException"),
    (r"OutOfMemoryError", "OutOfMemoryError"),
    (r"StackOverflowError", "StackOverflowError"),
    (r"SecurityException", "SecurityException"),
    (r"IndexOutOfBoundsException", "IndexOutOfBoundsException"),
    (r"ClassCastException", "ClassCastException"),
    (r"NumberFormatException", "NumberFormatException"),
    (r"ParseException", "ParseException"),
    (r"ActivityNotFoundException", "ActivityNotFoundException"),
    (r"RuntimeException", "RuntimeException"),
    (r"Crash", "Crash"),
    (r"Force finishing", "Force finishing"),
    (r"Process.*has died", "Process died"),
    (r"binder.*transaction.*failed", "Binder transaction failed"),
    (r"Native crash", "Native crash"),
    (r"SIGSEGV", "Segmentation fault"),
    (r"SIGABRT", "Abort signal"),
    (r"Failed to write to", "File write error"),
    (r"Permission.*denied", "Permission denied"),
    (r"Connection.*refused", "Connection refused"),
    (r"Connection timed out", "Connection timeout"),
    (r"Network is unreachable", "Network unreachable"),
]

# Warning patterns to detect
WARNING_PATTERNS = [
    (r"slow", "Slow operation"),
    (r"timeout", "Timeout"),
    (r"leak", "Memory leak"),
    (r"deprecated", "Deprecated API"),
    (r"FATAL EXCEPTION", "FATAL EXCEPTION"),
    (r"W.*ActivityManager", "Activity manager warning"),
    (r"Skipped", "Frame skipped"),
    (r"dropped", "Frame dropped"),
    (r"GC.*slow", "GC slow"),
    (r"binder.*transaction.*full", "Binder transaction full"),
]


def detect_error_patterns(message: str) -> List[str]:
    """
    Detect error patterns in a log message.
    
    Args:
        message: Log message string
        
    Returns:
        List of detected error types
    """
    if not message:
        return []
    
    detected = []
    for pattern, error_type in ERROR_PATTERNS:
        try:
            if re.search(pattern, message, re.IGNORECASE):
                detected.append(error_type)
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
    
    return detected


def detect_warning_patterns(message: str) -> List[str]:
    """
    Detect warning patterns in a log message.
    
    Args:
        message: Log message string
        
    Returns:
        List of detected warning types
    """
    if not message:
        return []
    
    detected = []
    for pattern, warning_type in WARNING_PATTERNS:
        try:
            if re.search(pattern, message, re.IGNORECASE):
                detected.append(warning_type)
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
    
    return detected


def is_error_level(level: str) -> bool:
    """
    Check if log level is an error level.
    
    Args:
        level: Log level string
        
    Returns:
        True if error level, False otherwise
    """
    return level.upper() in ["E", "ERROR", "F", "FATAL"]


def is_warning_level(level: str) -> bool:
    """
    Check if log level is a warning level.
    
    Args:
        level: Log level string
        
    Returns:
        True if warning level, False otherwise
    """
    return level.upper() in ["W", "WARNING"]


def classify_error_severity(log: Dict[str, Any]) -> Optional[str]:
    """
    Classify an error-level log into a severity bucket.

    Returns None for non-error logs. Error severity buckets are mutually exclusive,
    so critical + high + medium equals the total number of error-level logs.
    """
    level = str(log.get("level", "")).upper()
    if not is_error_level(level):
        return None

    message = str(log.get("message", "")).lower()

    if (
        level == "FATAL"
        or "fatal exception" in message
        or re.search(r"\banr\b", message)
        or "outofmemory" in message
        or "stack overflow" in message
        or "stack overflowerror" in message
        or "native crash" in message
        or "sigsegv" in message
        or "sigabrt" in message
        or "system crash" in message
    ):
        return "critical"

    if (
        "exception" in message
        or "crash" in message
        or "failed" in message
        or "securityexception" in message
        or "nullpointerexception" in message
        or "illegalstateexception" in message
        or "runtimeexception" in message
        or "permission denied" in message
    ):
        return "high"

    return "medium"


def analyze_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze logs and generate summary report.
    
    Args:
        logs: List of parsed log dictionaries
        
    Returns:
        Summary report with total_logs, error_count, warning_count, top_errors
    """
    if not logs:
        return {
            "total_logs": 0,
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "debug_count": 0,
            "top_errors": [],
            "top_warnings": [],
            "errors": [],
            "warnings": [],
            "level_distribution": {}
        }
    
    # Count log levels
    level_counts = Counter()
    error_types_found = Counter()
    warning_types_found = Counter()
    
    errors = []
    warnings = []
    
    for log in logs:
        level = log.get("level", "UNKNOWN")
        message = log.get("message", "")
        
        # Count by level
        level_counts[level.upper()] += 1
        
        # Check level-based errors/warnings
        if is_error_level(level):
            detected = detect_error_patterns(message)
            for error_type in detected:
                error_types_found[error_type] += 1
                errors.append({
                    "error_type": error_type,
                    "message": message[:500],  # Truncate long messages
                    "timestamp": log.get("timestamp"),
                    "tag": log.get("tag")
                })
        
        elif is_warning_level(level):
            detected = detect_warning_patterns(message)
            for warning_type in detected:
                warning_types_found[warning_type] += 1
                warnings.append({
                    "warning_type": warning_type,
                    "message": message[:500],
                    "timestamp": log.get("timestamp"),
                    "tag": log.get("tag")
                })
    
    # Get top errors
    top_errors = [
        {"error_type": error_type, "count": count}
        for error_type, count in error_types_found.most_common(10)
    ]
    
    # Get top warnings
    top_warnings = [
        {"warning_type": warning_type, "count": count}
        for warning_type, count in warning_types_found.most_common(10)
    ]
    
    return {
        "total_logs": len(logs),
        "error_count": level_counts["ERROR"] + level_counts["FATAL"],
        "warning_count": level_counts["WARNING"],
        "info_count": level_counts["INFO"],
        "debug_count": level_counts["DEBUG"],
        "top_errors": top_errors,
        "top_warnings": top_warnings,
        "errors": errors[:50],  # Limit errors in response
        "warnings": warnings[:50],  # Limit warnings in response
        "level_distribution": dict(level_counts)
    }


def generate_summary_report(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary report for the logs.
    
    Args:
        logs: List of parsed log dictionaries
        
    Returns:
        Summary report dictionary
    """
    analysis = analyze_logs(logs)
    level_counts = analysis["level_distribution"]
    total_logs = analysis["total_logs"]
    error_count = analysis["error_count"]
    warning_count = analysis["warning_count"]
    severity_counts = Counter(
        severity for severity in (classify_error_severity(log) for log in logs)
        if severity
    )
    health_score = 100
    if total_logs > 0:
        health_score = max(0, 100 - (error_count * 0.5) - (warning_count * 0.2))
    
    severity_stats = {
        "critical": severity_counts["critical"],
        "high": severity_counts["high"],
        "medium": severity_counts["medium"],
    }
    
    # Get level distribution
    level_distribution = [
        {"level": level, "count": count}
        for level, count in level_counts.items()
    ]
    
    # Get top tags (by frequency)
    tag_counts = Counter()
    for log in logs:
        tag = log.get("tag", "")
        if tag:
            tag_counts[tag] += 1
    
    top_tags = [
        {"tag": tag, "count": count}
        for tag, count in tag_counts.most_common(15)
    ]
    
    # Get top messages (by frequency)
    message_counts = Counter()
    for log in logs:
        message = log.get("message", "")[:150]  # Truncate for grouping
        if message:
            message_counts[message] += 1
    
    top_messages = [
        {"message": message, "count": count}
        for message, count in message_counts.most_common(15)
    ]
    
    return {
        "total_logs": total_logs,
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": analysis["info_count"],
        "debug_count": analysis["debug_count"],
        "health_score": round(health_score, 1),
        "severity_stats": severity_stats,
        "top_errors": analysis["top_errors"],
        "level_distribution": level_distribution,
        "top_tags": top_tags,
        "top_messages": top_messages,
        "info": {
            "total_logs": analysis["total_logs"],
            "info_count": analysis["info_count"],
            "debug_count": analysis["debug_count"]
        }
    }


def get_error_frequency(logs: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get frequency of each error type.
    
    Args:
        logs: List of parsed log dictionaries
        
    Returns:
        Dictionary of error types and their counts
    """
    error_types = Counter()
    
    for log in logs:
        if is_error_level(log.get("level", "")):
            message = log.get("message", "")
            detected = detect_error_patterns(message)
            for error_type in detected:
                error_types[error_type] += 1
    
    return dict(error_types)


def get_critical_errors(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get only critical errors from logs.
    
    Args:
        logs: List of parsed log dictionaries
        
    Returns:
        List of critical error logs
    """
    critical_errors = []
    
    for log in logs:
        level = log.get("level", "").upper()
        message = log.get("message", "")
        
        if classify_error_severity(log) == "critical":
            critical_errors.append(log)
    
    return critical_errors


# Test function
def test_error_detector():
    """
    Test the error detector with sample data.
    """
    sample_logs = [
        {
            "timestamp": "2024-01-15 10:30:45.123",
            "level": "E",
            "tag": "AndroidRuntime",
            "message": "FATAL EXCEPTION: main"
        },
        {
            "timestamp": "2024-01-15 10:30:45.234",
            "level": "E",
            "tag": "AndroidRuntime",
            "message": "java.lang.NullPointerException at com.example.app.MainActivity.onCreate"
        },
        {
            "timestamp": "2024-01-15 10:30:45.345",
            "level": "W",
            "tag": "ActivityManager",
            "message": "Activity pause timeout"
        },
        {
            "timestamp": "2024-01-15 10:30:46.123",
            "level": "I",
            "tag": "ActivityManager",
            "message": "Starting activity"
        }
    ]
    
    summary = generate_summary_report(sample_logs)
    print("Summary Report:")
    print(f"Total logs: {summary['total_logs']}")
    print(f"Error count: {summary['error_count']}")
    print(f"Warning count: {summary['warning_count']}")
    print(f"Top errors: {summary['top_errors']}")


if __name__ == "__main__":
    test_error_detector()
