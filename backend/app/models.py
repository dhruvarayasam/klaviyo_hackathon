from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


def utcnow():
    return datetime.now(timezone.utc)

# a monitored object is a flow or campaign
# that we can keep a watch on for performance --> if it dips below a certain threshold, we can trigger an incident

class MonitoredObject(Base):
    # monitored objects are saved in database
    __tablename__ = "monitored_objects"

    id = Column(Integer, primary_key=True, index=True)

    klaviyo_id = Column(String, nullable=False, index=True)
    obj_type = Column(String, nullable=False)  # "flow" | "campaign"
    name = Column(String, nullable=False)

    channel = Column(String, nullable=False)  # "email" | "sms"
    primary_metric = Column(String, nullable=False)  # "conversion_rate" | "revenue_per_recipient"

    baseline_hours = Column(Integer, nullable=False, default=24 * 14) # used to calculate historical data over 2 weeks
    recent_hours = Column(Integer, nullable=False, default=48) # calculates performance over last 2 days
    
     # if performance of metric drops by more than this val, we trigger an incident
    allowed_drop_pct = Column(Float, nullable=False, default=0.20) 

    is_enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    snapshots = relationship("MetricSnapshot", back_populates="monitored_object")
    incidents = relationship("Incident", back_populates="monitored_object")

    __table_args__ = (
        UniqueConstraint("klaviyo_id", "obj_type", name="uq_monitored_klaviyo_object"),
    )


# this is for storing the performance metrics for a monitored object at a given time window (baseline or recent)

class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    monitored_object_id = Column(Integer, ForeignKey("monitored_objects.id"), nullable=False)

    window = Column(String, nullable=False)  # "baseline" | "recent"
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)

    sent = Column(Integer, nullable=False, default=0)
    opened = Column(Integer, nullable=False, default=0)
    clicked = Column(Integer, nullable=False, default=0)
    converted = Column(Integer, nullable=False, default=0)
    revenue = Column(Float, nullable=False, default=0.0)

    conversion_rate = Column(Float, nullable=False, default=0.0)
    revenue_per_recipient = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    monitored_object = relationship("MonitoredObject", back_populates="snapshots")


# this is created when performance dips below accepted threshold

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    monitored_object_id = Column(Integer, ForeignKey("monitored_objects.id"), nullable=False)

    status = Column(String, nullable=False, default="open")
    # open | healing | resolved | rolled_back

    severity = Column(String, nullable=False, default="major")
    # mild | major | critical

    baseline_metric = Column(Float, nullable=False)
    recent_metric = Column(Float, nullable=False)
    drop_pct = Column(Float, nullable=False)

    diagnosis = Column(String, nullable=True)
    proposal_json = Column(String, nullable=True)
    applied_change_json = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow)

    monitored_object = relationship("MonitoredObject", back_populates="incidents")
