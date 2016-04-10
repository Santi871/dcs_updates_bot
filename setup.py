from cx_Freeze import setup, Executable

includes = ['updates_bot', 'threading', 'time', 'urllib.request', 're', 'praw',  'OAuth2Util',
            'sqlite3', 'contextlib']

setup(name = "DCS Updates Bot" ,
      version = "0.2" ,
      description = "" ,
      options={"build_exe":{"includes":includes}},
      executables = [Executable("main.py")])
