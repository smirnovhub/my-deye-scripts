import os
import io
import gc
import logging
import zipfile

import matplotlib
# Use Agg backend for non-interactive PNG generation
# Should be BEFORE import matplotlib.pyplot as plt
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.transforms import ScaledTranslation
from matplotlib.backends.backend_pdf import PdfPages

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import date, datetime

from debug_timer import DebugTimerWithLog
from deye_graph_data import DeyeGraphData
from deye_file_with_lock import DeyeFileWithLock
from deye_graph_inverters import DeyeGraphInverters
from deye_graph_inverter_data import DeyeGraphInverterData
from deye_graph_group_data import DeyeGraphGroupData
from src.deye_graph_server_config import DeyeGraphServerConfig

class DeyeGraphManager:
  def __init__(
    self,
    config: DeyeGraphServerConfig,
    logger: logging.Logger,
  ):
    self._config = config
    self._logger = logger
    self._data_path = f"data/{config.DEYE_DATA_COLLECTOR_DIR}"

    base_dir = Path(self._data_path)

    if not base_dir.is_dir():
      raise RuntimeError(f"Data dir '{self._data_path}' doesn't exist")

    self._thresholds = self._get_thresholds(self._data_path)

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
      with DeyeFileWithLock(file_path, "r") as f:
        df = pd.read_csv(f)

      result: List[DeyeGraphInverterData] = []

      # Get list of physical units (master, slave1, slave2, etc.)
      # We exclude 'all' to handle it as a separate category
      all_units = df['inverter'].unique()
      physical_inverters = [inv for inv in all_units if inv != 'all']

      # Temporary storage for register sets to calculate intersection later
      physical_params_map = {}

      # Process each physical inverter and collect all its available registers
      for inv in sorted(physical_inverters):
        # Filter dataframe for this specific unit
        inv_df = df.loc[df['inverter'] == inv]
        unit_params: List[str] = sorted(list(inv_df['register'].unique()))
        physical_params_map[inv] = set(unit_params)

        # Append full data object with grouped graphs
        result.append(DeyeGraphInverterData(inverter = inv, groups = self._get_graph_data(inv_df)))

      # Handle 'all' (aggregated system data) separately if present
      if 'all' in all_units:
        all_inv_df = df.loc[df['inverter'] == 'all']
        if isinstance(all_inv_df, pd.DataFrame):
          result.append(DeyeGraphInverterData(inverter = 'all', groups = self._get_graph_data(all_inv_df)))

      # Calculate 'combined' graphs (intersection of ALL physical inverters)
      # This allows side-by-side comparison of shared metrics
      if len(physical_inverters) > 1:
        # Start with registers of the first physical inverter
        common_set = physical_params_map[physical_inverters[0]]

        # Intersect with registers of all other physical units
        for inv in physical_inverters[1:]:
          common_set = common_set.intersection(physical_params_map[inv])

        # If common registers exist, add a virtual 'combined' inverter entry
        if common_set:
          cs_df = df.loc[df['register'].isin(common_set)].drop_duplicates(subset = ['register'])
          result.append(DeyeGraphInverterData(inverter = "combined", groups = self._get_graph_data(cs_df)))

      return DeyeGraphInverters(
        graph_date = graph_date,
        inverters = result,
      )

    except Exception as e:
      # Log error details if file is corrupted or column names are missing
      self._logger.error(f"Error processing {file_name}: {e}")
      raise

  def _get_graph_data(self, df: pd.DataFrame) -> List[DeyeGraphGroupData]:
    # Ensure we use unique rows to avoid duplicate graph definitions
    unique_df = df.drop_duplicates(subset = ['register'])

    # Group by the 'group' column
    grouped = unique_df.groupby('group')

    group_results: List[DeyeGraphGroupData] = []

    for group_name, group_df in grouped:
      graphs_in_group: List[DeyeGraphData] = []

      for _, row in group_df.iterrows():
        # Original logic for name and description
        graphs_in_group.append(
          DeyeGraphData(name = str(row['register']).replace(" ", "_").lower(), description = str(row['register'])))

      group_results.append(DeyeGraphGroupData(group = str(group_name), graphs = graphs_in_group))

    return group_results

  def _get_color(self, name: str) -> str:
    # Define fixed colors for specific inverter types
    color_map = {
      'master': 'steelblue',
      'all': 'forestgreen',
      'slave': 'orange',
    }

    for inverter, color in color_map.items():
      if name.startswith(inverter):
        return color

    return "steelblue"

  def _prepare_figure_object(
    self,
    df: pd.DataFrame,
    graph_date: date,
    inverter: str,
    graph_name: str,
  ) -> Figure:
    # Normalize the input graph_name for comparison (lowercase and no underscores)
    target_name_norm = graph_name.lower().replace("_", " ").strip()

    threshold = self._thresholds.get(target_name_norm)

    if threshold is not None:
      with DebugTimerWithLog("Trimming data"):
        df = self._trim_by_register(
          df = df,
          graph_name = target_name_norm,
          threshold = threshold,
        )

    graph_line_width = 1.5

    # Find the actual register name in the CSV to keep original casing in title
    available_params: List[str] = df['register'].unique().tolist()
    actual_graph_name = None

    for p in available_params:
      if p.lower().replace("_", " ").strip() == target_name_norm:
        actual_graph_name = p
        break

    if not actual_graph_name:
      raise RuntimeError(f"register '{graph_name}' not found in data")

    # Create figure and axis with A4 proportions
    # Use Figure object directly to avoid global state memory leaks
    fig = Figure(figsize = (297 / 25.4, 210 / 25.4))
    ax = fig.add_subplot(111)

    # Make plot border (spines) thicker
    spine_width = 1.3
    for spine in ax.spines.values():
      spine.set_linewidth(spine_width)
      spine.set_zorder(10)

    # Get unit of measurement using the correctly cased register name
    sample_data = df[df['register'] == actual_graph_name]
    unit_label = ""
    if not sample_data.empty and 'unit' in df.columns:
      unit_val = sample_data['unit'].iloc[0]
      if pd.notna(unit_val):
        unit_label = f", {unit_val.replace('deg', '°C')}"

    if inverter == "combined":
      # Logic for comparing multiple physical inverters on one plot
      physical_units = [inv for inv in df['inverter'].unique() if inv != 'all']
      for unit in physical_units:
        unit_data = df[(df['inverter'] == unit) & (df['register'] == actual_graph_name)]
        if not unit_data.empty:
          with DebugTimerWithLog("Plot combined graph"):
            ax.plot(
              unit_data['timestamp'],
              unit_data['value'],
              label = unit,
              linewidth = graph_line_width,
              color = self._get_color(unit),
              zorder = 5 if unit == 'master' else 3,
            )

      ax.set_title(f"{graph_date} {actual_graph_name}{unit_label}", fontsize = 15, pad = 10)
    else:
      # Logic for a single inverter
      plot_data = df[(df['inverter'] == inverter) & (df['register'] == actual_graph_name)]
      if plot_data.empty:
        raise RuntimeError(f"plot data for {inverter} is empty")

      with DebugTimerWithLog("Plot regular graph"):
        ax.plot(
          plot_data['timestamp'],
          plot_data['value'],
          label = inverter,
          color = self._get_color(inverter),
          linewidth = graph_line_width,
        )

      ax.set_title(f"{graph_date} {actual_graph_name}{unit_label}", fontsize = 15, pad = 10)

    # Configure X-axis time format and grid intervals
    time_min: datetime = df['timestamp'].min()
    time_max: datetime = df['timestamp'].max()
    time_delta = (time_max - time_min).total_seconds()

    # Raise error if there is not enough data to form an interval
    if pd.isna(time_min) or pd.isna(time_max) or time_min == time_max:
      raise RuntimeError(f"not enough data points for {graph_date} to build a time interval")

    left_limit: float = mdates.date2num(time_min)
    right_limit: float = mdates.date2num(time_max)

    # Remove empty space on the sides
    ax.set_xlim(left_limit, right_limit)

    major_locator: mdates.DateLocator

    # Define intervals based on time span
    if time_delta < 3600:
      major_locator = mdates.MinuteLocator(byminute = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
      ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval = 1))
    elif time_delta < 3 * 3600:
      major_locator = mdates.MinuteLocator(byminute = [0, 15, 30, 45])
      ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute = [5, 10, 20, 25, 35, 40, 50, 55]))
    elif time_delta < 7 * 3600:
      major_locator = mdates.MinuteLocator(byminute = [0, 30])
      ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute = [10, 20, 40, 50]))
    else:
      major_locator = mdates.HourLocator(interval = 1)
      ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute = [30]))

    # Add start and end times, but filter standard ticks that are too close (15 min threshold)
    if time_delta < 3600:
      min_dist = 5 / (24 * 60) # 5 minutes threshold for short spans
    else:
      min_dist = 15 / (24 * 60) # 15 minutes threshold for long spans

    std_ticks = major_locator.tick_values(time_min, time_max) # type: ignore
    final_ticks = [t for t in std_ticks if abs(t - left_limit) > min_dist and abs(t - right_limit) > min_dist]
    final_ticks.extend([left_limit, right_limit])

    ax.set_xticks(sorted(final_ticks))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Generation time watermark
    gen_time = datetime.now().strftime("Generated: %Y-%m-%d %H:%M:%S")
    ax.set_xlabel(gen_time, fontsize = 7, color = 'black', loc = 'right', labelpad = 15)

    # Basic styling
    ax.grid(True, which = 'major', linestyle = '--', alpha = 0.84)
    ax.grid(True, which = 'minor', linestyle = ':', alpha = 0.6)
    ax.legend(loc = 'upper left', fontsize = 10, framealpha = 0.8)

    # Applying tick parameters via axis object
    ax.tick_params(axis = 'x', rotation = 90, labelsize = 9)
    ax.tick_params(axis = 'y', rotation = 0, labelsize = 9)

    # Apply a fine-tuned horizontal offset (in points) to align X-axis labels perfectly
    offset = ScaledTranslation(1 / 72, 0, fig.dpi_scale_trans)
    for label in ax.get_xticklabels():
      label.set_transform(label.get_transform() + offset)

    # --- Y-axis limits logic ---
    # Get all y-values to find absolute min and max for the current plot
    all_y_values = [] # type: ignore
    for line in ax.get_lines():
      all_y_values.extend(line.get_ydata()) # type: ignore

    if all_y_values:
      y_min_val = min(all_y_values)
      y_max_val = max(all_y_values)

      # Get default ticks that Matplotlib calculated
      std_y_ticks = ax.get_yticks()

      # Set threshold for Y-axis (e.g., 5% of range) to avoid overlapping
      y_range = y_max_val - y_min_val if y_max_val != y_min_val else 1
      y_threshold = y_range * 0.05

      # Filter out standard ticks too close to our boundaries
      final_y_ticks = [t for t in std_y_ticks if abs(t - y_min_val) > y_threshold and abs(t - y_max_val) > y_threshold]

      final_y_ticks.extend([y_min_val, y_max_val])
      ax.set_yticks(sorted(final_y_ticks))

      # --- Prevention of Y-min and X-min collision ---
      # If the lowest Y-label is too close to the X-axis,
      # Matplotlib usually handles it, but we can pad the Y-axis slightly
      ax.set_ylim(y_min_val - (y_range * 0.02), y_max_val + (y_range * 0.02))

    # Layout adjustment to prevent clipping
    fig.tight_layout(pad = 1.5)
    return fig

  def generate_graph_image(
    self,
    graph_date: date,
    inverter: str,
    graph_name: str,
    format: str,
  ) -> bytes:
    # Construct file path from date
    file_name = f"{graph_date.isoformat()}.csv"
    file_path = os.path.join(self._data_path, file_name)

    if not os.path.exists(file_path):
      raise RuntimeError(f"data file for date {graph_date.isoformat()} not found")

    fig: Optional[Figure] = None

    # Load data and ensure timestamp is parsed
    with DebugTimerWithLog("CSV reading"):
      with DeyeFileWithLock(file_path, "r") as f:
        df = pd.read_csv(f, parse_dates = ['timestamp'])

    # Set font type to 42 (TrueType) to enable text search and embedding
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['pdf.compression'] = 9

    metadata = {
      "Title": f"Deye Inverter Graph for {graph_date}",
      "Author": "Dimitras Papandopoulos",
      "Subject": f"Inverter: {inverter}, Register: {graph_name}",
      "Keywords": "Deye, Solar, PV, Python, Matplotlib"
    }

    buf = io.BytesIO()
    fig: Optional[Figure] = None

    try:
      fig = self._prepare_figure_object(
        df = df,
        graph_date = graph_date,
        inverter = inverter,
        graph_name = graph_name,
      )

      # Save to memory buffer
      with DebugTimerWithLog(f"Image {format} generation"):
        fig.savefig(
          buf,
          format = format,
          dpi = 300,
          metadata = metadata,
        )

        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
      self._logger.error(f"Error generating graph for {graph_date}/{inverter}/{graph_name}: {e}")
      raise
    finally:
      # Explicitly clean up figure and call garbage collector
      if fig:
        fig.clear()

      buf.close()

      with DebugTimerWithLog("Cleanup & GC"):
        plt.close('all')
        gc.collect()

  def generate_full_report_pdf(self, graph_date: date) -> bytes:
    """
    Generates a single multipage PDF using the internal plotting logic.
    """
    # Set font type to 42 (TrueType) to enable text search and embedding
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['pdf.compression'] = 9

    # Construct file path from date
    file_name = f"{graph_date.isoformat()}.csv"
    file_path = os.path.join(self._data_path, file_name)

    if not os.path.exists(file_path):
      raise RuntimeError(f"data file for date {graph_date.isoformat()} not found")

    fig: Optional[Figure] = None

    # Load data and ensure timestamp is parsed
    with DebugTimerWithLog("CSV reading"):
      with DeyeFileWithLock(file_path, "r") as f:
        df = pd.read_csv(f, parse_dates = ['timestamp'])

    inverters_data = self.get_inverters_by_date(graph_date)

    metadata = {
      "Title": f"Deye Inverter Graphs for {graph_date}",
      "Author": "Dimitras Papandopoulos",
      "Subject": "Deye Full Report PDF",
      "Keywords": "Deye, Solar, PV, Python, Matplotlib"
    }

    buf = io.BytesIO()
    fig: Optional[Figure] = None

    try:
      with DebugTimerWithLog("Full PDF report generation"):
        with PdfPages(buf, keep_empty = False, metadata = metadata) as pdf:
          for inv_info in inverters_data.inverters:
            for group in inv_info.groups:
              for graph in group.graphs:

                fig = None

                try:
                  with DebugTimerWithLog(f"Generate PDF graph for {inv_info.inverter} {graph.name}"):
                    fig = self._prepare_figure_object(
                      df = df,
                      graph_date = graph_date,
                      inverter = inv_info.inverter,
                      graph_name = graph.name,
                    )

                  with DebugTimerWithLog("Adding graph to PDF"):
                    pdf.savefig(fig)
                except Exception:
                  self._logger.error(f"Error generating graph for {graph_date}/{inv_info.inverter}/{graph.name}: {e}")
                  continue
                finally:
                  if fig:
                    with DebugTimerWithLog("Graph data cleanup"):
                      fig.clear()
                      plt.close(fig)

        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
      self._logger.error(f"Error generating full PDF report for {graph_date}: {e}")
      raise
    finally:
      # Explicitly clean up figure and call garbage collector
      if buf:
        buf.close()

      with DebugTimerWithLog("Cleanup & GC"):
        plt.close('all')
        gc.collect()

  def _trim_by_register(
    self,
    df: pd.DataFrame,
    graph_name: str,
    threshold: float,
  ) -> pd.DataFrame:
    df_working: pd.DataFrame = df.copy()
    df_working['temp_norm'] = df_working['register'].str.lower().str.replace("_", " ").str.strip()

    target_rows = df_working[df_working['temp_norm'] == graph_name]

    if not target_rows.empty:
      condition = target_rows['value'] >= threshold
      if condition.any():
        # Physical limits of data in file
        file_min_t = df_working['timestamp'].min()
        file_max_t = df_working['timestamp'].max()

        # Actual activity bounds
        t_start = target_rows.loc[condition.idxmax(), 'timestamp']
        t_end = target_rows.loc[condition[::-1].idxmax(), 'timestamp']

        # Define available rounding intervals in minutes
        trim_intervals = [60, 30, 15, 5]

        # --- LEFT BOUNDARY (Floor to nearest interval) ---
        for mins in trim_intervals:
          # Calculate total minutes from the start of the day
          total_mins = t_start.hour * 60 + t_start.minute
          # Find the nearest boundary to the left (multiple of mins)
          rounded_mins = (total_mins // mins) * mins
          potential_t = t_start.replace(
            hour = rounded_mins // 60,
            minute = rounded_mins % 60,
            second = 0,
            microsecond = 0,
          )

          if potential_t >= file_min_t:
            t_start = potential_t
            break

        # --- RIGHT BOUNDARY (Ceil to nearest interval) ---
        for mins in trim_intervals:
          total_mins = t_end.hour * 60 + t_end.minute
          # Find the nearest boundary to the right (multiple of mins)
          rounded_mins = ((total_mins // mins) + 1) * mins

          # Handle midnight transition (if 1440 mins)
          if rounded_mins >= 1440:
            potential_t = file_max_t
          else:
            potential_t = t_end.replace(
              hour = rounded_mins // 60,
              minute = rounded_mins % 60,
              second = 0,
              microsecond = 0,
            )

          if potential_t <= file_max_t:
            t_end = potential_t
            break

        # Slice the entire dataframe
        df_working = df_working[(df_working['timestamp'] >= t_start) & (df_working['timestamp'] <= t_end)]

    return df_working.drop(columns = ['temp_norm'])

  def get_zipped_csv(self, graph_date: date) -> bytes:
    # Construct file path from date
    file_name = f"{graph_date.isoformat()}.csv"
    file_path = os.path.join(self._data_path, file_name)

    if not os.path.exists(file_path):
      raise RuntimeError(f"data file for date {graph_date.isoformat()} not found")

    # Create an in-memory byte stream
    buffer = io.BytesIO()

    # Create the ZIP archive within the buffer
    with zipfile.ZipFile(buffer, "w", compression = zipfile.ZIP_DEFLATED) as zf:
      # arcname prevents including the full directory structure in the zip
      zf.write(file_path, arcname = file_name)

    # Grab the bytes from the buffer
    return buffer.getvalue()

  def _get_thresholds(self, data_path: str) -> Dict[str, float]:
    try:
      file_path = os.path.join(data_path, "thresholds.csv")
      with DeyeFileWithLock(file_path, "r") as f:
        df = pd.read_csv(f)
      df['register'] = df['register'].str.lower().str.replace("_", " ").str.strip()
      return dict(zip(df['register'], df['threshold']))
    except Exception as e:
      self._logger.error(f"Error loading thresholds.csv: {e}")
      raise
