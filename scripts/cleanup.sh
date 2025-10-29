#!/bin/bash

echo "Cleaning up test data and blockchain files..."

rm -rf db/blockchain_a.json
rm -rf db/blockchain_b.json
rm -rf tests/test_blockchain_a.json
rm -rf tests/test_blockchain_b.json

echo "Cleanup complete."
