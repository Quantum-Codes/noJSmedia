import json
import os

# supposed to be a drop-in replacement for replit db which stopped working

class db(dict):
    def __init__(self):
        if os.path.exists("db.json"):
            with open("db.json", "r") as file:
                super().__init__(json.load(file))
        else:
            super().__init__()
            with open("id.txt","w") as file:
                file.write("0")
            with open("db.json", "w") as file:
                self["data"] = []
                self["login"] = {}
                self["users"] = {}
                self["session"] = {}
                json.dump(self, file, indent = 2)


    def save(self):
        with open("db.json", "w") as file:
            json.dump(self, file, indent = 2)

    # the problem with these is that they only change the top level dictionary. so need to do .save() everywhere to change sublists/subdicts that were updated by using stuff like append, update, etc
    def __setitem__(self, key, value): # for db[key] = value
        super().__setitem__(key, value)
        self.save()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.save()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self.save()

    def clear(self):
        super().clear()
        self.save()

