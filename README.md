# Google Spreadsheet Driven Arista eAPI Automation Demo

This script realizes the concept of "SDN - Spreadsheet Defined Network" (c) Anthony P. Kuzub, CBC/ Radio Canada

The script uses Google Drive and Spreadsheet APIs to get the information that is propagated into the Arista switches using eAPI.
It was written to solve one particular use case, but can be used as a demo of using a Google spreadsheet as a data source for switch configuration.
It will also read some information from the switch and populate a separate tab of the spreadsheet.

The functionality currently realised:

- Reading the vlan list and vlan names from the spreadsheet and creating them in the switch

- Reading interface descriptions and access vlans from the spreadsheet and setting them in the switch (only one vlan per interface can be set via the script, trunk ports are not affected)

- Reading interfaces status and the mac address table from the switch and writing the data to the spreadsheet

The script is using [oauth2client](https://github.com/googleapis/oauth2client) library for authentication and [gspread](https://github.com/burnash/gspread) to access Goggle APIs.
The script is tailored for Arista switches and is using [pyeapi](https://github.com/arista-eosplus/pyeapi).

The Google spreadsheet needs to follow the exact format.
A sample spreadsheet can be found [HERE](https://docs.google.com/spreadsheets/d/12l3Q-th76AO2daifAsOwWcnlWg6zrYHp_pXvaQWuEgI/edit?usp=sharing)
Please use "save as copy" to be able to edit.
The demo spreadsheet was used to drive a vEOS instance, therefore it is only limited to 12 ports.
More ports and vlans can be added to the spreadsheet.
Ports of >10GbE and multi-lane ports are also supported (e.g. Ethernet7/3).

User needs to supply the Google API json access token.
Example token is provided, however it is a dummy file that will **not** give you access to any Google API resources.
You **have** to provide your own API token.
Follow the first step from this article as a how-to: [LINK](https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html)

User also needs to suply a config file that has an **exact** name of the spreadsheet in your Google drive, IP address or a fully qualified domain name (FQDN) of the switch, and login and pass to the switch.

Example config file is provided.

```bash
spreadsheet:Switches
ip:172.16.158.100
username:admin
password:admin
```

## Requirements

```bash
pyeapi
gspread
oauth2client
colorlog
```

## Installation

Clone the repo.

```bash
git clone https://github.com/ievgen-kostiukevych/Google-Spreadsheet-Driven-Arista-eAPI-Automation-Demo.git
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install dependencies.

```bash
pip install requirements
```

## Usage example

Use `-h` for how-to use.

```bash
usage: automation.py [-h] [-vL] [-iD] [-iS] [-iV] [-c] config api [time]

positional arguments:
  config                provide the config file
  api                   provide the API json file
  time                  amount of seconds to wait before repeating tasks,
                        default is 10 seconds

optional arguments:
  -h, --help            show this help message and exit
  -vL, --vlans_list     read vlans from the spreadsheet and create in the
                        switch
  -iD, --interfaces_description
                        read interfaces descriptions from the spreadsheet and
                        update in the switch
  -iS, --interfaces_status
                        read interfaces status from the switch and update in
                        the spreadsheet
  -iV, --interfaces_vlans
                        read interfaces vlans from the spreadsheet and update
                        in the switch
  -c, --continious      repeat activated tasks after 10 seconds (default,
                        unless time is specified)
```

Examples:

```bash
python automation.py -vL -iD -iS -iV -c demo_config.cfg switch-automation-api.json 30
```

Script will execute all tasks every 30 seconds using `switch-automation-api.json` Google API access token and `demo_config.cfg` config source file

```bash
python automation.py -iD demo_config.cfg switch-automation-api.json
```

Script will update interfaces descriptions once and will exit.

```bash
python automation.py -iV -c demo_config.cfg switch-automation-api.json
```

Script will update interfaces access vlans every 10 seconds (default timeout value).

To stop the continious execution use keyboard interrupt `CTRL/CMD + C`

## Contributing

This project is a demo, it is not heavily maintained.
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Release History

- 0.1.0
  - The first public release

## TO DOs

- Migrate from depricated `oauth2client` library

## Meta

Thanks you to Robert Welch (Arista Networks) and Anthony P. Kuzub (CBC/Radio Cannada) for support and inspiration

## Licenses

Author – [Ievgen Kostiukevych](https://github.com/ievgen-kostiukevych), European Broadcasting Union, Technology and Innovation

[MIT](https://choosealicense.com/licenses/mit)

[pyeapi](https://github.com/arista-eosplus/pyeapi) is [Copyright (c) 2015, Arista Networks EOS+ All rights reserved.](https://github.com/arista-eosplus/pyeapi/blob/develop/LICENSE)

## Disclaimer

The software is provided "As is", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
Use at your own risk.
Lab testing is ALWAYS recomended before any use for production network.
