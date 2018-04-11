# -*- coding: utf-8 -*-

import datetime
from telegram.ext import (ConversationHandler, CommandHandler,
                          MessageHandler, RegexHandler, CallbackQueryHandler, Filters)
from logger import *
import timezone
import database.location
import database.tasks
import keyboards
import datetime_parser
import tasks


SET_LOCATION, READY, SETTINGS, ADD_NOTE_TEXT, ADD_NOTE_TIME = range(5)

MAX_TASKS_NUM_PER_CHAT = 100


def check_location_decorator(func):
    def wrapper(bot, update, chat_data):
        chat_id = None
        if update.message is not None:
            chat_id = update.message.chat_id
        elif update.callback_query is not None:
            chat_id = update.callback_query.message.chat_id

        if chat_id is None:
            logger.error('CHAT_ID IS NONE IN CHECK_LOCATION_DECORATOR, update: %s' % update)

        if chat_data.get('CHECK_DB', None) is None:
            geopos = database.location.get(chat_id)
            if geopos is not None:
                chat_data['LOC'] = geopos
            chat_data['CHECK_DB'] = True

        if chat_data.get('LOC', None) is None:
            update.message.reply_text('''Для начала, мне нужно узнать ваш часовой пояс.
Пришлите мне название вашего города или прикрепите локацию''',
                                      reply_markup=keyboards.SET_LOCATION_KEYBOARD)
            return SET_LOCATION

        return func(bot, update, chat_data=chat_data)

    return wrapper


def delete_invalid_notes_decorator(func):
    def wrapper(bot, update, chat_data, job_queue=None):
        chat_id = None
        if update.message is not None:
            chat_id = update.message.chat_id
        elif update.callback_query is not None:
            chat_id = update.callback_query.message.chat_id

        if 'TASKS' not in chat_data:
            chat_data['TASKS'] = []
            if job_queue is None:
                return func(bot, update, chat_data=chat_data)
            else:
                return func(bot, update, chat_data=chat_data, job_queue=job_queue)

        utc_now = int(datetime.datetime.utcnow().timestamp())
        l = []
        for t in chat_data['TASKS']:
            if t.time - utc_now > 0 and t.job.enabled and not t.job.removed:
                l.append(t)
            else:
                t.job.schedule_removal()
                database.tasks.delete(t.id, chat_id)

        chat_data['TASKS'] = l

        if job_queue is None:
            return func(bot, update, chat_data=chat_data)
        else:
            return func(bot, update, chat_data=chat_data, job_queue=job_queue)

    return wrapper


def start(bot, update, chat_data):
    if chat_data.get('CHECK_DB', None) is None:
        geopos = database.location.get(update.message.chat_id)
        if geopos is not None:
            chat_data['LOC'] = geopos
        chat_data['CHECK_DB'] = True

    if chat_data.get('LOC', None) is None:
        update.message.reply_text('''Привет!
Чтобы начать отправлять напоминания, мне нужно знать ваш часовой пояс.
Пришлите мне название вашего города или прикрепите локацию''',
                                  reply_markup=keyboards.SET_LOCATION_KEYBOARD)
        return SET_LOCATION

    update.message.reply_text('Я готов к работе!)', reply_markup=keyboards.READY_KEYBOARD)
    return READY


def cancel(bot, update):
    update.message.reply_text('Ок)', reply_markup=keyboards.READY_KEYBOARD)
    return READY


def set_location_geopos(bot, update, chat_data):
    geopos = timezone.geopos_to_key(update.message.location.latitude,
                                    update.message.location.longitude)
    tz = timezone.get_timezone(geopos)

    if tz is None:
        update.message.reply_text('Не удалось определить ваш часовой пояс, извините(\nПопробуйте еще раз')
        logger.error('Bad TZ request in update "{}" for geopos "{} {}"'.format(update, *geopos))
        return SET_LOCATION

    if database.location.get(update.message.chat_id) is None:
        database.location.insert(update.message.chat_id, geopos)
    else:
        database.location.update(update.message.chat_id, geopos)

    chat_data['LOC'] = geopos
    update.message.reply_text('Готово!)\nВаш часовой пояс:\n{}'.format(tz), reply_markup=keyboards.READY_KEYBOARD)
    logger.info("'{}' set location to {}".format(update, geopos))
    return READY


