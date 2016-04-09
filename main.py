import updates_bot
import threading
import time


class MyThread(threading.Thread):
    def __init__(self, threadid, name, bot, method):
        threading.Thread.__init__(self)
        self.threadid = threadid
        self.name = name
        self.bot = bot
        self.method = method

    def run(self):
        print("Starting " + self.name)
        methodToRun = self.method()
        print("Exiting " + self.name)


def main():

    bot = updates_bot.UpdatesBot()

    time.sleep(5)

    website_checker = MyThread(1, "Website checker", bot, bot.check_website)
    website_checker.start()

    time.sleep(2)

    message_checker = MyThread(2, "Message checker", bot, bot.watch_messages)
    message_checker.start()

    time.sleep(2)

    thread_watcher = MyThread(3, "Thread watcher", bot, bot.watch_thread)
    thread_watcher.start()

if __name__ == '__main__':
    main()
