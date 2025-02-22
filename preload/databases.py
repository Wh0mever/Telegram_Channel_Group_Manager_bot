import sqlite3

base = sqlite3.connect('databases/users.db')
cur = base.cursor()
base.execute('create table if not exists {}(id integer, channel integer, info text, life integer)'.format('data'))

base2 = sqlite3.connect('databases/admins.db')
cur2 = base2.cursor()
base2.execute('create table if not exists {}(id integer, info text)'.format('data'))

base3 = sqlite3.connect('databases/channels.db')
cur3 = base3.cursor()
base3.execute('create table if not exists {}(id integer, info text, message text, turn integer)'.format('data'))