import urllib.request as urllib
import re
import praw
import OAuth2Util
import sqlite3


class UpdatesBot:

    def __init__(self):

        self.r = praw.Reddit(user_agent='windows:DCS Update Checker v1 (by /u/santi871)')
        self.o = OAuth2Util.OAuth2Util(self.r)
        self.o.refresh(force=True)
        self.db = sqlite3.connect('dcs_updates_bot.db')
        self.cur = self.db.cursor()

        self.db.execute('''CREATE TABLE IF NOT EXISTS CURVERSION
                           (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                           BRANCH TEXT NOT NULL UNIQUE,
                           VERSION TEXT NOT NULL)''')

        self.db.commit()

        self.url = "http://updates.digitalcombatsimulator.com/"

        data = urllib.urlopen(self.url)

        result = re.findall(r'\d\.\d\.\d\.\d{5}\.\d{2}', str(data.read()), flags=0)

        self.cur_stable = result[0]
        self.cur_open_beta = result[1]
        self.cur_open_alpha = result[2]

        try:
            self.cur.execute('''INSERT INTO CURVERSION(BRANCH, VERSION) VALUES(?,?)''', ("STABLE", result[0]))
            self.cur.execute('''INSERT INTO CURVERSION(BRANCH, VERSION) VALUES(?,?)''', ("OPEN BETA", result[1]))
            self.cur.execute('''INSERT INTO CURVERSION(BRANCH, VERSION) VALUES(?,?)''', ("OPEN ALPHA", result[2]))
        except Exception:
            pass

        self.db.commit()

        self.new_stable = self.cur_stable
        self.new_open_beta = self.cur_open_beta
        self.new_open_alpha = self.cur_open_alpha

    def check_website(self):

        changes = []
        data = urllib.urlopen(self.url)

        result = re.findall(r'\d\.\d\.\d\.\d{5}\.\d{2}', str(data.read()), flags=0)

        self.new_stable = "asd"
        self.new_open_beta = result[1]
        self.new_open_alpha = result[2]

        self.cur.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 1''')
        self.cur_stable = self.cur.fetchone()[3]

        self.cur.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 2''')
        self.cur_open_beta = self.cur.fetchone()[3]

        self.cur.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 3''')
        self.cur_open_alpha = self.cur.fetchone()[3]

        if self.new_stable != self.cur_stable:
            changes.append("Stable")
            self.cur.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 1;''', (result[0],))

        if self.new_open_beta != self.cur_open_beta:
            changes.append("Open Beta")
            self.cur.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 2;''', (result[1],))

        if self.new_open_alpha != self.cur_open_alpha:
            changes.append("Open Alpha")
            self.cur.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 3;''', (result[2],))

        self.db.commit()
        self.db.close()

        if len(changes) > 0:
            self.send_messages(changes)

    def send_messages(self, changes):

        message = str(changes)

        self.r.send_message("santi871", "hello", message)

bot = UpdatesBot()
bot.check_website()







