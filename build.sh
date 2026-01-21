#!/bin/bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
pip install --upgrade pip
pip install -r requirements.txt