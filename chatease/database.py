from abc import ABCMeta, abstractmethod


class User(object, metaclass=ABCMeta):
    @abstractmethod
    def get(self, username):
        pass

    @abstractmethod
    def auth_user(self, password):
        pass

    @abstractmethod
    def get_friends(self):
        pass

    @abstractmethod
    def get_groups(self):
        pass