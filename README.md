# OPCUA Machine Base #

## Contributors
- [Michael List](https://github.com/orgs/protolab-rosenheim/people/Michael-List)

## Create .exe from project ##
* Load venv
* cd in your project directory
```
pyinstaller .\opcua_base\opcua_base_starter.py --clean -p opcua_base
```
* A dependency is the VC++ Redistributable(Visual C++ Redistributable for Visual Studio 2015 ), otherwise errors will occur
    * Download here: https://www.microsoft.com/en-us/download/details.aspx?id=48145
