from env_var import EnvVar
from env_utils import EnvUtils

class EnvVars:
  DEYE_LOG_NAME = EnvVar(
    name = EnvUtils.DEYE_LOG_NAME,
    default = '',
    description = 'Individual folder name for logging',
    value_getter = EnvUtils.get_log_name,
  )

  DEYE_DATA_COLLECTOR_DIR = EnvVar(
    name = EnvUtils.DEYE_DATA_COLLECTOR_DIR,
    default = '',
    description = 'Directory for data files',
    value_getter = EnvUtils.get_deye_data_collector_dir,
  )

  DEYE_GRAPHS_DIR = EnvVar(
    name = EnvUtils.DEYE_GRAPHS_DIR,
    default = '',
    description = 'Directory for graph files',
    value_getter = EnvUtils.get_deye_graphs_dir,
  )

  REMOTE_GRAPH_SERVER_URL = EnvVar(
    name = EnvUtils.REMOTE_GRAPH_SERVER_URL,
    default = '',
    description = 'Remote graph server URL',
    value_getter = EnvUtils.get_remote_graph_server_url,
  )

  DEYE_GRAPHS_FORMAT = EnvVar(
    name = EnvUtils.DEYE_GRAPHS_FORMAT,
    default = '',
    description = 'Format for graph files',
    value_getter = EnvUtils.get_deye_graphs_format,
  )
