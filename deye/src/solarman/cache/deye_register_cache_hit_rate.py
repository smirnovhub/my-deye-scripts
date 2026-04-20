from dataclasses import dataclass

@dataclass
class DeyeRegisterCacheHitRate:
  got_from_cache_count: int
  got_from_inverter_count: int
  total_count: int
  cache_hit_rate: float

  @property
  def cache_hit_rate_percent(self) -> int:
    return round(self.cache_hit_rate * 100)

  @classmethod
  def zero(cls) -> "DeyeRegisterCacheHitRate":
    return cls(
      got_from_cache_count = 0,
      got_from_inverter_count = 0,
      total_count = 0,
      cache_hit_rate = 0.0,
    )
