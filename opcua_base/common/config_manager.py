import configparser


class ConfigManager:
    _config_folder = '/data'
    _bhx_config = None
    _base_config = None

    def __init__(self, config_folder):
        ConfigManager._config_folder = config_folder

    @staticmethod
    def get_config_folder():
        return ConfigManager._config_folder

    @staticmethod
    def get_base_cfg():
        if ConfigManager._base_config:
            return ConfigManager._base_config
        else:
            ConfigManager._base_config = configparser.ConfigParser()
            ConfigManager._base_config.read(ConfigManager._config_folder + '/base.ini')
            return ConfigManager._base_config

    @staticmethod
    def get_bhx_cfg():
        if ConfigManager._bhx_config:
            return ConfigManager._bhx_config
        else:
            ConfigManager._bhx_config = configparser.ConfigParser()
            ConfigManager._bhx_config.read(ConfigManager._config_folder + '/bhx.ini')
            return ConfigManager._bhx_config
