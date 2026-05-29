import datetime
import os
import uuid
import json
import struct


class Helper:
    def __init__(self):
        print("Helper initialized")

    def get_uuid(self):
        return str(uuid.uuid4())
