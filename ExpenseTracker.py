import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater, MessageHandler, filters, CallbackContext
import datetime
import csv

conn = sqlite3.connect('expenses.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,       
        amount REAL,
        description TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'{update.effective_user.first_name}, Welcome to the Expense Tracker Bot! Send /add expense to log your expenses.')

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    text = update.message.text.replace('/add', '').strip()
    name = update.effective_user.first_name
    print(name)

    try:
        amount, description = map(str.strip, text.split(' ', 1))
        amount = float(amount)
    except ValueError:
        await update.message.reply_text('Invalid input. Please use /add <amount> <description>')
        return

    cursor.execute('INSERT INTO expenses (user_id, amount, name, description) VALUES (?, ?, ?, ?)', (user_id, amount, name,  description))
    conn.commit()

    if (amount<0):
        await update.message.reply_text(f' {amount} Subtract successfully!')
    else:    
        await update.message.reply_text(f'Expense of {amount} added successfully!')

async def list_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    cursor.execute('SELECT amount, description, timestamp FROM expenses WHERE user_id=?', (user_id,))
    expenses = cursor.fetchall()

    if not expenses:
        await update.message.reply_text('No expenses found.')
        return

    message = "Your expenses:\n"
    for expense in expenses:
        amount, description, timestamp = expense
        message += f"{timestamp}: {description} - {amount}\n"

    await update.message.reply_text(message)

async def generate_csv(update: Update, context: CallbackContext) -> None:
    cursor.execute('SELECT * FROM expenses')
    rows = cursor.fetchall()

    with open('expense.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
      
        csv_writer.writerow(['Sno.','Your ID', 'Name', 'Amount', 'Description', 'Time'])

        csv_writer.writerows(rows)

    await update.message.reply_document(document=open('expense.csv', 'rb'))    
    

async def clear_expenses(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute('DELETE FROM expenses WHERE user_id=?', (user_id,))
    conn.commit()

    await update.message.reply_text('All expenses cleared successfully!')

async def monthly_summary(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    first_day_of_month = datetime.date.today().replace(day=1)
    cursor.execute('SELECT SUM(amount) FROM expenses WHERE user_id=? AND timestamp >= ? AND timestamp < ?', (user_id, first_day_of_month, first_day_of_month + datetime.timedelta(days=32)))
    total_amount = cursor.fetchone()[0]

    if total_amount is not None:
        await update.message.reply_text(f'Your total expenses for this month: {total_amount}')
    else:
        await update.message.reply_text('No expenses found for this month.')

app = ApplicationBuilder().token("6728770002:AAGnIvilElJcPNIp9KsDnMcx_k0Lu0O2jtg").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_expense))
app.add_handler(CommandHandler("list", list_expenses))
app.add_handler(CommandHandler("Delete", clear_expenses))
app.add_handler(CommandHandler("Monthly", monthly_summary))
app.add_handler(CommandHandler("generatecsv", generate_csv))

app.run_polling()