import configparser
from linebot import (
    LineBotApi, WebhookHandler
)

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self, file='config.ini'):
        self.config = configparser.ConfigParser()
        self.check_file(file)
        self.Channel_Secret = self.config['line_bot']['Channel_Secret']
        self.Channel_Access_Token = self.config['line_bot']['Channel_Access_Token']

        self.data_path = "data/"

        self.weather_api = self.config["central_weather_bureau"]["weather_api"]
        self.member_token = self.config["central_weather_bureau"]["member_token"]
        
        self.AQI_api = self.config["environmental_protection_administration"]["AQI_api"]
        
        self.vegetable_api  = self.config["agricultural_product_wholesale_market"]["vegetable_api"]
        self.fruit_api = self.config["agricultural_product_wholesale_market"]["fruit_api"]
        self.flower_api = self.config["agricultural_product_wholesale_market"]["flower_api"]
        
        self.db = {}
        self.db["host"] = self.config["redis"]["host"]
        self.db["port"] = self.config["redis"]["port"]
        self.db["password"] = self.config["redis"]["password"]

        self.google_key = self.config["google"]["google_key"]

        self.handler = None
        self.line_bot_api = None
        self.line_bot_init()

    def check_file(self, file):
        self.config.read(file)
        if not self.config.sections():
            raise configparser.Error('config.ini not exists')

    def line_bot_init(self):
        self.handler = WebhookHandler(self.Channel_Secret)
        self.line_bot_api = LineBotApi(self.Channel_Access_Token)