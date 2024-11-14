import os
import logging
import asyncio
from asgiref.sync import sync_to_async
import django
from django.core.wsgi import get_wsgi_application

# Django Application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecormmerceBot.settings')
django_application = get_wsgi_application()
django.setup()


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, Updater, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from django.core.exceptions import ObjectDoesNotExist
from BotCommerce.models import Category, Product, Purchase


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Bot token
BOT_TOKEN = '7618359397:AAG7MC--oYQzhEmy4echw6Gjv4uGbVJYCXo'

# Bank details
BANK_DETAILS = """
Bank Name: Precious Ferrarri Bank
Account Number: 1234567890
Account Name: Beautiful Lucifer
"""


# Start command handler
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Categories", callback_data='categories')],
        [InlineKeyboardButton("Search", callback_data='search')],
        [InlineKeyboardButton("Quit", callback_data='quit')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to the store! Choose an option:', reply_markup=reply_markup)

# Handle categories display
async def show_categories(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Fetch categories asynchronously using sync_to_async
    categories = await sync_to_async(lambda: list(Category.objects.all()))()

    if categories:  # Check if there are any categories
        keyboard = [
            [InlineKeyboardButton(category.name, callback_data=f'category_{category.id}')]
            for category in categories
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data='start')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Ensure you await edit_message_text
        await query.edit_message_text("Select a category:", reply_markup=reply_markup)
    else:
        await query.edit_message_text("No categories available. Please check back later.")

def get_product_info(product):
    """Return formatted product information"""
    return f"{product.name} - ₦{product.price:.2f} (Stock: {product.stock})"

# Display products in a selected category
async def show_products_in_category(update: Update, context: CallbackContext) -> None:
    """Handle category selection and display products"""
    query = update.callback_query
    await query.answer()

    try:
        category_name = query.data.split('_')[1]
    except IndexError:
        await query.edit_message_text("Invalid category ID.")
        return
    except Exception as e:
        await query.edit_message_text(f"Error: {str(e)}")
        return

    # Use sync_to_async for ORM calls
    products = await sync_to_async(Product.objects.filter)(category=category_name)

    # Check if products exist using sync_to_async
    if await sync_to_async(products.exists)():
        message = "Available Products:\n"
        # Use sync_to_async for ORM iteration
        products_list = await sync_to_async(list)(products)

        for product in products_list:
            message += f"\n{get_product_info(product)}"

        # Add button to purchase products
        keyboard = [
            [InlineKeyboardButton(product.name, callback_data=f'purchase_{product.id}') for product in products_list],
            [InlineKeyboardButton("Back", callback_data='categories')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(text=message, reply_markup=reply_markup)
        except Exception as e:
            await query.edit_message_text(f"Error: {str(e)}")
    else:
        await query.edit_message_text("No products available in this category.")


# Handle product search
# Handle search button click
async def search_products_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please type the name of the product you're looking for:")


# Handle search input
async def search_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    search_query = update.message.text.lower()

    try:
        products = await sync_to_async(Product.objects.filter)(name__icontains=search_query)
    except Exception as e:
        update.message.reply_text(f"Error searching products: {str(e)}")
        return

    if products.exists():
        message = f"Search results for '{search_query}':\n"
        keyboard = []
        for product in products:
            if product.stock > 0:
                message += f"\n{product.name} - ₦{product.price:.2f} (Stock: {product.stock})"
                keyboard.append([InlineKeyboardButton(product.name, callback_data=f'purchase_{product.id}')])

        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text=message, reply_markup=reply_markup)
        else:
            update.message.reply_text("Products found, but all are currently out of stock.")
    else:
        update.message.reply_text(f"No products found matching '{search_query}'.")


# Handle purchase request
async def purchase_product(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    try:
        product_id = query.data.split('_')[1]
        product = await sync_to_async(Product.objects.get)(id=product_id)
    except IndexError:
        await query.edit_message_text("Invalid product ID.")
        return
    except Exception as e:
        await query.edit_message_text(f"Error: {str(e)}")
        return

    # If stock is available
    if product.stock > 0:
        # Reduce stock count
        product.stock -= 1
        await sync_to_async(product.save)()

        message = f"You are about to purchase {product.name} for ₦{product.price:.2f}.\n\n"
        message += "Please make the payment to the following bank details:\n"
        message += BANK_DETAILS

        # Provide "Done" option
        keyboard = [[InlineKeyboardButton("Done", callback_data=f'done_{product.id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=message, reply_markup=reply_markup)
    else:
        await query.edit_message_text("Sorry, this product is out of stock.")


async def payment_done(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Thank you! Your payment has been processed.")
    await query.edit_message_reply_markup(None)


# Quit handler
async def quit(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Thank you for visiting. Goodbye!")


# Handlers
# Telegram Application
telegram_application = ApplicationBuilder().token(BOT_TOKEN).read_timeout(60).connect_timeout(60).build()
telegram_application.add_handler(CommandHandler('start', start))

# Callback query handlers
telegram_application.add_handler(CallbackQueryHandler(show_categories, pattern='categories'))
telegram_application.add_handler(CallbackQueryHandler(search_products_prompt, pattern='search'))
telegram_application.add_handler(CallbackQueryHandler(quit, pattern='quit'))
telegram_application.add_handler(CallbackQueryHandler(show_products_in_category, pattern=r'^category_\d+'))
telegram_application.add_handler(CallbackQueryHandler(purchase_product, pattern=r'^purchase_\d+'))
telegram_application.add_handler(CallbackQueryHandler(payment_done, pattern=r'^done_\d+'))

# Message handler for search
telegram_application.add_handler(MessageHandler(filters.TEXT, search_products))



# Main bot function
def main():
    try:
        logging.info("Bot started")
        telegram_application.run_polling()
    
    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()