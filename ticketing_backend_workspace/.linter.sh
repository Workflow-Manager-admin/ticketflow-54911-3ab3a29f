#!/bin/bash
cd /home/kavia/workspace/code-generation/ticketflow-54911-3ab3a29f/ticketing_backend_workspace/ticketing_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

