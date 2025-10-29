#!/bin/bash

echo "Starting Node A on port 5001..."
export NODE_CONFIG=configs/node_a_config.json
python main.py
