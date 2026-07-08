#!/bin/bash

# Terminate background processes on script exit
trap 'kill $(jobs -p)' EXIT

echo "⚡ Starting Spark Practice Hub..."

# 1. Start Django Backend Server
echo "🚀 Launching Django backend API at http://localhost:8000/api/..."
.venv/bin/python backend/manage.py runserver 0.0.0.0:8000 &

# Wait for backend to start up
sleep 2

# 2. Start React Frontend Dev Server
echo "💻 Launching React frontend at http://localhost:5173/..."
npm --prefix frontend run dev

# Keep script running
wait
