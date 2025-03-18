# --------------------------------------------------------------------------
# Custom Exceptions module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
class BackendExceptions(Exception):
    """
    Exceptions occurs from server-side operations
    """

    def __init__(self, message):
        if isinstance(message, Exception):
            # minimize stack trace
            message_str = (
                str(message).split("\n")[0] if "\n" in str(message) else str(message)
            )
            self.message = f"{type(message).__name__}: {message_str}"
        else:
            self.message = str(message)

        super().__init__(self.message)


class AIException(Exception):
    """
    Exceptions occurs from AI operations
    """

    pass
