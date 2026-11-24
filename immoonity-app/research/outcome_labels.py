"""Reference labels for research. Inputs must have been independently adjudicated."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    component: str
    first_confirmed_day: int
    last_known_absent_day: int | None = None


def status_by_day(day: int, *, last_joint_negative: int | None, followup_end: int,
                  events: list[Event], event_free_at_launch: bool | None) -> str:
    """Retrospective event-by-day label. Unknown stays unknown. Day 1 is the first flight day.

    last_joint_negative certifies that NEITHER component had occurred since launch
    through that day. Absence of active symptoms on an isolated later visit is insufficient.
    Confirmed cases are part of the composite forever after the first documented occurrence.
    """
    if type(day) is not int or day < 1 or type(followup_end) is not int or followup_end < 0:
        raise ValueError("Invalid day or follow-up")
    if last_joint_negative is not None and (type(last_joint_negative) is not int
                                          or not 0 <= last_joint_negative <= followup_end):
        raise ValueError("Invalid joint-negative coverage")
    for event in events:
        if event.component not in ("mission_failure", "immune_deficiency_with_disease"):
            raise ValueError("Adjudicate the endpoint components before labelling")
        if type(event.first_confirmed_day) is not int or not 1 <= event.first_confirmed_day <= followup_end:
            raise ValueError("Event outside observed flight follow-up")
        if event.last_known_absent_day is not None and (type(event.last_known_absent_day) is not int
                or not 0 <= event.last_known_absent_day < event.first_confirmed_day):
            raise ValueError("Invalid detection interval")
        if last_joint_negative is not None and last_joint_negative >= event.first_confirmed_day:
            raise ValueError("Joint-negative coverage contradicts a confirmed event")
    if event_free_at_launch is not True:
        return "baseline_ineligible_or_unknown"
    if any(e.first_confirmed_day <= day for e in events):
        return "observed_event"
    if day > followup_end:
        return "followup_ended"
    # In an interval between last negative and first confirmation the event may already have occurred.
    if last_joint_negative is not None and day <= last_joint_negative:
        return "observed_event_free"
    return "unknown"
