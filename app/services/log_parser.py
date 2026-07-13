"""
Log Parser Module for Android logcat logs.

This module provides functions to parse raw Android logcat log text
and extract structured information.

Input: raw log text file or line
Output: structured JSON with timestamp, level, tag, and message
"""
import re
import json
import logging
from urllib.parse import unquote
from typing import List, Dict, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log level mapping
LOG_LEVELS = {
    "V": "VERBOSE",
    "D": "DEBUG",
    "I": "INFO",
    "W": "WARNING",
    "E": "ERROR",
    "F": "FATAL",
    "A": "ASSERT"
}

# Regular expression patterns for logcat log lines
# Format: "YYYY-MM-DD HH:MM:SS.mmm  PID  TID LEVEL TAG: MESSAGE"
LOG_PATTERN_V4 = re.compile(
    r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+"  # Timestamp
    r"(\d+)\s+"  # PID
    r"(\d+)\s+"  # TID
    r"([VDIWEFA])\s+"  # Level
    r"(\w+):\s*"  # Tag
    r"(.*)$"  # Message
)

# Alternative format: "LEVEL/TAG: MESSAGE" (simplified format)
LOG_PATTERN_SIMPLE = re.compile(
    r"^([VDIWEFA])/([^:]+):\s*(.*)$"
)

# Another common format with time only
LOG_PATTERN_TIME_ONLY = re.compile(
    r"^(\d{2}:\d{2}:\d{2}\.\d{3})\s+"  # Time only
    r"(\d+)\s+"  # PID
    r"(\d+)\s+"  # TID
    r"([VDIWEFA])\s+"  # Level
    r"(\w+):\s*"  # Tag
    r"(.*)$"  # Message
)

# Android format with tag and message combined: "  PID  TID LEVEL TAG: MESSAGE"
# Updated to handle trailing spaces before colon: MM-DD HH:MM:SS.mmm PID TID LEVEL TAG    : MESSAGE
LOG_PATTERN_ANDROID = re.compile(
    r"^\s*(\d+-\d+\s+\d+:\d+:\d+\.\d+)\s+"  # MM-DD HH:MM:SS.mmm
    r"(\d+)\s+"  # PID
    r"(\d+)\s+"  # TID
    r"([VDIWEFA])\s+"  # Level
    r"(\w+)\s*:\s*"  # Tag (with optional trailing spaces before colon)
    r"(.*)$"  # Message
)

# Alternative Android format without date (time only): "HH:MM:SS.mmm PID TID LEVEL TAG    : MESSAGE"
LOG_PATTERN_ANDROID_TIME = re.compile(
    r"^(\d+:\d+:\d+\.\d+)\s+"  # HH:MM:SS.mmm
    r"(\d+)\s+"  # PID
    r"(\d+)\s+"  # TID
    r"([VDIWEFA])\s+"  # Level
    r"(\w+)\s*:\s*"  # Tag (with optional trailing spaces)
    r"(.*)$"  # Message
)

