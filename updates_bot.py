import urllib.request as urllib
import re
import praw
import OAuth2Util
import sqlite3
import contextlib
from time import sleep

class UpdatesBot:

    def __init__(self):

        print("Connecting to reddit...")

        self.r = praw.Reddit(user_agent='windows:DCS Update Checker v1 (by /u/santi871)')
        self.o = OAuth2Util.OAuth2Util(self.r)
        self.o.refresh(force=True)
        self.db = sqlite3.connect('dcs_updates_bot_database.db', check_same_thread=False)
        self.cur = self.db.cursor()
        self.changes_pending = False
        self.blacklist = []
        self.init = True

        print("Creating tables...")

        self.db.execute('''CREATE TABLE IF NOT EXISTS CURVERSION
                           (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                           BRANCH TEXT NOT NULL UNIQUE,
                           VERSION TEXT NOT NULL)''')

        self.db.execute('''CREATE TABLE IF NOT EXISTS SUBSCRIBERS
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USER TEXT NOT NULL UNIQUE)''')

        self.db.execute('''CREATE TABLE IF NOT EXISTS BLACKLIST
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USER TEXT NOT NULL UNIQUE)''')

        self.db.execute('''CREATE TABLE IF NOT EXISTS MESSAGES
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            MSG_ID TEXT NOT NULL UNIQUE)''')

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

        self.cur.execute('''SELECT USER FROM BLACKLIST''')
        blacklist_tuples = self.cur.fetchall()

        for user in blacklist_tuples:
            self.blacklist.append(user[0])

        self.new_stable = self.cur_stable
        self.new_open_beta = self.cur_open_beta
        self.new_open_alpha = self.cur_open_alpha

        print("Done initialiazing.")

    def check_website(self):

        while True:

            #print("Checking website...")

            if not self.changes_pending or self.init:
                changes = []
                self.init = False

                with contextlib.closing(urllib.urlopen(self.url)) as data:

                    result = re.findall(r'\d\.\d\.\d\.\d{5}\.\d{2}', str(data.read()), flags=0)

                self.new_stable = result[0]
                self.new_open_beta = result[1]
                self.new_open_alpha = result[2]

                self.cur.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 1''')
                self.cur_stable = self.cur.fetchone()[3]

                self.cur.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 2''')
                self.cur_open_beta = self.cur.fetchone()[3]

                self.cur.execute('''SELECT rowid, * FROM CURVERSION WHERE id = 3''')
                self.cur_open_alpha = self.cur.fetchone()[3]

                if self.new_stable != self.cur_stable:
                    changes.append("Stable: " + result[0])
                    self.cur.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 1;''', (result[0],))
                    print("New stable!")

                if self.new_open_beta != self.cur_open_beta:
                    changes.append("Open Beta: " + result[1])
                    self.cur.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 2;''', (result[1],))
                    print("New open beta!")

                if self.new_open_alpha != self.cur_open_alpha:
                    changes.append("Open Alpha " + result[2])
                    self.cur.execute('''UPDATE CURVERSION SET VERSION = ? WHERE ID = 3;''', (result[2],))
                    print("New open alpha!")

                self.db.commit()

            if len(changes) > 0 or self.changes_pending:
                try:
                    self.changes_pending = True
                    self.send_messages(changes)
                except Exception:
                    pass

            sleep(60)

    def send_messages(self, changes):

        #print("Sending messages...")

        changes_string = ''

        for item in changes:
            changes_string = changes_string + '* ' + item + '\n\n'

        message = '#DCS World has been updated!\n\n---\n\n**Updated branches:**\n\n' + changes_string +\
                  '\n\n[DCS World Updates](http://updates.digitalcombatsimulator.com/) | [Hoggit](https://www.reddit.com/r/hoggit)\n\n---\n\n*I am a bot! [Click and send to unsubscribe](https://www.reddit.com/message/compose?to=DCS_updates_bot&subject=Dear%20DCS%20Updates%20bot&message=unsubscribe) | [Source](https://github.com/Santi871/dcs_updates_bot) | [Message my owner](https://www.reddit.com/message/compose?to=Santi871)*'

        self.cur.execute('''SELECT USER FROM SUBSCRIBERS''')
        users = self.cur.fetchall()

        for user in users:
            self.r.send_message(user[0], "An update for DCS World is out!", message)
            print("Sent message to: " + user[0] + ". Reason: DCS World update")

        self.changes_pending = False

    def watch_thread(self):

        thread_id = '4e80x7'
        already_done = []

        while True:

            #print("Checking thread...")

            try:
                submission = self.r.get_submission(submission_id=thread_id)
                all_comments = submission.comments
                for comment in all_comments:

                    if comment.body.find("subscribe") != 1 and comment.permalink not in already_done\
                            and str(comment.author) not in self.blacklist:

                        try:
                            self.cur.execute('''INSERT INTO SUBSCRIBERS(USER) VALUES(?)''', (str(comment.author),))
                            self.db.commit()
                            self.r.send_message(str(comment.author), "You have subscribed to DCS updates bot!", 'You have been successfully subscribed to DCS updates bot. You will now receive messages when a branch of DCS World is updated.\n\n---\n\n*I am a bot! [Click and send to unsubscribe](https://www.reddit.com/message/compose?to=DCS_updates_bot&subject=Dear%20DCS%20Updates%20bot&message=unsubscribe) | [Source](https://github.com/Santi871/dcs_updates_bot) | [Message my owner](https://www.reddit.com/message/compose?to=Santi871)*')
                            print("Sent message to: " + str(comment.author) + ". Reason: subscribed")
                            sleep(1)
                        except Exception:
                            pass

                        already_done.append(comment.permalink)

            except Exception:
                pass

            sleep(20)

    def watch_messages(self):

        already_done = []

        self.cur.execute('''SELECT MSG_ID FROM MESSAGES''')
        already_done_tuples = self.cur.fetchall()

        for item in already_done_tuples:
            already_done.append(item[0])

        while True:

            #print("Checking messages...")

            try:
                messages = self.r.get_messages()

                for message in messages:

                    if message.body == "unsubscribe" and message.id not in already_done:

                        try:
                            self.cur.execute('''INSERT INTO MESSAGES(MSG_ID) VALUES(?)''', (str(message.id),))
                            self.cur.execute('''DELETE FROM SUBSCRIBERS WHERE USER = ?;''', (str(message.author),))
                            self.cur.execute('''INSERT INTO BLACKLIST(USER) VALUES(?)''', (str(message.author),))
                            self.db.commit()
                            self.blacklist.append(str(message.author))
                            message.reply('You have been successfully unsubscribed to DCS updates bot. You will no longer receive messages when a branch of DCS World is updated.\n\n---\n\n*I am a bot! [Source](https://github.com/Santi871/dcs_updates_bot) | [Message my owner](https://www.reddit.com/message/compose?to=Santi871)*')
                            print("Sent message to: " + str(message.author) + ". Reason: unsubscribed")
                        except Exception:
                            pass

            except Exception as e:
                print(e)

            sleep(30)








