#!/bin/bash

echo "Starting Node B on port 5002..."
export NODE_CONFIG=configs/node_b_config.json
python main.py
