@echo off
setlocal enabledelayedexpansion

set "DEYE_LOG_NAME=deye_graph_generator_server"
set "REMOTE_GRAPH_SERVER_URL=http://127.0.0.1:1115"
set "DEYE_PNG_GRAPHS_DIR=deye-png-graphs"

python -u deye_graph_generator_server.py
