# Plug P100
This is a fork of original work of [@K4CZP3R](https://github.com/K4CZP3R/tapo-p100-python)

The purpose of this fork is to provide the library as PyPi package. 

# How to install
```bash
cd /home/blu/git/plugp100 || exit
python3 -m venv venv
source venv/bin/activate
pip3 -r requirements.txt
```
# How to use
```python
# Usage: python plugp100helper.py <ip_address> <action>")
# Available actions: 'on', 'off', 'watt', 'info', 'energy', 'childlist', or 'componentlist'

# example to turn device on
cd /home/blu/git/plugp100 || exit
python3 -m venv venv
python3 plugp100-helper.py <deviceip> on
```
