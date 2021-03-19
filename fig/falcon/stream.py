from .api import Api

class Stream():
    def __init__(self):
        self.falcon_api = Api()

    def run(self):
        print("Stream.run")
        self.falcon_api.streams()
