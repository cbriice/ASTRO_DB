#!/bin/bash
gunicorn apptest:app.server --bind 0.0.0.0:8050
