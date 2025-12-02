from dataclasses import dataclass

@dataclass
class TimeOfUseWeek:
  """
  Represents the days of the week for a time-of-use schedule.

  Attributes:
      monday (bool): True if the schedule applies on Monday.
      tuesday (bool): True if the schedule applies on Tuesday.
      wednesday (bool): True if the schedule applies on Wednesday.
      thursday (bool): True if the schedule applies on Thursday.
      friday (bool): True if the schedule applies on Friday.
      saturday (bool): True if the schedule applies on Saturday.
      sunday (bool): True if the schedule applies on Sunday.
  """
  monday: bool
  tuesday: bool
  wednesday: bool
  thursday: bool
  friday: bool
  saturday: bool
  sunday: bool

  def __str__(self) -> str:
    return (f'monday={self.monday}, tuesday={self.tuesday}, '
            f'wednesday={self.wednesday}, thursday={self.thursday}, '
            f'friday={self.friday}, saturday={self.saturday}, sunday={self.sunday}')
