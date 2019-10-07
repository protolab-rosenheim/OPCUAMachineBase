
class VarDesc:
    """Describes how a var has to look like on the opcua server"""
    def __init__(self, var_name, var_type):
        self.var_name = var_name
        self.var_type = var_type


class MethodDesc:
    """Describes how a method has to look like on the opcua server"""
    def __init__(self, method, method_name, call_var_type, return_type):
        self.method = method
        self.method_name = method_name
        self.call_var_type = call_var_type
        self.return_type = return_type