# Format with just level after tag: "TAG: LEVEL MESSAGE"
LOG_PATTERN_TAG_LEVEL = re.compile(
    r"^(\w+):\s*([VDIWEFA])\s+(.*)$"
)


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single logcat line into structured data.
    
    Args:
        line: Raw log line string
        
    Returns:
        Dictionary with timestamp, level, tag, message or None if malformed
    """
    if not line or not line.strip():
        return None
    
    line = line.strip()
    
    # Skip empty lines and system messages
    if not line or line.startswith("-"):
        return None
    
    # Try the detailed timestamp format (YYYY-MM-DD HH:MM:SS.mmm)
    match = LOG_PATTERN_V4.match(line)
    if match:
        return {
            "timestamp": match.group(1),
            "pid": match.group(2),
            "tid": match.group(3),
            "level": LOG_LEVELS.get(match.group(4), match.group(4)),
            "tag": match.group(5),
            "message": match.group(6).strip()
        }
    
    # Try simple format (LEVEL/TAG: MESSAGE)
    match = LOG_PATTERN_SIMPLE.match(line)
    if match:
        return {
            "timestamp": None,
            "pid": None,
            "tid": None,
            "level": LOG_LEVELS.get(match.group(1), match.group(1)),
            "tag": match.group(2).strip(),
            "message": match.group(3).strip()
        }
    
# Try time-only format (HH:MM:SS.mmm)
    match = LOG_PATTERN_TIME_ONLY.match(line)
    if match:
        return {
            "timestamp": match.group(1),
            "pid": match.group(2),
            "tid": match.group(3),
            "level": LOG_LEVELS.get(match.group(4), match.group(4)),
            "tag": match.group(5),
            "message": match.group(6).strip()
        }
    
# Try Android format with date: "MM-DD HH:MM:SS.mmm PID TID LEVEL TAG: MESSAGE"
    match = LOG_PATTERN_ANDROID.match(line)
    if match:
        return {
            "timestamp": match.group(1),
            "pid": match.group(2),
            "tid": match.group(3),
            "level": LOG_LEVELS.get(match.group(4), match.group(4)),
            "tag": match.group(5),
            "message": match.group(6).strip()
        }
    
    # Try Android time-only format: "HH:MM:SS.mmm PID TID LEVEL TAG: MESSAGE"
    match = LOG_PATTERN_ANDROID_TIME.match(line)
    if match:
        return {
            "timestamp": match.group(1),
            "pid": match.group(2),
            "tid": match.group(3),
            "level": LOG_LEVELS.get(match.group(4), match.group(4)),
            "tag": match.group(5),
            "message": match.group(6).strip()
        }
    
    # Try format: "TAG: LEVEL MESSAGE"
    match = LOG_PATTERN_TAG_LEVEL.match(line)
    if match:
        return {
            "timestamp": None,
            "pid": None,
            "tid": None,
            "level": LOG_LEVELS.get(match.group(2), match.group(2)),
            "tag": match.group(1),
            "message": match.group(3).strip()
        }
    
# If none of the patterns match, try to detect level from message content
    if line:
        # Detect level from keywords in message
        level = "UNKNOWN"
        if re.search(r'\bE\b|\bERROR\b|\bFAIL\b|\bFAILED\b', line, re.IGNORECASE):
            level = "ERROR"
        elif re.search(r'\bW\b|\bWARNING\b|\bWARN\b', line, re.IGNORECASE):
            level = "WARNING"
        elif re.search(r'\bI\b|\bINFO\b', line, re.IGNORECASE):
            level = "INFO"
        elif re.search(r'\bD\b|\bDEBUG\b', line, re.IGNORECASE):
            level = "DEBUG"
        elif re.search(r'\bV\b|\bVERBOSE\b', line, re.IGNORECASE):
            level = "VERBOSE"
        elif re.search(r'\bF\b|\bFATAL\b', line, re.IGNORECASE):
            level = "FATAL"
        
        # Try to extract tag from common formats - multiple patterns
        tag = "unknown"
        
        # Pattern 1: "TAG: message" or "TAG message"
        tag_match = re.match(r'^(\w+)[\s:]', line)
        if tag_match:
            tag = tag_match.group(1)
        # Pattern 2: "LEVEL/TAG: message" (already handled above but as fallback)
        elif '/' in line:
            parts = line.split('/', 1)
            if len(parts[0]) <= 2:  # Single letter level like E, W, D
                level_part = parts[0].strip()
                if level_part in LOG_LEVELS or level_part in "VDIWEFA":
                    tag_match = re.match(r'\w+', parts[1])
                    if tag_match:
                        tag = tag_match.group(0)
        # Pattern 3: "[TAG] message" or "(TAG) message"
        tag_match = re.match(r'\[(\w+)\]', line)
        if tag_match:
            tag = tag_match.group(1)
        tag_match = re.match(r'\((\w+)\)', line)
        if tag_match:
            tag = tag_match.group(1)
        
        return {
            "timestamp": None,
            "pid": None,
            "tid": None,
            "level": level,
            "tag": tag,
            "message": line
        }
    # This handles malformed or unexpected formats
    if line:
        return {
            "timestamp": None,
            "pid": None,
            "tid": None,
            "level": "UNKNOWN",
            "tag": "unknown",
            "message": line
        }
    
    return None


def parse_log_file(file_path: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """
    Parse an entire log file and return all parsed log entries.
    
    Args:
        file_path: Path to the log file
        encoding: File encoding (default: utf-8)
        
    Returns:
        List of dictionaries containing parsed log entries
    """
    parsed_logs = []
    malformed_count = 0
    
    try:
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    parsed = parse_log_line(line)
                    if parsed:
                        parsed_logs.append(parsed)
                    else:
                        malformed_count += 1
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")
                    malformed_count += 1
    except FileNotFoundError:
        logger.error(f"Log file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise
    
    logger.info(f"Parsed {len(parsed_logs)} logs, {malformed_count} malformed lines")
    return parsed_logs


def parse_log_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse log text directly from a string.
    
    Args:
        text: Raw log text
        
    Returns:
        List of dictionaries containing parsed log entries
    """
    parsed_logs = []
    lines = text.split("\n")
    
    for line in lines:
        parsed = parse_log_line(line)
        if parsed:
            parsed_logs.append(parsed)
    
    return parsed_logs


