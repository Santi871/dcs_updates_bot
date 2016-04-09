import urllib.request as urllib
import re
import praw
import OAuth2Util
import sqlite3
import contextlib
from time import sleep

class UpdatesBot:

    def __init__(self):

        self.r = praw.Reddit(user_agent='windows:DCS Update Checker v1 (by /u/santi871)')
        self.o = OAuth2Util.OAuth2Util(self.r)
        self.o.refresh(force=True)
        self.db = sqlite3.connect('dcs_updates_bot.db')
        self.cur = self.db.cursor()

        print("Creating tables...")

        self.db.execute('''CREATE TABLE IF NOT EXISTS CURVERSION
                           (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                           BRANCH TEXT NOT NULL UNIQUE,
                           VERSION TEXT NOT NULL)''')

        self.db.execute('''CREATE TABLE IF NOT EXISTS SUBSCRIBERS
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USER TEXT NOT NULL UNIQUE)''')

        self.db.commit()

        print("Fetching url...")

        self.url = "http://updates.digitalcombatsimulator.com/"

        with contextlib.closing(urllib.urlopen(self.url)) as data:

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

        print("Done starting up.")

    def check_website(self):

        self.db1 = sqlite3.connect('dcs_updates_bot.db')
        self.cur1 = self.db1.cursor()

        while True:

            print("Checking website...")

            changes = []

            with contextlib.closing(urllib.urlopen(self.url)) as data:

                result = re.findall(r'\d\.\d\.\d\.\d{5}\.\d{2}', str(data.read()), flags=0)

            self.new_stable = result[0]
            self.new_open_beta = result[1]
            self.new_open_alpha = result[2]

            self.cur1.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 1''')
            self.cur_stable = self.cur1.fetchone()[3]

            self.cur1.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 2''')
            self.cur_open_beta = self.cur1.fetchone()[3]

            self.cur1.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 3''')
            self.cur_open_alpha = self.cur1.fetchone()[3]

            if self.new_stable != self.cur_stable:
                changes.append("Stable")
                self.cur1.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 1;''', (result[0],))

            if self.new_open_beta != self.cur_open_beta:
                changes.append("Open Beta")
                self.cur1.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 2;''', (result[1],))

            if self.new_open_alpha != self.cur_open_alpha:
                changes.append("Open Alpha")
                self.cur1.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 3;''', (result[2],))

            self.db1.commit()

            if len(changes) > 0:
                self.send_messages(changes)

            sleep(60)

    def send_messages(self, changes):

        print("Sending messages...")

        changes_string = ''

        for item in changes:
            changes_string = changes_string + '* ' + item + '\n\n'

        message = '#DCS World has been updated!\n\n---\n\n**Updated branches:**\n\n' + changes_string +\
                  '\n\n[DCS World Updates](http://updates.digitalcombatsimulator.com/) | [Hoggit](https://www.reddit.com/r/hoggit)\n\n---\n\n*I am a bot! [Click and send to unsubscribe](https://www.reddit.com/message/compose?to=DCS_updates_bot&subject=Dear%20DCS%20Updates%20bot&message=unsubscribe) | [Source](https://github.com/Santi871/dcs_updates_bot)*'

        self.cur.execute('''SELECT USER FROM SUBSCRIBERS''')
        users = self.cur1.fetchall()

        for user in users:
            self.r.send_message(user[0], "An update for DCS World is out!", message)
            print("Sent message to: " + user[0] + ". Reason: DCS World update")
            sleep(2)

    def watch_thread(self):

        self.db2 = sqlite3.connect('dcs_updates_bot.db')
        self.cur2 = self.db2.cursor()

        thread_id = '4dy94g'
        submission = self.r.get_submission(submission_id=thread_id)
        already_done = []

        while True:

            print("Checking thread...")

            submission.replace_more_comments(limit=None, threshold=0)
            all_comments = praw.helpers.flatten_tree(submission.comments)

            for comment in all_comments:
                if comment.body == "subscribe" and comment.permalink not in already_done:

                    try:
                        self.cur2.execute('''INSERT INTO SUBSCRIBERS(USER) VALUES(?)''', (str(comment.author),))
                        self.db2.commit()
                        self.r.send_message(str(comment.author), "You have subscribed to DCS updates bot!", 'You have been successfully subscribed to DCS updates bot. You will now receive messages when a branch of DCS World is updated.\n\n---\n\n*I am a bot! [Click and send to unsubscribe](https://www.reddit.com/message/compose?to=DCS_updates_bot&subject=Dear%20DCS%20Updates%20bot&message=unsubscribe) | [Source](https://github.com/Santi871/dcs_updates_bot)*')
                        print("Sent message to: " + str(comment.author) + ". Reason: subscribed")
                        sleep(1)
                    except Exception:
                        pass

                    already_done.append(comment.permalink)

            sleep(20)

    def watch_messages(self):

        self.db3 = sqlite3.connect('dcs_updates_bot.db')
        self.cur3 = self.db3.cursor()
        already_done = []

        while True:

            print("Checking messages...")
            messages = self.r.get_messages()

            for message in messages:

                if message.body == "unsubscribe" and message.id not in already_done:

                    try:
                        self.cur3.execute('''DELETE FROM SUBSCRIBERS WHERE USER = ?;''', (str(message.author),))
                        self.db3.commit()
                        message.reply("You have been unsubscribed!")
                        print("Sent message to: " + str(message.author) + ". Reason: unsubscribed")
                    except Exception:
                        pass

                    already_done.append(message.id)

            sleep(30)

    def closedb(self):

        self.db.close()
        self.db1.close()
        self.db2.close()
        self.db3.close()








