import bcrypt

class Usuario:
    def __init__(self,email,password):
        self._email = email
        self._password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())