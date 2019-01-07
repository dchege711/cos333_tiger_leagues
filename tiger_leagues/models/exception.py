"""
exception.py

Allows for error pages with custom exception messages.

"""

class TigerLeaguesException(Exception):
    """
    A catchall exception for all problems.
    Status code and message can be customized wherever it's raised.

    """

    status_code = 400

    def __init__(self, message, status_code=None):
        """
        :param message: str

        human readable string explaining the problem

        :kwarg status_code: int

        To specify the error code in the response. Like 400, 404, 500, etc. 

        """
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        """
        :return: ``dict``

        A dict representation of the exception
        
        """
        rv = {}
        rv['message'] = self.message
        return rv