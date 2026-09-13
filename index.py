import sys
import os

# Menambahkan root folder project ke sys.path agar modul lokal (app, database) dapat di-import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Entry point Vercel Serverless Function
if __name__ == '__main__':
    app.run()
