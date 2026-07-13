"""
Log API Routes for Device Log Intelligence Platform.

Provides endpoints for:
- POST /login: Simple authentication
- POST /upload-log: Accept log file, parse and store logs
- GET /summary: Return error summary
- GET /logs: Paginated logs

With proper error handling and logging.
"""
import os
import logging
import hashlib
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func

from app.utils.database import get_db
from app.models.log_models import Log, ErrorSummary, DeviceInfo
from app.services.log_parser import parse_log_text, parse_log_file, extract_device_info
from app.services.error_detector import generate_summary_report, get_error_frequency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Creator signature embedded in the system
CREATOR_NAME = "Drawesh Kumar Yadav"
CREATOR_VERSION = "v1.0-DY"

# Create router
router = APIRouter()

# Upload directory
UPLOAD_DIR = "logs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Simple API key for demo (in production, use proper JWT)
DEMO_API_KEY = "dev_log_intel_2024"


@router.post("/login")
async def login(username: str = "", password: str = ""):
    """
    Simple login endpoint for demo authentication.
    
    In production, use proper JWT with python-jose.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        API token
    """
    try:
        # Simple demo authentication
        if username and password:
            # Create a simple token
            token_data = f"{username}:{datetime.now().isoformat()}:{DEMO_API_KEY}"
            token = hashlib.sha256(token_data.encode()).hexdigest()
            
            logger.info(f"User {username} logged in")
            
            return {
                "status": "success",
                "token": token,
                "username": username,
                "expires_in": 86400,
                "message": "Demo login successful. Use token in X-API-Key header."
            }
        else:
            # Allow demo access without username/password
            token = hashlib.sha256(f"demo:{datetime.now().isoformat()}:{DEMO_API_KEY}".encode()).hexdigest()
            
            return {
                "status": "success",
                "token": token,
                "username": "demo",
                "expires_in": 86400,
                "message": "Demo mode. Use token in X-API-Key header."
            }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )


@router.post("/upload-log")
async def upload_log_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a log file.
    
    Accepts a log file, parses it, and stores the logs in the database.
    
    Args:
        file: Uploaded log file
        db: Database session
        
    Returns:
        JSON response with parsed log count and summary
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file extension
        allowed_extensions = [".log", ".txt", ".cat"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions and file_ext != "":
            logger.warning(f"File extension {file_ext} might not be a log file")
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Write file to disk
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved: {file_path}")
        
        # Parse log file
        try:
            parsed_logs = parse_log_file(file_path)
        except Exception as e:
            logger.error(f"Error parsing log file: {e}")
            # Try parsing as text
            try:
                parsed_logs = parse_log_text(content.decode("utf-8"))
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to parse log file: {str(e)}"
                )
        
        if not parsed_logs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid log entries found in file"
            )
        
        # Clear old logs and insert new ones
        try:
            db.query(Log).delete()
            db.commit()
        except:
            db.rollback()
        
# Insert logs into database
        inserted_count = 0
        for log_data in parsed_logs:
            try:
                db_log = Log(
                    timestamp=log_data.get("timestamp"),
                    pid=log_data.get("pid"),
                    tid=log_data.get("tid"),
                    level=log_data.get("level", "UNKNOWN"),
                    tag=log_data.get("tag", ""),
                    message=log_data.get("message", "")
                )
                db.add(db_log)
                inserted_count += 1
            except Exception as e:
                logger.warning(f"Error inserting log: {e}")
        
        db.commit()
        logger.info(f"Inserted {inserted_count} logs into database")
        
# Generate summary
        summary = generate_summary_report(parsed_logs)
        
        # Extract and save device info
        device_info = extract_device_info(parsed_logs)
        if device_info:
            save_device_info(db, device_info)
            logger.info(f"Extracted device info: {device_info}")
        
        # Update error summary in database
        update_error_summary(db, parsed_logs)
        
        return {
            "status": "success",
            "message": f"Successfully parsed {inserted_count} log entries",
            "total_logs": inserted_count,
            "file": file.filename,
            "summary": summary,
            "device_info": device_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading log file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading log file: {str(e)}"
        )


