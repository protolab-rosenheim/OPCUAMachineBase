from .bhx import BHX

"""In this file all factorys for the different machines should be added"""


class BHXFactory:
    @staticmethod
    def create_bhx(bhx_config):
        return BHX(bhx_config['general']['ip_address'], bhx_config['general']['port'],
                   bhx_config['general']['bhx_logfolder'], bhx_config['general']['bhx_logfile'],
                   bhx_config['general']['tcp_string_length'], bhx_config['mes_files']['write_mes_files'],
                   bhx_config['mes_files']['mes_input_folder'])
