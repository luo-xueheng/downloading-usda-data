"""Evidence-backed publication events with precision and stale-calendar state."""
from dataclasses import dataclass,asdict
from datetime import date,datetime,time,timedelta,timezone
from zoneinfo import ZoneInfo
from .errors import ConfigurationError

@dataclass(frozen=True)
class PublicationEvent:
    dataset: str
    artifact_kind: str
    source_date: str
    source_url: str
    verified_at_utc: str
    source_time: str | None = None
    source_timezone: str | None = None
    event_id: str = ''

    def to_dict(self):
        result=asdict(self)
        result['release_time_precision']='timestamp' if self.source_time else 'date'
        result['source_release_at_utc']=self.utc().isoformat() if self.utc() else None
        return result

    def utc(self):
        day=date.fromisoformat(self.source_date)
        if self.source_time is None:return None
        if not self.source_timezone:raise ConfigurationError('A source clock needs an independently verified timezone')
        clock=time.fromisoformat(self.source_time)
        return datetime.combine(day,clock,tzinfo=ZoneInfo(self.source_timezone)).astimezone(timezone.utc)


def calendar_status(event,now,*,available=False,stale_after_days=30):
    if now.tzinfo is None:raise ConfigurationError('Calendar clock must be timezone-aware')
    verified=datetime.fromisoformat(event.verified_at_utc)
    if now-verified>timedelta(days=stale_after_days):return 'stale_calendar'
    if available:return 'available'
    instant=event.utc()
    if instant:return 'delayed' if now>=instant else 'pending'
    # A date without a clock cannot establish a missed hour on that date.
    return 'delayed_date_only' if now.date()>date.fromisoformat(event.source_date) else 'pending_date_only'


def presentation(event,timezone_name='Asia/Shanghai'):
    result=event.to_dict();instant=event.utc()
    result['display_timezone']=timezone_name
    result['display_release_at']=instant.astimezone(ZoneInfo(timezone_name)).isoformat() if instant else None
    return result
