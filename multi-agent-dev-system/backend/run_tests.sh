#!/bin/bash

# Run tests with coverage
echo "Running pytest with coverage..."
python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Check exit code
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed!"
    exit 1
fi