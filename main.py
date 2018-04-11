#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from telegram.ext import Updater, CommandHandler, RegexHandler
from logger import logger
import handlers
import conf
import tasks
import database.tasks


def main():
    updater = Updater(conf.TELEGRAM_API_KEY)

    dp = updater.dispatcher

    dp.add_handler(handlers.main_conv_handler)
    dp.add_handler(handlers.callback_query_handler)
    dp.add_error_handler(handlers.error)

    for t in database.tasks.get_all():
        id, chat_id, text, time = t

        utc_now = int(datetime.datetime.utcnow().timestamp())
        if time - utc_now < 0:
            database.tasks.delete(id, chat_id)
            continue
        job = dp.job_queue.run_once(handlers.alarm, time - utc_now, context=(id, chat_id, text))
        task = tasks.Task(id, text, time, job)

        chat_data = dp.chat_data[chat_id]
        if 'TASKS' not in chat_data:
            chat_data['TASKS'] = []
        chat_data['TASKS'].append(task)

    updater.start_polling()
    updater.idle()

    print('End')


if __name__ == '__main__':
    main()