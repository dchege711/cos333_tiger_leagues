"""
exception.py

Allows for error pages/responses with custom exception messages.

"""

class TigerLeaguesException(Exception):
    """
    A special exception for errors that arise due to constraints that we set on 
    the application, for instance, a user may not access the league panel for a 
    league in which they lack an admin status, etc.

    :param message: str

    human readable string explaining the problem

    :kwarg status_code: int

    To specify the error code in the response. Like 400, 404, 500, etc. 

    """

    def __init__(self, message, status_code=400, jsonify=True):
        Exception.__init__(self)
        self.message = message
        self.jsonify = jsonify
        self.status_code = status_code

    def to_dict(self):
        """
        :return: ``dict``

        A dict representation of the exception
        
        """
        return {
            "success": False, "message": self.message, 
            "status": self.status_code
        }
