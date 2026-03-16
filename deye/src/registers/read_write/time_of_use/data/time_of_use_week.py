from dataclasses import dataclass

@dataclass
class TimeOfUseWeek:
  """
  Represents the days of the week for a time-of-use schedule.

  Attributes:
      enabled (bool): True if time of use schedule enabled.
      monday (bool): True if the schedule applies on Monday.
      tuesday (bool): True if the schedule applies on Tuesday.
      wednesday (bool): True if the schedule applies on Wednesday.
      thursday (bool): True if the schedule applies on Thursday.
      friday (bool): True if the schedule applies on Friday.
      saturday (bool): True if the schedule applies on Saturday.
      sunday (bool): True if the schedule applies on Sunday.
  """
  enabled: bool
  monday: bool
  tuesday: bool
  wednesday: bool
  thursday: bool
  friday: bool
  saturday: bool
  sunday: bool
