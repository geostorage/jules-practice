@echo off
chcp 65001
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name "PDF文献重命名工具" --collect-all pdfplumber --collect-all pdfminer --collect-all pypdf app.py
pause