@router.get("/summary")
async def get_summary(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive error summary from database.
    
    Returns:
        JSON response with detailed analytics and insights
    """
    try:
        from sqlalchemy import func
        from app.services.error_detector import classify_error_severity, detect_error_patterns, detect_warning_patterns
        
        # Get total counts from database
        total_logs = db.query(Log).count()
        error_count = db.query(Log).filter(Log.level.in_(["ERROR", "FATAL"])).count()
        warning_count = db.query(Log).filter(Log.level == "WARNING").count()
        info_count = db.query(Log).filter(Log.level == "INFO").count()
        debug_count = db.query(Log).filter(Log.level == "DEBUG").count()
        verbose_count = db.query(Log).filter(Log.level == "VERBOSE").count()
        unknown_count = db.query(Log).filter(Log.level == "UNKNOWN").count()
        
        # Get top errors
        error_summary = db.query(ErrorSummary).order_by(desc(ErrorSummary.count)).limit(10).all()
        top_errors = [{"error_type": e.error_type, "count": e.count} for e in error_summary]
        
        # Get recent errors
        recent_logs = db.query(Log).filter(
            Log.level.in_(["ERROR", "FATAL"])
        ).order_by(desc(Log.id)).limit(20).all()
        
        # Get top tags by frequency
        top_tags_query = db.query(
            Log.tag,
            func.count(Log.id).label('count')
        ).group_by(Log.tag).order_by(desc('count')).limit(15).all()
        top_tags_list = [{"tag": t.tag, "count": t.count} for t in top_tags_query]
        
        # Get level distribution
        level_dist = db.query(
            Log.level,
            func.count(Log.id).label('count')
        ).group_by(Log.level).all()
        level_distribution = [{"level": l.level, "count": l.count} for l in level_dist]
        
        # Get most common messages
        common_messages = db.query(
            Log.message,
            func.count(Log.id).label('count')
        ).group_by(Log.message).order_by(desc('count')).limit(15).all()
        top_messages = [{"message": m.message[:150] if m.message else "", "count": m.count} for m in common_messages]
        
        # Get additional analytics
        # 1. Error patterns detected (from messages)
        all_logs = db.query(Log.message).limit(5000).all()
        error_pattern_counts = {}
        warning_pattern_counts = {}
        
        for log_tuple in all_logs:
            message = log_tuple[0] or ""
            # Detect error patterns
            errors = detect_error_patterns(message)
            for err in errors:
                error_pattern_counts[err] = error_pattern_counts.get(err, 0) + 1
            # Detect warning patterns
            warnings = detect_warning_patterns(message)
            for warn in warnings:
                warning_pattern_counts[warn] = warning_pattern_counts.get(warn, 0) + 1
        
        # Convert to sorted list
        detected_errors = sorted(error_pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        detected_warnings = sorted(warning_pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 2. Time-based analytics (if timestamps available)
        # Get unique tag count
        unique_tags = db.query(Log.tag).distinct().count()
        
        # 3. Process/PID analytics
        pid_logs = db.query(
            Log.pid,
            func.count(Log.id).label('count')
        ).filter(Log.pid != None).group_by(Log.pid).order_by(desc('count')).limit(10).all()
        top_pids = [{"pid": str(p.pid) if p.pid else "unknown", "count": p.count} for p in pid_logs]
        
        # 4. Severity analysis. These are subdivisions of error_count only.
        error_logs_for_severity = db.query(Log.level, Log.message).filter(
            Log.level.in_(["ERROR", "FATAL"])
        ).all()
        severity_stats = {"critical": 0, "high": 0, "medium": 0}
        for level, message in error_logs_for_severity:
            severity = classify_error_severity({"level": level, "message": message})
            if severity:
                severity_stats[severity] += 1

        # Non-error level counts are kept separate from error severity.
        severity_stats.update({
            "low": info_count + debug_count,
            "verbose": verbose_count
        })
        
        # 5. System health score (simple calculation)
        health_score = 100
        if total_logs > 0:
            health_score = max(0, 100 - (error_count * 0.5) - (warning_count * 0.2))
        
        # 6. Get device info
        device_info_record = db.query(DeviceInfo).first()
        device_info = device_info_record.to_dict() if device_info_record else {}
        
        # Remove id from device_info to avoid confusion
        if "id" in device_info:
            del device_info["id"]
        
        return {
            "total_logs": total_logs,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "debug_count": debug_count,
            "verbose_count": verbose_count,
            "unknown_count": unknown_count,
            "unique_tags": unique_tags,
            "health_score": round(health_score, 1),
            # Error analysis
            "top_errors": top_errors,
            "detected_error_patterns": [{"pattern": e[0], "count": e[1]} for e in detected_errors],
            "detected_warning_patterns": [{"pattern": w[0], "count": w[1]} for w in detected_warnings],
            # Recent logs
            "recent_errors": [log.to_dict() for log in recent_logs],
            # Tag analytics
            "top_tags": top_tags_list,
            # Level distribution
            "level_distribution": level_distribution,
            # Message analytics
            "top_messages": top_messages,
            # Process analytics
            "top_pids": top_pids,
            # Severity analysis
            "severity_stats": severity_stats,
            # Device info
            "device_info": device_info,
            # Creator signature embedded - Created by Drawesh Kumar Yadav
            "_creator": CREATOR_NAME,
            "_version": CREATOR_VERSION,
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting summary: {str(e)}"
        )


@router.get("/logs/by-level")
async def get_logs_by_level(
    level_type: str = Query(..., description="Log level type: errors, warnings, info, debug, verbose, all"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=10000, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    """
    Get logs filtered by level type.
    
    Args:
        level_type: Type of logs to fetch (errors, warnings, info, debug, verbose, all)
        page: Page number (starting from 1)
        page_size: Number of items per page
        
    Returns:
        JSON response with filtered logs
    """
    try:
        from app.services.error_detector import classify_error_severity

        query = db.query(Log)
        
        # Apply level filter
        if level_type == "errors":
            query = query.filter(Log.level.in_(["ERROR", "FATAL"]))
        elif level_type == "warnings":
            query = query.filter(Log.level == "WARNING")
        elif level_type == "info":
            query = query.filter(Log.level == "INFO")
        elif level_type == "debug":
            query = query.filter(Log.level == "DEBUG")
        elif level_type == "verbose":
            query = query.filter(Log.level == "VERBOSE")
        # "all" returns everything, no filter applied
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        offset = (page - 1) * page_size
        
        # Get logs (most recent first)
        logs = query.order_by(desc(Log.id)).offset(offset).limit(page_size).all()
        
        serialized_logs = []
        for log in logs:
            log_data = log.to_dict()
            if level_type == "errors":
                log_data["error_severity"] = classify_error_severity(log_data)
            serialized_logs.append(log_data)

        return {
            "level_type": level_type,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            "logs": serialized_logs
        }
        
    except Exception as e:
        logger.error(f"Error getting logs by level: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting logs: {str(e)}"
        )


@router.get("/logs")
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in message"),
    db: Session = Depends(get_db)
):
    """
    Get paginated logs from database.
    
    Args:
        page: Page number (starting from 1)
        page_size: Number of items per page
        level: Filter by log level
        tag: Filter by tag
        search: Search in message
        
    Returns:
        JSON response with paginated logs
    """
    try:
        # Build query
        query = db.query(Log)
        
        # Apply filters
        if level:
            query = query.filter(Log.level == level.upper())
        
        if tag:
            query = query.filter(Log.tag.like(f"%{tag}%"))
        
        if search:
            query = query.filter(Log.message.like(f"%{search}%"))
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        offset = (page - 1) * page_size
        
        # Get logs
        logs = query.order_by(desc(Log.id)).offset(offset).limit(page_size).all()
        
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
            "logs": [log.to_dict() for log in logs]
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting logs: {str(e)}"
        )


def update_error_summary(db: Session, parsed_logs: List[dict]):
    """
    Update error summary in database.
    
    Args:
        db: Database session
        parsed_logs: List of parsed log dictionaries
    """
    try:
        # Clear old error summary
        db.query(ErrorSummary).delete()
        db.commit()
        
        # Get error frequency
        error_freq = get_error_frequency(parsed_logs)
        
        # Insert new error summary
        for error_type, count in error_freq.items():
            error_summary = ErrorSummary(
                error_type=error_type,
                count=count
            )
            db.add(error_summary)
        
        db.commit()
        logger.info(f"Updated error summary with {len(error_freq)} error types")
        
    except Exception as e:
        logger.error(f"Error updating error summary: {e}")
        db.rollback()


def save_device_info(db: Session, device_info: dict):
    """
    Save device information to database.
    
    Args:
        db: Database session
        device_info: Dictionary with device information
    """
    try:
        # Clear old device info
        db.query(DeviceInfo).delete()
        db.commit()
        
        # Create new device info entry
        db_device = DeviceInfo(
            device_model=device_info.get("device_model"),
            manufacturer=device_info.get("manufacturer"),
            android_version=device_info.get("android_version"),
            sdk_version=device_info.get("sdk_version"),
            serial_number=device_info.get("serial_number"),
            bootloader_version=device_info.get("bootloader_version"),
            radio_version=device_info.get("radio_version"),
            up_time=device_info.get("up_time"),
            uptime_seconds=device_info.get("uptime_seconds"),
            manufacture_date=device_info.get("manufacture_date"),
            registered_date=device_info.get("registered_date"),
            battery_health=device_info.get("battery_health"),
            battery_level=device_info.get("battery_level"),
            charging_status=device_info.get("charging_status"),
            charging_cycles=device_info.get("charging_cycles"),
            temperature=device_info.get("temperature"),
            voltage=device_info.get("voltage"),
            kernel_version=device_info.get("kernel_version"),
            build_fingerprint=device_info.get("build_fingerprint")
        )
        db.add(db_device)
        db.commit()
        logger.info(f"Saved device info to database")
        
    except Exception as e:
        logger.error(f"Error saving device info: {e}")
        db.rollback()


@router.delete("/logs")
async def delete_all_logs(
    db: Session = Depends(get_db)
):
    """
    Delete all logs from database (for testing/reset).
    
    Returns:
        JSON response with deletion status
    """
    try:
        db.query(Log).delete()
        db.query(ErrorSummary).delete()
        db.commit()
        
        return {
            "status": "success",
            "message": "All logs deleted"
        }
        
    except Exception as e:
        logger.error(f"Error deleting logs: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting logs: {str(e)}"
        )
