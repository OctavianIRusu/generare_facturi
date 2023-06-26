class AuthenticationError(Exception):
    """
    Exception raised for authentication errors.

    Attributes:
        message (str): The error message describing the authentication error.

    Methods:
        __init__(self, message): Initialize the AuthenticationError instance.
        __str__(self): Return a string representation of the exception.
    """

    def __init__(self, message):
        """
        Initialize the AuthenticationError instance.

        Args:
            message (str): The error message describing the authentication error.
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """
        Return a string representation of the exception.

        Returns:
            str: The error message of the exception.
        """
        return f"{self.__class__.__name__}: {self.message}"