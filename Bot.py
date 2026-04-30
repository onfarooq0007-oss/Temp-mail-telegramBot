import os import requests from telegram import Update, ReplyKeyboardMarkup from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv('BOT_TOKEN', 'PASTE_YOUR_TOKEN_HERE') BASE = 'https://api.mail.tm' user_data_store = {}

KEYBOARD = ReplyKeyboardMarkup([ ['/start', '/gen'], ['/inbox', '/del'], ['/help', '/me'] ], resize_keyboard=True)

def get_domains(): r = requests.get(f'{BASE}/domains') r.raise_for_status() data = r.json().get('hydra:member', []) return data[0]['domain'] if data else 'mail.tm'

def create_account(address, password): r = requests.post(f'{BASE}/accounts', json={'address': address, 'password': password}) r.raise_for_status() return r.json()

def get_token(address, password): r = requests.post(f'{BASE}/token', json={'address': address, 'password': password}) r.raise_for_status() return r.json()['token']

def get_messages(token): r = requests.get(f'{BASE}/messages', headers={'Authorization': f'Bearer {token}'}) r.raise_for_status() return r.json().get('hydra:member', [])

def get_message(token, mid): r = requests.get(f'{BASE}/messages/{mid}', headers={'Authorization': f'Bearer {token}'}) r.raise_for_status() return r.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text('Welcome to Temp Mail Bot!\nUse buttons or commands below.', reply_markup=KEYBOARD)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): txt = ('Commands:\n' '/gen - generate new temp email\n' '/inbox - check inbox\n' '/del - delete saved mailbox\n' '/me - show current email\n' '/help - show help') await update.message.reply_text(txt, reply_markup=KEYBOARD)

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id domain = get_domains() import random, string name = 'user' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) password = ''.join(random.choices(string.ascii_letters + string.digits, k=12)) address = f'{name}@{domain}' try: create_account(address, password) token = get_token(address, password) user_data_store[uid] = {'email': address, 'password': password, 'token': token} await update.message.reply_text(f'New Email Created:\n{address}', reply_markup=KEYBOARD) except Exception as e: await update.message.reply_text(f'Error: {e}')

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id if uid in user_data_store: await update.message.reply_text('Current Email: ' + user_data_store[uid]['email']) else: await update.message.reply_text('No mailbox. Use /gen')

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id if uid not in user_data_store: await update.message.reply_text('No mailbox. Use /gen') return token = user_data_store[uid]['token'] try: msgs = get_messages(token) if not msgs: await update.message.reply_text('Inbox empty.') return out = [] for m in msgs[:10]: detail = get_message(token, m['id']) out.append(f"From: {detail.get('from', {}).get('address', 'Unknown')}\nSubject: {detail.get('subject', '')}\nText: {detail.get('text', '')[:500]}\n---") await update.message.reply_text('\n\n'.join(out)) except Exception as e: await update.message.reply_text(f'Error: {e}')

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE): uid = update.effective_user.id if uid in user_data_store: del user_data_store[uid] await update.message.reply_text('Mailbox deleted from bot memory.') else: await update.message.reply_text('Nothing to delete.')

def main(): app = Application.builder().token(BOT_TOKEN).build() app.add_handler(CommandHandler('start', start)) app.add_handler(CommandHandler('help', help_cmd)) app.add_handler(CommandHandler('gen', gen)) app.add_handler(CommandHandler('me', me)) app.add_handler(CommandHandler('inbox', inbox)) app.add_handler(CommandHandler('del', delete)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start)) print('Bot running...') app.run_polling()

if name == 'main': main()
