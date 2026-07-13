"""
SQLAlchemy models for storing parsed logs.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.utils.database import Base


class Log(Base):
    """
    Model for storing parsed log entries.
    """
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(String(50), nullable=True, index=True)
    pid = Column(String(20), nullable=True, index=True)
    tid = Column(String(20), nullable=True, index=True)
    level = Column(String(10), nullable=False, index=True)
    tag = Column(String(100), nullable=True, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """
        Convert log entry to dictionary.
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "pid": self.pid,
            "tid": self.tid,
            "level": self.level,
            "tag": self.tag,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ErrorSummary(Base):
    """
    Model for storing error summary statistics.
    """
    __tablename__ = "error_summary"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    error_type = Column(String(100), nullable=False, unique=True, index=True)
    count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """
        Convert error summary to dictionary.
        """
        return {
            "id": self.id,
            "error_type": self.error_type,
            "count": self.count,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DeviceInfo(Base):
    """
    Model for storing device information extracted from logs.
    """
    __tablename__ = "device_info"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_model = Column(String(100), nullable=True, index=True)
    manufacturer = Column(String(100), nullable=True, index=True)
    android_version = Column(String(50), nullable=True)
    sdk_version = Column(String(50), nullable=True)
    serial_number = Column(String(100), nullable=True, index=True)
    bootloader_version = Column(String(100), nullable=True)
    radio_version = Column(String(100), nullable=True)
    up_time = Column(String(100), nullable=True)
    uptime_seconds = Column(Integer, nullable=True)
    manufacture_date = Column(String(50), nullable=True)
    registered_date = Column(String(50), nullable=True)
    battery_health = Column(String(50), nullable=True)
    battery_level = Column(Integer, nullable=True)
    charging_status = Column(String(50), nullable=True)
    charging_cycles = Column(Integer, nullable=True, default=0)
    temperature = Column(String(50), nullable=True)
    voltage = Column(String(50), nullable=True)
    kernel_version = Column(String(100), nullable=True)
    build_fingerprint = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """
        Convert device info to dictionary.
        """
        return {
            "id": self.id,
            "device_model": self.device_model,
            "manufacturer": self.manufacturer,
            "android_version": self.android_version,
            "sdk_version": self.sdk_version,
            "serial_number": self.serial_number,
            "bootloader_version": self.bootloader_version,
            "radio_version": self.radio_version,
            "up_time": self.up_time,
            "uptime_seconds": self.uptime_seconds,
            "manufacture_date": self.manufacture_date,
            "registered_date": self.registered_date,
            "battery_health": self.battery_health,
            "battery_level": self.battery_level,
            "charging_status": self.charging_status,
            "charging_cycles": self.charging_cycles,
            "temperature": self.temperature,
            "voltage": self.voltage,
            "kernel_version": self.kernel_version,
            "build_fingerprint": self.build_fingerprint
        }
