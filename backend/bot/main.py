from typing import Final
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN: Final = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME: Final = os.getenv('BOT_USERNAME')
API_URL: Final = os.getenv('API_URL', 'http://localhost:8000')

# Store user preferences for notifications
notification_users = set()

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm the Real Estate Bot. How can I help you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """I'm here to help you with your real estate needs. Here are the commands you can use:
/start - Start the bot
/help - Show this help message
/noti <email> - Register to receive content of interest
/cancel <email> - Cancel receiving suggested daily news
/predict <area> <bedrooms> <bathrooms> <location> - Estimate the price of real estate"""
    await update.message.reply_text(help_text)

async def noti_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide your email address: /noti your.email@example.com")
        return
    
    email = context.args[0]
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_URL}/subscribe", json={"email": email}) as response:
                if response.status == 200:
                    await update.message.reply_text("You have been registered for notifications! You will receive daily updates about real estate content of interest.")
                else:
                    await update.message.reply_text("Failed to register for notifications. Please try again later.")
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {str(e)}")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide your email address: /cancel your.email@example.com")
        return
    
    email = context.args[0]
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(f"{API_URL}/unsubscribe/{email}") as response:
                if response.status == 200:
                    await update.message.reply_text("You have been unsubscribed from notifications.")
                else:
                    await update.message.reply_text("Failed to unsubscribe. Please try again later.")
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {str(e)}")

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        await update.message.reply_text(
            "Please provide all required information:\n"
            "/predict <area> <bedrooms> <bathrooms> <location>\n"
            "Example: /predict 100 2 2 Hanoi"
        )
        return
    
    try:
        area = float(context.args[0])
        bedrooms = int(context.args[1])
        bathrooms = int(context.args[2])
        location = ' '.join(context.args[3:])
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_URL}/predict",
                json={
                    "area": area,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "location": location
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    price = result["estimated_price"]
                    response_text = f"""Estimated price for your property:
- Area: {area}m²
- Bedrooms: {bedrooms}
- Bathrooms: {bathrooms}
- Location: {location}
Estimated price: {price:,.2f} VND

Note: This is an estimation based on current market data."""
                    await update.message.reply_text(response_text)
                else:
                    await update.message.reply_text("Failed to get price prediction. Please try again later.")
    except ValueError:
        await update.message.reply_text(
            "Invalid format. Please use: /predict <area> <bedrooms> <bathrooms> <location>\n"
            "Example: /predict 100 2 2 Hanoi"
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.reply_text("This is a custom command, you can add any funtionality you want")


# Errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


def handle_response(text: str) -> str:
    processed: str = text.lower()
    if 'hello' in processed:
        return 'Hey there!'
    
    if 'how are you' in processed:
        return 'I\'m good, thanks for asking!'
    
    return 'I don\'t understand'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: {text}')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
        
    print(f'Bot response: {response}')

    await update.message.reply_text(response)


if __name__ == '__main__':
    print('Starting bot...')
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('noti', noti_command))
    app.add_handler(CommandHandler('cancel', cancel_command))
    app.add_handler(CommandHandler('predict', predict_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print('Polling...')
    app.run_polling(poll_interval=3) 
    
            
            

    
    