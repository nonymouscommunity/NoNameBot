# A very simple Flask Hello World app for you to get started with...

from flask import Flask

# MongoDB Client Connection

from pymongo.mongo_client import MongoClient
from urllib.parse import quote_plus
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
import github
import logging
import os
import sys
import subprocess
from webserver import keep_alive

username = quote_plus(os.environ['username'])
password = quote_plus(os.environ['password'])
cluster = os.environ['cluster']
authSource = os.environ['auth']
uri = 'mongodb+srv://' + username + ':' + password + '@' + cluster + '/?retryWrites=' + authSource
client = MongoClient(uri)
DATABASE_NAME = os.environ['db']
COLLECTION_NAME = os.environ['col']
BOT_TOKEN = os.environ['bot_token']

# Send a ping to confirm a successful connection

try:
  client.admin.command('ping')
  print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
  print(e)

# Testing DB Connection


def get_database():
  return client[DATABASE_NAME]


dbname = get_database()
collection_name = dbname[COLLECTION_NAME]

# Define conversation states
MENU, RESOURCES, CERTIFICATIONS, PATHWAY, SETTINGS = range(5)
BACK = 'back'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log',  # Specify the log file name and path
    filemode='a'  # Append mode, change to 'w' for overwrite
)


# Add a function to read text files
def read_text_file(filename):
  file_path = os.path.join("NoName/", filename)
  with open(file_path, "r") as file:
    return file.read()


welcome = read_text_file('start')
resources = read_text_file('resources')
cert = read_text_file('cert')


def main_menu_keyboard():
  # Create the main menu keyboard
  keyboard = [
      [InlineKeyboardButton("Resources", callback_data='resources')],
      [InlineKeyboardButton("Certifications", callback_data='certifications')],
      [
          InlineKeyboardButton("Request a Feature",
                               callback_data='request_feature')
      ],
      [
          InlineKeyboardButton("Join Community",
                               callback_data='join_community',
                               url='https://t.me/NonymousCommunity')
      ],
      [InlineKeyboardButton("Settings", callback_data='settings')],
  ]
  return InlineKeyboardMarkup(keyboard)


def notification_keyboard(not_check):
  ON_OFF = not_check
  keyboard = [[
      InlineKeyboardButton(f"Notification: {ON_OFF}",
                           callback_data='notification')
  ], [InlineKeyboardButton("Back to Main Menu", callback_data='back')]]
  return InlineKeyboardMarkup(keyboard)


def resources_menu_keyboard():
  # Create the resources menu keyboard
  keyboard = [
      [InlineKeyboardButton("Information Technology", callback_data='it')],
      [InlineKeyboardButton("Cybersecurity", callback_data='cybersecurity')],
      [InlineKeyboardButton("Programming", callback_data='programming')],
      [InlineKeyboardButton("Dark Web", callback_data='dark_web')],
      [InlineKeyboardButton("Pathway", callback_data='pathway')],
      [InlineKeyboardButton("Back to Main Menu", callback_data='back')],
  ]
  return InlineKeyboardMarkup(keyboard)


def certifications_menu_keyboard():
  # Create the certifications menu keyboard
  keyboard = [
      [
          InlineKeyboardButton(
              "Offensive Security Certified Professional (OSCP)",
              callback_data='oscp')
      ],
      [
          InlineKeyboardButton("Practical Network Penetration Tester (PNPT) ",
                               callback_data='pnpt')
      ],
      [InlineKeyboardButton("Back to Main Menu", callback_data='back')],
  ]
  return InlineKeyboardMarkup(keyboard)


def edit_updates_menu_keyboard(query_data):
  github_url = f'https://github.com/nonymouscommunity/NoName/blob/main/{query_data}'
  keyboard = [
      [InlineKeyboardButton("Edit", url=github_url)],
      [InlineKeyboardButton("Back to Main Menu", callback_data='back')],
  ]
  return InlineKeyboardMarkup(keyboard)


