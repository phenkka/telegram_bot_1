from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

greeting = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Let's start!", callback_data='start')]
])

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Influencer info", callback_data='check_sol'),
     InlineKeyboardButton(text="Token holders", callback_data='holders')],
    [InlineKeyboardButton(text="Token Buyout by Influencers", callback_data='spy')]
])

return_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Menu", callback_data='start')]
])

tips = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Whom I know", callback_data='tip')]
])