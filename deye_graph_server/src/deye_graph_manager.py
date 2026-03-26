import os
import io
import logging

import pandas as pd
import matplotlib
# Use Agg backend for non-interactive PNG generation
# Should be BEFORE import matplotlib.pyplot as plt
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import pandas as pd
from pathlib import Path
from typing import List
from datetime import date, datetime

from deye_graph_data import DeyeGraphData
from deye_graph_inverters import DeyeGraphInverters
from deye_graph_inverter_data import DeyeGraphInverterData
from src.deye_graph_server_config import DeyeGraphServerConfig

class DeyeGraphManager:
  def __init__(
    self,
    config: DeyeGraphServerConfig,
    logger: logging.Logger,
  ):
    self._config = config
    self._logger = logger
    self._data_path = "data/deye-collected-data"

  def check_data_dir_exist(self) -> None:
    base_dir = Path(self._data_path)

    if not base_dir.is_dir():
      raise RuntimeError(f"Data dir '{self._data_path}' doesn't exist")

  def get_available_dates(self) -> List[date]:
    available_dates = []
    # Use Path for convenient file globbing
    base_dir = Path(self._data_path)

    if not base_dir.is_dir():
      raise RuntimeError(f"data dir '{self._data_path}' doesn't exist")

    # Iterate over files matching the YYYY-MM-DD.csv pattern
    for file_path in base_dir.glob("????-??-??.csv"):
      try:
        # Extract filename without extension and convert to date object
        date_str = file_path.stem
        current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        available_dates.append(current_date)
      except ValueError:
        # Skip files that don't strictly match the date format
        continue

    # Return sorted list of dates
    return sorted(available_dates)

  def get_inverters_by_date(self, graph_date: date) -> DeyeGraphInverters:
    # Construct filename from date: YYYY-MM-DD.csv
    file_name = f"{graph_date.isoformat()}.csv"
    file_path = os.path.join(self._data_path, file_name)

    # Check if data file exists for the requested date
    if not os.path.exists(file_path):
      raise RuntimeError(f"data file for date {graph_date.isoformat()} not found")

    try:
      # Load daily data
      df = pd.read_csv(file_path)
      result: List[DeyeGraphInverterData] = []

      # Get list of physical units (master, slave1, slave2, etc.)
      # We exclude 'all' to handle it as a separate category
      all_units = df['inverter'].unique()
      physical_inverters = [inv for inv in all_units if inv != 'all']

      # Temporary storage for parameter sets to calculate intersection later
      physical_params_map = {}

      # Process each physical inverter and collect all its available parameters
      for inv in sorted(physical_inverters):
        # Get unique parameters for this specific unit
        unit_params: List[str] = sorted(list(df[df['inverter'] == inv]['parameter'].unique()))
        physical_params_map[inv] = set(unit_params)

        # Append full data object for this inverter
        result.append(DeyeGraphInverterData(inverter = inv, graphs = self._get_graph_data(unit_params)))

      # Handle 'all' (aggregated system data) separately if present
      if 'all' in all_units:
        all_params: List[str] = sorted(list(df[df['inverter'] == 'all']['parameter'].unique()))
        result.append(DeyeGraphInverterData(inverter = 'all', graphs = self._get_graph_data(all_params)))

      # Calculate 'combined' graphs (intersection of ALL physical inverters)
      # This allows side-by-side comparison of shared metrics
      if len(physical_inverters) > 1:
        # Start with parameters of the first physical inverter
        common_set = physical_params_map[physical_inverters[0]]

        # Intersect with parameters of all other physical units
        for inv in physical_inverters[1:]:
          common_set = common_set.intersection(physical_params_map[inv])

        # If common parameters exist, add a virtual 'combined' inverter entry
        if common_set:
          cs: List[str] = sorted(list(common_set))
          result.append(DeyeGraphInverterData(inverter = "combined", graphs = self._get_graph_data(cs)))

      return DeyeGraphInverters(
        graph_date = graph_date,
        inverters = result,
      )

    except Exception as e:
      # Log error details if file is corrupted or column names are missing
      self._logger.error(f"Error processing {file_name}: {e}")
      raise

  def _get_graph_data(self, graphs: List[str]) -> List[DeyeGraphData]:
    return [DeyeGraphData(
      name = p.replace(" ", "_").lower(),
      description = p,
    ) for p in graphs]

  def generate_graph_png(self, graph_date: date, inverter: str, graph_name: str) -> bytes:
    # Construct file path from date
    file_name = f"{graph_date.isoformat()}.csv"
    file_path = os.path.join(self._data_path, file_name)

    if not os.path.exists(file_path):
      raise RuntimeError(f"data file for date {graph_date.isoformat()} not found")

    try:
      # Load data and ensure timestamp is parsed
      df = pd.read_csv(file_path, parse_dates = ['timestamp'])

      # Normalize the input graph_name for comparison (lowercase and no underscores)
      target_name_norm = graph_name.lower().replace("_", " ").strip()

      # Find the actual parameter name in the CSV to keep original casing in title
      # We normalize all unique parameters in the file to find a match
      available_params: List[str] = df['parameter'].unique().tolist()
      actual_graph_name = None

      for p in available_params:
        if p.lower().replace("_", " ").strip() == target_name_norm:
          actual_graph_name = p
          break

      if not actual_graph_name:
        raise RuntimeError(f"parameter '{graph_name}' not found in data")

      # Create figure and axis
      plt.figure(figsize = (10, 6))
      ax = plt.gca()

      # Get unit of measurement using the correctly cased parameter name
      sample_data = df[df['parameter'] == actual_graph_name]
      unit_label = ""
      if not sample_data.empty and 'unit' in df.columns:
        unit_val = sample_data['unit'].iloc[0]
        if pd.notna(unit_val):
          unit_label = f" [{unit_val}]"

      if inverter == "combined":
        # Logic for comparing multiple physical inverters on one plot
        physical_units = [inv for inv in df['inverter'].unique() if inv != 'all']
        for unit in physical_units:
          unit_data = df[(df['inverter'] == unit) & (df['parameter'] == actual_graph_name)]
          if not unit_data.empty:
            plt.plot(unit_data['timestamp'], unit_data['value'], label = unit)
        plt.title(f"Comparison: {actual_graph_name}{unit_label} ({graph_date})")
      else:
        # Logic for a single inverter
        plot_data = df[(df['inverter'] == inverter) & (df['parameter'] == actual_graph_name)]
        if plot_data.empty:
          plt.close()
          raise RuntimeError(f"plot data for {inverter} is empty")

        plt.plot(plot_data['timestamp'], plot_data['value'], label = actual_graph_name, color = 'orange')
        plt.title(f"{inverter.upper()}: {actual_graph_name}{unit_label} ({graph_date})")

      # Configure X-axis time format and grid intervals
      time_min: datetime = df['timestamp'].min()
      time_max: datetime = df['timestamp'].max()
      time_delta = (time_max - time_min).total_seconds()

      left_limit: float = mdates.date2num(time_min)
      right_limit: float = mdates.date2num(time_max)

      # Remove empty space on the sides
      ax.set_xlim(left_limit, right_limit)

      # Define intervals based on time span
      if time_delta < 3 * 3600:
        # Major: 0, 15, 30, 45
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute = [0, 15, 30, 45]))
        # Minor: 5, 10, 20, 25, 35, 40, 50, 55 (excluding major points)
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute = [5, 10, 20, 25, 35, 40, 50, 55]))
      elif time_delta < 7 * 3600:
        # Major: 0, 30
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute = [0, 30]))
        # Minor: 10, 20, 40, 50 (excluding 0 and 30)
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute = [10, 20, 40, 50]))
      else:
        # Major: Every 2 hours (at 00 minutes)
        ax.xaxis.set_major_locator(mdates.HourLocator(interval = 2))
        # Minor: Only at 30 minutes, or every hour except the major ones
        # Here we use an interval of 1 hour for minor, but it will overlap.
        # Better: set minor specifically to 1-hour steps or 30-min steps
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute = [0, 30]))
        # Note: Even with overlap, 'major' usually takes visual precedence
        # if you draw it AFTER or with higher Z-order, but let's be precise:

      ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

      # Generation time watermark
      gen_time = datetime.now().strftime("Generated: %Y-%m-%d %H:%M:%S")
      plt.figtext(0.99, 0.01, gen_time, fontsize = 7, color = 'black', ha = 'right', va = 'bottom')

      # Basic styling
      plt.grid(True, which = 'major', linestyle = '--', alpha = 0.7)
      plt.grid(True, which = 'minor', linestyle = ':', alpha = 0.4)
      plt.legend(loc = 'upper left', fontsize = 10, framealpha = 0.8)
      plt.xticks(rotation = 0)

      # Layout adjustment to prevent clipping
      plt.tight_layout(rect = (0, 0.021, 1, 1))

      # Save to memory buffer
      buf = io.BytesIO()
      plt.savefig(buf, format = 'png', dpi = 300)
      buf.seek(0)
      plt.close()

      return buf.getvalue()

    except Exception as e:
      plt.close()
      self._logger.error(f"Error generating graph for {graph_date}/{inverter}/{graph_name}: {e}")
      raise
