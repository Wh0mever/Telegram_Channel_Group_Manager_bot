from aiogram.fsm.state import State, StatesGroup


class aForm(StatesGroup):
    channel_message = State()

    edit_message = State()
    edit_kbs = State()

    spam_post = State()
    spam_kbs = State()
    spam_channels = State()

    admin_message = State()