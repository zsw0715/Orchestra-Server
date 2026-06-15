#!/bin/bash
cd /Users/shenweizhang/Desktop/orchestra_server
source .venv/bin/activate
uvicorn server.main:app --reload
