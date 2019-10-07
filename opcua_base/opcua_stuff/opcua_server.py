from threading import Thread
import time
import logging
from opcua import ua, Server


class OPCUAServer:
    """OPCUA server for different machines"""
    def __init__(self, ip_address, port, machine=None):
        self._logger = logging.getLogger(__name__)
        self._machine = machine
        self._port = str(port)
        self._ip_address = ip_address
        self._variables = {}
        self.thread_run_ok = True
        self.thread = Thread(target=self.server, args=())

    def server(self):
        server_name = self._machine.__class__.__name__
        # Now setup our server
        server = Server()
        server.set_endpoint('opc.tcp://' + self._ip_address + ':' + self._port + '/')
        server.set_server_name(server_name + 'OPCUA-Server')

        # Setup namespace
        machine_ns = server.register_namespace(server_name)
        machine_obj = server.nodes.objects.add_object(machine_ns, server_name)

        # Setup variables
        for var_desc in self._machine.opcua_variables:
            if var_desc.var_type == 'string':
                self._variables[var_desc.var_name] = machine_obj.add_variable(machine_ns, var_desc.var_name, '',
                                                                              self._get_datatype(var_desc.var_type))
            elif var_desc.var_type == 'int':
                self._variables[var_desc.var_name] = machine_obj.add_variable(machine_ns, var_desc.var_name, -1,
                                                                              self._get_datatype(var_desc.var_type))

        # Setup methods
        for method_desc in self._machine.opcua_methods:
            var_list = []
            for var_type in method_desc.call_var_type:
                    var_list.append(self._get_datatype(var_type))

            machine_obj.add_method(machine_ns, method_desc.method_name, method_desc.method, var_list,
                                   [self._get_datatype(method_desc.return_type)])

        # Subscribe to machine
        self._machine.subscribe(self)

        # Start server
        try:
            server.start()
            self._logger.info('OPCUA-Server started')

            while self.thread_run_ok:
                time.sleep(2)

            server.stop()
            self._logger.info('OPCUA-Server stopped')
        except OSError as e:
            self.thread_run_ok = False
            self._logger.critical('OS error: {0}'.format(e))

    def start_server(self):
        self.thread_run_ok = True
        self.thread.start()

    def stop_server(self):
        self.thread_run_ok = False

    def _get_datatype(self, datatype):
        # Check datatype and set it -> fallback is string
        if datatype == 'string':
            return ua.VariantType.String
        elif datatype == 'boolean':
            return ua.VariantType.Boolean
        elif datatype == 'int':
            return ua.VariantType.Int64
        else:
            return ua.VariantType.String

    def listener(self, var_name, content):
        """Other classes can use this to notify us on any var changes"""
        if var_name in self._variables:
            self._logger.debug('Updated var_name({0}) with value: {1}'.format(var_name, content))
            self._variables[var_name].set_value(content)
