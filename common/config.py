# -*- coding: utf-8 -*-
import json
import os

CONFIG_FILE = "config.json"

CONFIG_PATH_VAR = "path"
CONFIG_CARD_VAR = "card"
CONFIG_POINT_VAR = "points"
CONFIG_INDEX_VAR = "${index}"
CONFIG_INTERVAL_VAR = "interval"
CONFIG_LOGGING_VAR = "logging"

# requires tweaking to store fan profile based on card index
DEFAULTCONFIG = {
    CONFIG_CARD_VAR : "0",
    CONFIG_POINT_VAR : (
        (0, 0),
        (39, 0),
        (40, 40),
        (65, 100)
    ),
    CONFIG_INTERVAL_VAR : "2500",
    CONFIG_LOGGING_VAR : False
}

class Config():
    def __init__(self):
        self.load()

    def getValue(self, key):
        return self.myConfig[key]

    def setValue(self, key, value):
        self.myConfig[key] = value

    def load(self):
        conf = DEFAULTCONFIG
        
        try:
            with open(CONFIG_FILE, "r") as read_file:
                conf = json.load(read_file)
        except:
            print("Could not open file, using default config")
        
        conf = dict(DEFAULTCONFIG, **conf)

        if conf.__contains__(CONFIG_PATH_VAR) and conf.__contains__(CONFIG_CARD_VAR):
            path = conf[CONFIG_PATH_VAR].replace(CONFIG_INDEX_VAR, conf[CONFIG_CARD_VAR])
            
            if not os.path.isdir(path):
                path = DEFAULTCONFIG[CONFIG_PATH_VAR].replace(CONFIG_INDEX_VAR, DEFAULTCONFIG[CONFIG_CARD_VAR])

            conf[CONFIG_PATH_VAR] = path

        if len(conf[CONFIG_POINT_VAR]) < 2:
            conf[CONFIG_POINT_VAR] = DEFAULTCONFIG[CONFIG_POINT_VAR]
        
        with open(CONFIG_FILE, "w") as write_file:
            json.dump(conf, write_file)
        
        conf[CONFIG_POINT_VAR] = sorted(conf[CONFIG_POINT_VAR], key=lambda tup: tup[1])

        print("Loaded %s: %s" % (CONFIG_FILE, conf))
        self.myConfig = conf

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as write_file:
                json.dump(self.myConfig, write_file, sort_keys=True, indent=4)
            print("Saved %s: %s" % (CONFIG_FILE, self.myConfig))
        except:
            print("Failed to save config!")