from datetime import datetime


def local_now() -> datetime:
    """Server-local, timezone-aware 'now' — used consistently everywhere
    CareMate reasons about "today"/"now" (event generation, missed-status
    detection, adherence period boundaries).

    Simplification: assumes every patient is in the server's timezone.
    CAREMATE_MASTER_SPEC.md section 16 explicitly flags this as something
    not to assume forever — revisit once patient-level timezones exist.
    Not needed yet for a single-region prototype.
    """
    return datetime.now().astimezone()
