#DCS Updates bot

DCS Updates bot is a Reddit bot made by **/u/santi871** that notifies subscribers of a new DCS World update via PM as
it is available for download.

To do so, it reads *updates.digitalcombatsimulator.com* once a minute and stores the different version numbers in a
local SQLite database. When a change is found, it goes through the subscriber list (which is stored in the database)
and sends a PM to each user entry.


For subscribing, the bot reads a predefined thread every 30 seconds and looks for comments that say "subscribe". Once
found, it adds the comment's author name to the subscriber list in the database.


For unsubscribing, the bot reads its own Reddit inbox every 20 seconds, looking for messages that say "unsubscribe".
When it finds one, it deletes the author's name from the subscriber list in the database, and adds them to a blacklist
so that they are not subscribed again when the bot reads the subscription thread.


These 3 tasks are done on 3 separate threads for stability.


For any questions, complaints or suggestions, send a messasge to /u/santi871 on Reddit.