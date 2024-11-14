import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecormmerceBot.settings')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecormmerceBot.settings')

application = get_wsgi_application()
django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, Updater, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from BotCommerce.models import Category, Product, Purchase

# Load Django models

#application = get_wsgi_application()



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
def show_categories(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    categories = Category.objects.all()
    if categories.exists():
        keyboard = [[InlineKeyboardButton(category.name, callback_data=f'category_{category.id}')] for category in categories]
        keyboard.append([InlineKeyboardButton("Back", callback_data='start')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Select a category:", reply_markup=reply_markup)
    else:
        query.edit_message_text("No categories available. Please check back later.")

# Display products in a selected category
def show_products_in_category(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    category_id = query.data.split('_')[1]
    products = Product.objects.filter(category_id=category_id)

    if products.exists():
        message = "Available Products:\n"
        for product in products:
            message += f"\n{product.name} - ₦{product.price:.2f} (Stock: {product.stock})"

        # Add button to purchase products
        keyboard = [[InlineKeyboardButton(product.name, callback_data=f'purchase_{product.id}') for product in products]]
        keyboard.append([InlineKeyboardButton("Back", callback_data='categories')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=message, reply_markup=reply_markup)
    else:
        query.edit_message_text("No products available in this category.")

# Handle product search
def search_products_prompt(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text("Please type the name of the product you want to search for:")

def search_products(update: Update, context: CallbackContext) -> None:
    search_query = update.message.text
    products = Product.objects.filter(name__icontains=search_query)

    if products.exists():
        message = "Search Results:\n"
        for product in products:
            message += f"\n{product.name} - ₦{product.price:.2f} (Stock: {product.stock})"

        # Add button to purchase products
        keyboard = [[InlineKeyboardButton(product.name, callback_data=f'purchase_{product.id}') for product in products]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=message, reply_markup=reply_markup)
    else:
        update.message.reply_text("No products found with that name.")

# Handle purchase request
def purchase_product(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    product_id = query.data.split('_')[1]
    product = Product.objects.get(id=product_id)

    # If stock is available
    if product.stock > 0:
        # Create purchase entry
        purchase = Purchase.objects.create(product=product, user_id=query.from_user.id)

        message = f"You are about to purchase {product.name} for ₦{product.price:.2f}.\n\n"
        message += "Please make the payment to the following bank details:\n"
        message += BANK_DETAILS

        # Provide "I've Paid" option
        keyboard = [[InlineKeyboardButton("I've Paid", callback_data=f'paid_{purchase.id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(text=message, reply_markup=reply_markup)
    else:
        query.edit_message_text("Sorry, this product is out of stock.")

# Handle payment confirmation
def confirm_payment(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    purchase_id = query.data.split('_')[1]
    purchase = Purchase.objects.get(id=purchase_id)

    # Change status to PAID
    purchase.status = 'PAID'
    purchase.save()

    message = "Thank you for your payment. Please upload your receipt."
    query.edit_message_text(text=message)

# Handle receipt upload
def handle_receipt_upload(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    purchase = Purchase.objects.filter(user_id=user_id, status='PAID').first()

    if purchase:
        # Save receipt image
        file = update.message.photo[-1].get_file()
        file_path = f'receipts/{purchase.id}.jpg'
        file.download(file_path)

        # Update the purchase with the receipt image
        purchase.receipt_image = file_path
        purchase.status = 'COMPLETED'
        purchase.save()

        # Update stock
        product = purchase.product
        product.stock -= 1
        product.save()

        # Send confirmation
        update.message.reply_text(f"Purchase completed! Your receipt has been uploaded.")
    else:
        update.message.reply_text("No pending payment found.")

# Quit handler
def quit(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="Thank you for visiting. Goodbye!")

# Main bot function
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(show_categories, pattern='categories'))
    application.add_handler(CallbackQueryHandler(quit, pattern='quit'))
    application.add_handler(CallbackQueryHandler(show_products_in_category, pattern=r'^category_\d+'))
    application.add_handler(CallbackQueryHandler(purchase_product, pattern=r'^purchase_\d+'))
    application.add_handler(CallbackQueryHandler(confirm_payment, pattern=r'^paid_\d+'))

    # Message handler for search
    application.add_handler(CallbackQueryHandler(search_products_prompt, pattern='search'))
    #application.add_handler(MessageHandler(filters.Text & ~filters.command, search_products))

    # Message handler for receipt upload - fix this
    #application.add_handler(MessageHandler(filters.Photo, handle_receipt_upload))

    application.run_polling()

main()