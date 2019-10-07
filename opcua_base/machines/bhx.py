from threading import Thread
import time
from datetime import datetime
from os import path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from opcua import uamethod

from .machine import Machine
from tcp_sender.tcp_sender import TCPSender, TCPPacket
from machines.var_method_desc import VarDesc, MethodDesc

_IN_TIME_FORMAT = '%d.%m.%Y_%H:%M:%S'
_OUT_TIME_FORMAT = '%Y%m%d%H%M%S'


class BHX(Machine):
    def __init__(self, ip, port, bhx_logfolder, bhx_logfile, tcp_string_length, write_mes_files, mes_input_folder):
        opcua_variables = [VarDesc('log_date', 'string'), VarDesc('log_time', 'string'),
                           VarDesc('action', 'string'), VarDesc('first_number', 'int'),
                           VarDesc('program', 'string'), VarDesc('second_number', 'int')]
        opcua_methods = [MethodDesc(self.send_program, 'send_program', [('program_name', 'string')], 'boolean')]
        super().__init__(opcua_variables, opcua_methods)
        self._ip = ip
        self._port = int(port)
        self._bhx_logfolder = bhx_logfolder
        self._bhx_logfile = bhx_logfile
        self._tcp_string_length = int(tcp_string_length)
        self._write_mes_files = bool(write_mes_files)
        self._mes_input_folder = mes_input_folder
        self._mes_programs = {}
        self.m_log_date = None
        self.m_log_time = None
        self.m_action = None
        self.m_first_number = None
        self.m_program = None
        self.m_second_number = None
        self._subscriber_list = []
        self.thread_run_ok = True
        self.thread = Thread(target=self.fetch_logs, args=())

    @uamethod
    def send_program(self, _, program_name):
        """For sending a tcp packet which contains the program number to load to the Homag BHX"""
        TCPSender.send_packet(TCPPacket(self._ip, self._port, self._build_message(program_name)))

    def fetch_logs(self):
        m_log_filehandler = MachineLogfileHandler(self._bhx_logfolder, self._bhx_logfile)
        event_handler = m_log_filehandler
        observer = Observer()
        # Subscribe to MachineLofFileHandler
        m_log_filehandler.subscribe(self)
        observer.schedule(event_handler, self._bhx_logfolder, recursive=True)
        observer.start()
        while self.thread_run_ok:
            time.sleep(5)
        observer.stop()
        observer.join()

    def _build_message(self, program_name):
        """
        Builds the string that we can send via tcp_sender to the Homag BHX.
        If you need to know how the message should look like please read BHX_Socket.pdf in the doc folder
        :param program_name: name of program the machine should load
        :return: string that we can send to the BHX
        """
        if len(program_name) > self._tcp_string_length:
            raise ValueError(
                'Cannot build message because the program name length is larger than the tcp string length ')
        else:
            start = 'BARCODE:'
            end = '$'
            data = ''
            for i in range(self._tcp_string_length - len(program_name)):
                data += ' '
            data += program_name
            return start + data + end

    def _write_mes_file(self, var_name, content):
        """Gets called if BHX logfile changes and if activated writes a log file that the MES system imports"""
        if self._write_mes_files and var_name == 'bhx_machine_log':
            if content.program in self._mes_programs:
                start_datetime = datetime.strptime(self._mes_programs[content.program].log_date + '_' +
                                                   self._mes_programs[content.program].log_time, _IN_TIME_FORMAT)
                end_datetime = datetime.strptime(content.log_date + '_' + content.log_time, _IN_TIME_FORMAT)
                program_name = content.program.split('.mpr')[0].split('\\')[-1]

                string_to_write = self._mes_programs[content.program].action
                string_to_write += ',' + start_datetime.strftime(_OUT_TIME_FORMAT)
                string_to_write += ',' + content.program
                string_to_write += ',' + program_name
                string_to_write += ',' + content.action
                string_to_write += ',' + end_datetime.strftime(_OUT_TIME_FORMAT)
                with open(self._mes_input_folder + end_datetime.strftime(_OUT_TIME_FORMAT) + '.txt', 'w') as f:
                    f.write(string_to_write + '\n')
                    f.close()
                _ = self._mes_programs.pop(content.program, None)
            else:
                self._mes_programs[content.program] = content

    def start_thread(self):
        self.thread_run_ok = True
        self.thread.start()

    def stop_thread(self):
        self.thread_run_ok = False

    def subscribe(self, class_to_notify):
        """Other classes can use this method to subscribe for any changes"""
        if class_to_notify not in self._subscriber_list:
            self._subscriber_list.append(class_to_notify)

    def _notify(self, var_name, content):
        """Gets called if any changes happen. Other classes which are subscribed are called with the changes"""
        for subscriber in self._subscriber_list:
            subscriber.listener(var_name, content)

    def listener(self, var_name, content):
        """Other classes can use this to notify us on any var changes"""
        if var_name == 'bhx_machine_log':
            # Notify all who have subscribed to us
            self.m_log_date = content.log_date
            self._notify('log_date', self.m_log_date)
            self.m_log_time = content.log_time
            self._notify('log_time', self.m_log_time)
            self.m_action = content.action
            self._notify('action', self.m_action)
            self.m_first_number = content.first_number
            self._notify('first_number', self.m_first_number)
            self.m_program = content.program
            self._notify('program', self.m_program)
            self.m_second_number = content.second_number
            self._notify('second_number', self.m_second_number)

            # Write BHX files
            self._write_mes_file(var_name, content)


class MachineLogfileHandler(FileSystemEventHandler):
    """Reads the logfile from the machine and calls the subscribed classes"""
    def __init__(self, folder_to_watch, file_to_watch):
        self.folder_to_watch = folder_to_watch
        self.file_to_watch = file_to_watch
        self._subscriber_list = []
        self._last_line_read = ''

    def on_modified(self, event):
        """This method gets called if a file was changed in the folder that is monitored"""
        if event.event_type == 'modified' and event.src_path.endswith(self.file_to_watch):
            with open(self.folder_to_watch + self.file_to_watch, 'r') as f:
                lines = f.read().splitlines()
                if len(lines) > 0:
                    last_line = lines[-1]
                    log_date, log_time, action, first_number, program, second_number = last_line.split(',')
                    action = action.strip()

                    # For every line that is written the on_modified is called.
                    # So for a new line and the empty line after it, it is called two times.
                    # We prefent this with checking if the last_line is different
                    if self._last_line_read != last_line:
                        self._last_line_read = last_line
                        self._notify('bhx_machine_log',
                                     BHXMachineData(log_date, log_time, action, first_number, program, second_number))

    def subscribe(self, class_to_notify):
        """Other classes can use this method to subscribe for any changes"""
        if class_to_notify not in self._subscriber_list:
            self._subscriber_list.append(class_to_notify)

    def _notify(self, var_name, content):
        """Gets called if any changes happen. Other classes which are subscribed are called with the changes"""
        for subscriber in self._subscriber_list:
            subscriber.listener(var_name, content)


class BHXMachineData:
    """The data of a line from the machine logfile"""
    def __init__(self, log_date, log_time, action, first_number, program, second_number):
        self.log_date = log_date
        self.log_time = log_time
        self.action = action
        self.first_number = first_number
        self.program = program
        self.second_number = second_number
