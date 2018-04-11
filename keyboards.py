# -*- coding: utf-8 -*-

from telegram import ReplyKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


SHOW_ALL_TASKS, SHOW_SELECTED, DELETE_SELECTED = (chr(i) for i in range(3))


READY_KEYBOARD = ReplyKeyboardMarkup(
    [['Добавить заметку'],
     ['Добавленные заметки'],
     ['Настройки'],
     ['/time']],
    resize_keyboard=True
)


SET_LOCATION_KEYBOARD = ReplyKeyboardMarkup(
    [['Отмена']],
    resize_keyboard=True
)


SETTINGS_KEYBOARD = ReplyKeyboardMarkup(
    [['Поменять часовой пояс'],
     ['Отмена']],
    resize_keyboard=True
)


ADD_NOTE_TEXT_KEYBOARD = ReplyKeyboardMarkup(
    [['Отмена']],
    resize_keyboard=True
)

ADD_NOTE_TIME_KEYBOARD = ReplyKeyboardMarkup(
    [['Через 10 мин', 'Через 30 мин'],
     ['Через час', 'Через 3 часа'],
     ['Отмена'],
     ['Форматы времени']],
    resize_keyboard=True
)


def get_task_inline_keyboard(tz, tasks):
    keyboard = []
    for t in sorted(tasks, key=lambda x: x.time):
        if t.job.enabled and not t.job.removed:
            keyboard.append([InlineKeyboardButton('\n'.join((t.text, tz.get_time_short(t.time))),
                                                  callback_data=SHOW_SELECTED+str(t.id))])
    return InlineKeyboardMarkup(keyboard)


def get_selected_task_inline_keyboard(tz, task):
    return InlineKeyboardMarkup([[InlineKeyboardButton('Удалить', callback_data=DELETE_SELECTED+str(task.id)),
                                 InlineKeyboardButton('Назад', callback_data=SHOW_ALL_TASKS)]])
