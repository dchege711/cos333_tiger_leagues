"""
exception.py

Allows for error pages/responses with custom exception messages.

"""

import traceback

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

def validate_values(data_obj, constraints, jsonify=True):
    """
    Helper function for validating JSON input

    :param data_obj: dict

    A key-value pairing that needs to be validated

    :param constraints: list[tuple]

    Each tuple has 5 items. In order, they are: key (str), 
    cast_function (function), l_limit (value), u_limit (value), error_msg (str)

    :kwarg jsonify: bool

    If ``True``, the raised ``TigerLeaguesException`` will have its jsonify 
    attribute set.

    :raises: ``TigerLeaguesException``

    If any of the keys don't exist or any of the values fail to meet the 
    constraint.

    """
    for key, cast_function, l_limit, u_limit, error_msg in constraints:
        try:
            data_obj[key] = cast_function(data_obj[key])
            if l_limit is not None: assert data_obj[key] >= l_limit
            if u_limit is not None: assert data_obj[key] <= u_limit
        except:
            traceback.print_exc()
            raise TigerLeaguesException(error_msg, jsonify=jsonify)
