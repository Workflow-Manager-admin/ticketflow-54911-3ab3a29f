#!/bin/bash
cd /home/kavia/workspace/code-generation/ticketflow-54911-3ab3a29f/ticketing_frontend_workspace/ticketing_frontend
npx eslint
ESLINT_EXIT_CODE=$?
npm run build
BUILD_EXIT_CODE=$?
if [ $ESLINT_EXIT_CODE -ne 0 ] || [ $BUILD_EXIT_CODE -ne 0 ]; then
   exit 1
fi

