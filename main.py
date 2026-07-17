import telebot
import asyncio
import aiohttp
import json
import base64
import random
import re
import os
import string
import time
import uuid
import cv2
import ddddocr
import numpy as np
from datetime import datetime, timedelta, timezone
from telebot.async_telebot import AsyncTeleBot
from aiohttp import web

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8959581714:AAFXvY1jHdpYtdKtH4JJoNtf9mOlRiHYz1k')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '6621715335'))
CHANNEL_ID = os.environ.get('CHANNEL_ID', '-1002364805811')
CHANNEL_LINK = os.environ.get('CHANNEL_LINK', 'https://t.me/+rUbkkAwaEc8zOTI1')
# ============================

bot = AsyncTeleBot(BOT_TOKEN)
user_data = {}
scan_tasks = {}
success_messages = {}
success_texts = {}
limited_messages = {}
limited_texts = {}
captcha_state = {}
session = None
_connector = None
CONCURRENCY = 100
_voucher_sem = None
_start_time = time.monotonic()

# ========== DATABASE (Simple JSON) ==========
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# (Rest of the code remains the same as provided in the original attachment)
