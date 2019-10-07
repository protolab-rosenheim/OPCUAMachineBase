from abc import ABCMeta, abstractmethod


class Machine(metaclass=ABCMeta):
    """Abstract class for all machines"""
    def __init__(self, opcua_variables, opcua_methods):
        self.opcua_variables = opcua_variables
        self.opcua_methods = opcua_methods

    @abstractmethod
    def subscribe(self, class_to_notify):
        pass

    @abstractmethod
    def _notify(self, var_name, content):
        pass