def logs_to_json(logs: List[Dict[str, Any]], output_file: str = None) -> str:
    """
    Save parsed logs as structured JSON.
    
    Args:
        logs: List of parsed log dictionaries
        output_file: Optional file path to save JSON
        
    Returns:
        JSON string of parsed logs
    """
    json_data = json.dumps(logs, indent=2, ensure_ascii=False)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_data)
        logger.info(f"Saved parsed logs to {output_file}")
    
    return json_data


def filter_logs_by_level(logs: List[Dict[str, Any]], level: str) -> List[Dict[str, Any]]:
    """
    Filter logs by log level.
    
    Args:
        logs: List of parsed log dictionaries
        level: Log level to filter by (e.g., "ERROR", "WARNING")
        
    Returns:
        Filtered list of logs
    """
    return [log for log in logs if log.get("level") == level.upper()]


def filter_logs_by_tag(logs: List[Dict[str, Any]], tag: str) -> List[Dict[str, Any]]:
    """
    Filter logs by tag.
    
    Args:
        logs: List of parsed log dictionaries
        tag: Tag to filter by
        
    Returns:
        Filtered list of logs
    """
    return [log for log in logs if tag.lower() in log.get("tag", "").lower()]


def search_logs(logs: List[Dict[str, Any]], search_term: str) -> List[Dict[str, Any]]:
    """
    Search logs for a specific term in message or tag.
    
    Args:
        logs: List of parsed log dictionaries
        search_term: Search term to look for
        
    Returns:
        Filtered list of logs containing the search term
    """
    search_term = search_term.lower()
    return [
        log for log in logs
        if search_term in log.get("message", "").lower() or search_term in log.get("tag", "").lower()
    ]


# Device info extraction patterns
DEVICE_INFO_PATTERNS = {
    # Model and manufacturer
    "device_model": [
        r"\bcmodel=([^&\s,;]+)",
        r"\bcmodel[:\s]+([^&\s,;]+)",
        r"Model:\s*(\S+)",
        r"\bmodel=([^&\s,;]+)",
        r"\bmodel[:\s]+(\S+)",
        r"Device:\s*(\S+)",
        r"ro\.product\.model[=:\s]+(\S+)",
        r"Product:\s*(\S+)",
    ],
    "manufacturer": [
        r"\bcbrand=([^&\s,;]+)",
        r"\bcbrand[:\s]+(\S+)",
        r"\bbrand=([^&\s,;]+)",
        r"\bbrand[:\s]+(\S+)",
        r"Manufacturer:\s*(\S+)",
        r"\bmanufacturer=([^&\s,;]+)",
        r"\bmanufacturer[:\s]+(\S+)",
        r"ro\.product\.manufacturer[=:\s]+(\S+)",
        r"Brand:\s*(\S+)",
    ],
    # Android version
    "android_version": [
        r"Android\s*(\d+\.\d+(?:\.\d+)?)",
        r"Release:\s*(\d+\.\d+(?:\.\d+)?)",
        r"ro\.build\.version\.release[=:\s]+(\d+\.\d+(?:\.\d+)?)",
    ],
    "sdk_version": [
        r"SDK:\s*(\d+)",
        r"Sdk:\s*(\d+)",
        r"ro\.build\.version\.sdk[=:\s]+(\d+)",
    ],
    # Serial number
    "serial_number": [
        r"Serial\s*Number:\s*(\S+)",
        r"SerialNumber:\s*(\S+)",
        r"ro\.serialno[=:\s]+(\S+)",
        r"SN:\s*(\S+)",
    ],
    # Bootloader
    "bootloader_version": [
        r"Bootloader:\s*(\S+)",
        r"bootloader[:\s]+(\S+)",
        r"ro\.bootloader[=:\s]+(\S+)",
    ],
    # Radio version
    "radio_version": [
        r"Radio:\s*(\S+)",
        r"Baseband:\s*(\S+)",
        r"ro\.post\.cs\.global\.radio[=:\s]+(\S+)",
    ],
    # Kernel version
    "kernel_version": [
        r"Linux\s+version\s+(\S+)",
        r"Kernel:\s*(\S+)",
    ],
    # Build fingerprint
    "build_fingerprint": [
        r"Build fingerprint:\s*'(\S+)",
        r"ro\.build\.fingerprint[=:\s]+(\S+)",
    ],
    # Uptime
    "up_time": [
        r"uptime[:\s]+(\d+:\d+:\d+)",
        r"up\s+(\d+d\s+\d+h\s+\d+m)",
        r"System\s+up\s+time[:\s]+(\d+:\d+:\d+)",
    ],
    # Battery
    "battery_health": [
        r"Health:\s*(\w+)",
        r"Battery\s+Health:\s*(\w+)",
    ],
    "battery_level": [
        r"level[:\s]+(\d+)%",
        r"Battery:\s*(\d+)%",
    ],
    "charging_status": [
        r"Status:(\s*\w+),",
        r"Charging:\s*(\w+)",
    ],
    "charging_cycles": [
        r"cycle[s]?[:\s=]+(\d+)",
        r"Charge cycles:\s*(\d+)",
    ],
    "temperature": [
        r"temperature[:\s]+([-\d.]+)",
        r"Temp:\s*([-\d.]+)",
    ],
    "voltage": [
        r"voltage[:\s]+(\d+\s*mV)",
        r"Voltage:\s*(\d+\s*mV)",
    ],
    # Manufacture date
    "manufacture_date": [
        r"mfg\.date[:\s=]+(\S+)",
        r"Manuf\s+Date[:\s=]+(\S+)",
    ],
    "registered_date": [
        r" registered[:\s=]+(\S+)",
        r"registered\s+date[:\s=]+(\S+)",
    ],
}


