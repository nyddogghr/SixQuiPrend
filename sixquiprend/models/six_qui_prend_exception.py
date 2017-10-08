class SixQuiPrendException(Exception):
    def __init__(self, message, code):
        super(Exception, self).__init__()
        self.message = message
        self.code = code
