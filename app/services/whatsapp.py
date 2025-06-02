import os
import requests


META_TOKEN = os.getenv('META_TOKEN')

def sendCustomMessage(message, phoneNumber):
    return