def set_location_address(bot, update, chat_data):
    tz = None
    geopos = None
    if update.message.text is not None and len(update.message.text):
        geopos = timezone.get_geopos_for_address(update.message.text)
        if geopos is not None:
            tz = timezone.get_timezone(geopos)

    if tz is None:
        update.message.reply_text('Не удалось определить ваш часовой пояс, извините(\nПопробуйте еще раз',
                                  reply_markup=keyboards.SET_LOCATION_KEYBOARD)
        logger.error('Bad TZ request in update "{}" for address "{}"'.format(update, update.message.text))
        return SET_LOCATION
    else:
        if database.location.get(update.message.chat_id) is None:
            database.location.insert(update.message.chat_id, geopos)
        else:
            database.location.update(update.message.chat_id, geopos)

        chat_data['LOC'] = geopos
        update.message.reply_text('Готово!)\nВаш часовой пояс:\n{}'.format(tz), reply_markup=keyboards.READY_KEYBOARD)
        logger.info("'{}' set location to '{}'{}".format(update, update.message.text, geopos))
        return READY


@check_location_decorator
def get_time(bot, update, chat_data):
    tz = timezone.get_timezone(chat_data['LOC'])
    update.message.reply_text(tz.get_current_time(), reply_markup=keyboards.READY_KEYBOARD)
    return READY


@check_location_decorator
def settings(bot, update, chat_data):
    tz = timezone.get_timezone(chat_data['LOC'])
    update.message.reply_text('Ваш часовой пояс:\n{}'.format(tz), reply_markup=keyboards.SETTINGS_KEYBOARD)
    return SETTINGS


def settings_change_tz(bot, update, chat_data):
    update.message.reply_text('Пришлите мне название вашего города или прикрепите локацию',
                              reply_markup=keyboards.SET_LOCATION_KEYBOARD)
    return SET_LOCATION


@check_location_decorator
def add_note(bot, update, chat_data):
    update.message.reply_text('Напишите, о чем вам напомнить)', reply_markup=keyboards.ADD_NOTE_TEXT_KEYBOARD)
    return ADD_NOTE_TEXT


def add_note_text(bot, update, chat_data):
    chat_data['text'] = update.message.text.strip()
    update.message.reply_text('Когда прислать уведомление?',
                              reply_markup=keyboards.ADD_NOTE_TIME_KEYBOARD)
    return ADD_NOTE_TIME


def add_note_time_help(bot, update, chat_data):
    update.message.reply_text('Бла-бла-блаааа',
                              reply_markup=keyboards.ADD_NOTE_TIME_KEYBOARD)
    return ADD_NOTE_TIME


@delete_invalid_notes_decorator
def add_note_time(bot, update, chat_data, job_queue):
    utc_now = int(datetime.datetime.utcnow().timestamp())
    t = datetime_parser.get_timestamp(update.message.text, utc_now)
    if t is None:
        update.message.reply_text('Не понимаю( Посмотрите возможные форматы задания даты и времени',
                                  reply_markup=keyboards.ADD_NOTE_TIME_KEYBOARD)
        logger.info('WRONG TIME FORMAT: {} "{}"'.format(update.effective_user, update.message.text))
        return ADD_NOTE_TIME

    if len(chat_data.get('TASKS', [])) > MAX_TASKS_NUM_PER_CHAT:
        update.message.reply_text('У вас слишком много напоминаний, зачем столько???🙀',
                                  reply_markup=keyboards.READY_KEYBOARD)
        return READY

    job = job_queue.run_once(alarm, t - utc_now, context=(utc_now, update.message.chat_id, chat_data['text']))
    task = tasks.Task(utc_now, chat_data['text'], t, job)

    if 'TASKS' not in chat_data:
        chat_data['TASKS'] = []
    chat_data['TASKS'].append(task)

    database.tasks.insert(update.message.chat_id, task)

    update.message.reply_text(
        '"{}" добавлено на {}'.format(task.text,
                                      timezone.get_timezone(chat_data['LOC']).get_time(task.time)),
        reply_markup=keyboards.READY_KEYBOARD)

    logger.info('ADD NEW NOTE: {} "{}" at "{}"'.format(update.effective_user, task.text, update.message.text))

    return READY


def alarm(bot, job):
    id, chat_id, text = job.context
    bot.send_message(chat_id, text='⏰%s' % text)
    database.tasks.delete(id, chat_id)


@delete_invalid_notes_decorator
@check_location_decorator
def list_notes(bot, update, chat_data):
    if len(chat_data.get('TASKS', [])) == 0:
        update.message.reply_text('Вы не добавили ни одного напоминания', reply_markup=keyboards.READY_KEYBOARD)
        return READY
    k = keyboards.get_task_inline_keyboard(timezone.get_timezone(chat_data['LOC']), chat_data['TASKS'])
    update.message.reply_text('Нажмите, чтобы удалить', reply_markup=k)
    return READY