def extract_device_info(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract device information from parsed logs.
    
    Args:
        logs: List of parsed log dictionaries
        
    Returns:
        Dictionary with device information
    """
    device_info = {}
    combined_text = " ".join([log.get("message", "") for log in logs])
    decoded_text = unquote(combined_text)

    def clean_device_info_value(field: str, raw_value: str) -> Any:
        value = unquote(raw_value.strip().strip("'\"[]()"))
        if field == "device_model":
            value = re.split(r"[&;,]|\s+(?=\w+=)|\s+", value, maxsplit=1)[0]
        else:
            value = re.split(r"[&;,]|\s+(?=\w+=)", value, maxsplit=1)[0]
        return value.strip().strip("'\"[]()")

    key_value_patterns = {
        "device_model": r"(?:^|[?&\s,;])cmodel\s*=\s*([^&\s,;]+)",
        "manufacturer": r"(?:^|[?&\s,;])c?brand\s*=\s*(.+?)(?=$|[&;,]|\s+\w+\s*=)",
    }

    for field, pattern in key_value_patterns.items():
        for text in (decoded_text, combined_text):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = clean_device_info_value(field, match.group(1))
                if value and value.lower() != "unknown":
                    device_info[field] = value
                    break
    
    for field, patterns in DEVICE_INFO_PATTERNS.items():
        if field in device_info:
            continue
        for pattern in patterns:
            match = re.search(pattern, decoded_text, re.IGNORECASE) or re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                value = clean_device_info_value(field, match.group(1))
                if field == "battery_level":
                    try:
                        value = int(value)
                    except:
                        value = None
                if value and value != "unknown":
                    device_info[field] = value
                    break
    
    # Calculate uptime in seconds if up_time is found
    if "up_time" in device_info:
        try:
            uptime_str = device_info["up_time"]
            parts = uptime_str.split(":")
            seconds = 0
            if len(parts) == 3:
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            device_info["uptime_seconds"] = seconds
        except:
            pass
    
    return device_info


# Test function
def test_parser():
    """
    Test the log parser with sample data.
    """
    sample_logs = """
2024-01-15 10:30:45.123  1234  5678 E AndroidRuntime: FATAL EXCEPTION: main
2024-01-15 10:30:45.234  1234  5678 E AndroidRuntime: Process: com.example.app, PID: 1234
2024-01-15 10:30:45.345  1234  5678 W ActivityManager: Activity pause timeout
2024-01-15 10:30:46.123  1234  5678 I ActivityManager: Starting activity
E/Tag: This is a simple error message
D/SensorService: Sensor data received
    """
    
    parsed = parse_log_text(sample_logs)
    print(f"Parsed {len(parsed)} logs:")
    for log in parsed:
        print(json.dumps(log, indent=2))


if __name__ == "__main__":
    test_parser()
