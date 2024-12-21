from src.error_handlers.base import ExceptionsBase
from src.configs import Constants

class UserExceptionBase(ExceptionsBase):
    def __init__(self, username:str, password:str=None):
        self.username = username
        if password:
            self.password = password
        super().__init__()

    def get_status_code(self):
        return Constants.User.ERROR_CODE
    
class UserNotFoundError(UserExceptionBase):
    def get_messages(self):
        return f"{self.username} not found."

class UserAlreadyExistError(UserExceptionBase):
    def get_messages(self):
        return f"{self.username} Alerady exists, please login directly."

class InvalidError(UserExceptionBase):
    def get_messages(self):
        return "Invalid format of username or password, please try again."