def show_all_tasks(bot, update, chat_data):
    query = update.callback_query
    if len(chat_data['TASKS']) == 0:
        bot.edit_message_text(text='Вы не добавили ни одного напоминания',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        return READY
    k = keyboards.get_task_inline_keyboard(timezone.get_timezone(chat_data['LOC']), chat_data['TASKS'])
    bot.edit_message_text(text='Нажмите, чтобы удалить',
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          reply_markup=k)
    return READY


def show_selected_task(bot, update, chat_data):
    query = update.callback_query
    q_data = int(update.callback_query.data[1:])

    tz = timezone.get_timezone(chat_data['LOC'])

    for t in chat_data.get('TASKS', []):
        if t.id == q_data:
            bot.edit_message_text(text='\n'.join((t.text, tz.get_time(t.time))),
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=keyboards.get_selected_task_inline_keyboard(tz, t))
            return READY

    return show_all_tasks(bot, update, chat_data)


def delete_selected_task(bot, update, chat_data):
    query = update.callback_query
    q_data = int(update.callback_query.data[1:])

    l = []
    for t in chat_data.get('TASKS', []):
        if t.id == q_data:
            t.job.schedule_removal()
            database.tasks.delete(t.id, query.message.chat_id)
            bot.answer_callback_query(query.id, text='Удалено: %s' % t.text, show_alert=False)
        else:
            l.append(t)

    chat_data['TASKS'] = l

    if len(chat_data['TASKS']) == 0:
        bot.edit_message_text(text='У вас больше нет заметок😉',
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        return READY

    k = keyboards.get_task_inline_keyboard(timezone.get_timezone(chat_data['LOC']), chat_data['TASKS'])

    bot.edit_message_text(text='Нажмите, чтобы удалить',
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          reply_markup=k)


@delete_invalid_notes_decorator
@check_location_decorator
def inline_btn_callback(bot, update, chat_data):
    query = update.callback_query
    q_data = update.callback_query.data

    f = None
    if q_data[0] == keyboards.SHOW_ALL_TASKS:
        f = show_all_tasks
    elif q_data[0] == keyboards.SHOW_SELECTED:
        f = show_selected_task
    elif q_data[0] == keyboards.DELETE_SELECTED:
        f = delete_selected_task

    if f is not None:
        return f(bot, update, chat_data)


callback_query_handler = CallbackQueryHandler(inline_btn_callback, pass_chat_data=True)


main_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start, pass_chat_data=True),
                  CommandHandler('time', get_time, pass_chat_data=True),
                  RegexHandler('^Настройки$', settings, pass_chat_data=True),
                  RegexHandler('^Добавить заметку$', add_note, pass_chat_data=True),
                  RegexHandler('^Добавленные заметки$', list_notes, pass_chat_data=True)],

    states={
        SET_LOCATION: [RegexHandler('^Отмена$', cancel, pass_chat_data=False),
                       MessageHandler(Filters.location, set_location_geopos, pass_chat_data=True),
                       MessageHandler(Filters.text, set_location_address, pass_chat_data=True)],

        READY: [CommandHandler('start', start, pass_chat_data=True),
                CommandHandler('time', get_time, pass_chat_data=True),
                RegexHandler('^Настройки$', settings, pass_chat_data=True),
                RegexHandler('^Добавить заметку$', add_note, pass_chat_data=True),
                RegexHandler('^Добавленные заметки$', list_notes, pass_chat_data=True)],

        SETTINGS: [RegexHandler('^Поменять часовой пояс$', settings_change_tz, pass_chat_data=True),
                   RegexHandler('^Отмена$', cancel, pass_chat_data=False)],

        ADD_NOTE_TEXT: [RegexHandler('^Отмена$', cancel, pass_chat_data=False),
                        RegexHandler('^.*$', add_note_text, pass_chat_data=True)],

        ADD_NOTE_TIME: [RegexHandler('^Отмена$', cancel, pass_chat_data=False),
                        RegexHandler('^Форматы времени$', add_note_time_help, pass_chat_data=True),
                        RegexHandler('^.*$', add_note_time, pass_chat_data=True, pass_job_queue=True)],
    },

    fallbacks=[RegexHandler('^.*$', start, pass_chat_data=True)]
)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)