def pathway_menu_keyboard():
  keyboard = [
      [InlineKeyboardButton("Hacker Path", callback_data='pathfh')],
      [InlineKeyboardButton("Programmer Path", callback_data='pathfp')],
      [InlineKeyboardButton("Back to Main Menu", callback_data='back')],
  ]
  return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  user_id = user.id
  existing_user = collection_name.find_one({"_id": user_id})
  if existing_user is not None:
    print("You are already registered.")
  else:
    user_data = {
        "_id": user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "announcements": True
    }
    collection_name.insert_one(user_data)
  await update.message.reply_text(welcome,
                                  reply_markup=main_menu_keyboard(),
                                  parse_mode='Markdown')


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  user_id = query.from_user.id
  print(query.data)
  if query.data == 'resources':
    await query.edit_message_text(resources,
                                  reply_markup=resources_menu_keyboard(),
                                  parse_mode='Markdown')
    return RESOURCES
  elif query.data == 'pathway':
    text_file_content = read_text_file(query.data)
    await query.edit_message_text(text_file_content,
                                  reply_markup=pathway_menu_keyboard(),
                                  parse_mode='Markdown')
    return PATHWAY
  elif query.data == 'certifications':
    await query.edit_message_text(cert,
                                  reply_markup=certifications_menu_keyboard(),
                                  parse_mode='Markdown')
    return CERTIFICATIONS
  elif query.data == 'settings':
    user = update.effective_user
    user_id = user.id
    user_document = collection_name.find_one({"_id": user_id})
    if user_document:
      announcements = user_document.get("announcements", False)
      if announcements is True:
        print("announcements set to True.")
        not_check = 'On'
      else:
        print("announcements set to False.")
        not_check = 'Off'
    text_file_content = "Change your settings: "
    await query.edit_message_text(
        text_file_content,
        reply_markup=notification_keyboard(not_check),
        parse_mode='Markdown')
    return SETTINGS
  elif query.data == 'notification':
    user = update.effective_user
    user_id = user.id
    user_document = collection_name.find_one({"_id": user_id})

    if user_document:
      announcements = user_document.get("announcements", False)
      not_check = None  # Initialize not_check

      if announcements is True:
        filter_criteria = {"_id": user_id}
        update = {"$set": {"announcements": False}}
        collection_name.update_one(filter_criteria, update)
        not_check = 'Off'
        print("Announcements is changed to False.")
      elif announcements is False:
        filter_criteria = {"_id": user_id}
        update = {"$set": {"announcements": True}}
        collection_name.update_one(filter_criteria, update)
        not_check = 'On'
        print("Announcements is changed to True")
    else:
      print(f"User with ID {user_id} not found in the database.")

    text_file_content = "Change your settings: "
    await query.edit_message_text(
        text_file_content,
        reply_markup=notification_keyboard(not_check),
        parse_mode='Markdown')
    return SETTINGS

  elif query.data == 'back':
    await query.edit_message_text(welcome,
                                  reply_markup=main_menu_keyboard(),
                                  parse_mode='Markdown')
    return MENU  # Return to the MENU state
  # Handle the pathway options
  elif query.data == 'pathfh':
    text_file_content = read_text_file(query.data)
    await query.edit_message_text(text_file_content,
                                  reply_markup=edit_updates_menu_keyboard(
                                      query.data),
                                  disable_web_page_preview=True,
                                  parse_mode='Markdown')
    return RESOURCES
  elif query.data == 'pathfp':
    text_file_content = read_text_file(query.data)
    await query.edit_message_text(text_file_content,
                                  reply_markup=edit_updates_menu_keyboard(
                                      query.data),
                                  disable_web_page_preview=True,
                                  parse_mode='Markdown')
    return RESOURCES
  else:
    text_file_content = read_text_file(query.data)
    await query.edit_message_text(text_file_content,
                                  reply_markup=edit_updates_menu_keyboard(
                                      query.data),
                                  disable_web_page_preview=True,
                                  parse_mode='Markdown')
  return RESOURCES


async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  user_id = user.id
  user_document = collection_name.find_one({"_id": user_id})

  # Check if the sender is an admin
  if user_document and user_document.get("admin", False):
    # User is an admin, check if announcements are enabled
    announcement_text = context.args[
        0] if context.args else "Default announcement message"  # Get the announcement message from the command
    # Filter users with announcements enabled
    users_with_announcements = collection_name.find({"announcements": True})

    for user in users_with_announcements:
      user_id = user["_id"]
      await context.bot.send_message(user_id, announcement_text)
  else:
    await update.message.reply_text(
        "*You don't have permission to perform this action.*")


async def total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
  announcements_enabled_count = collection_name.count_documents(
      {"announcements": True})
  announcements_disabled_count = collection_name.count_documents(
      {"announcements": False})
  total_user_count = collection_name.count_documents({})

  response = f"*Total number of Users: {total_user_count}*\n"
  response += f"*Subscribers: {announcements_enabled_count}*\n"
  response += f"*Unsubscriber: {announcements_disabled_count}*"

  await update.message.reply_text(response, parse_mode='Markdown')


def restart_bot():
  # Get the current script's command line arguments
  script_args = sys.argv

  # Find the Python interpreter that's running the script
  python_executable = sys.executable

  # Restart the script using the same Python interpreter
  subprocess.Popen([python_executable] + script_args)


async def update_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
  try:
    for repo_info in github.repositories:
      github.clone_or_update_repository(repo_info['url'], repo_info['name'])
    await update.message.reply_text("*Repositories are updated successfully.*",
                                    parse_mode='Markdown')
    restart_bot()
  except:
    await update.message.reply_text(
        "*Repositories are not updated successfully.*", parse_mode='Markdown')


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        MENU: [
            CallbackQueryHandler(
                main_menu,
                pattern=
                '^(resources|certifications|request_feature|join_community|settings|back)$'
            )
        ],
    },
    fallbacks=[CallbackQueryHandler(main_menu, pattern=f'^{BACK}$')])


keep_alive()



app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("announce", announce_command))
app.add_handler(CommandHandler("stat", total_users))
app.add_handler(CommandHandler("update", update_data))
app.add_handler(CallbackQueryHandler(main_menu))
app.add_handler(conversation_handler)
app.run_polling()