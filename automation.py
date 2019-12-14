#!/usr/bin/env python

import pprint
import pyeapi
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import time
import logging
import colorlog
import sys
from datetime import datetime, timedelta
import argparse

__author__ = 'Ievgen Kostiukevych'
__copyright__ = 'Copyright 2019, Ievgen Kostiukevych'

# ===================Argument parser ===================

parser = argparse.ArgumentParser()
parser.add_argument('config', help='provide the config file')
parser.add_argument('api', help='provide the API json file')
parser.add_argument(
    'time', help='amount of seconds to wait before repeating tasks, default is 10 seconds', nargs='?', default=10, type=int)
parser.add_argument(
    '-vL', '--vlans_list', help='read vlans from the spreadsheet and create in the switch', action='store_true')
parser.add_argument('-iD', '--interfaces_description',
                    help='read interfaces descriptions from the spreadsheet and update in the switch', action='store_true')
parser.add_argument(
    '-iS', '--interfaces_status', help='read interfaces status from the switch and update in the spreadsheet', action='store_true')
parser.add_argument(
    '-iV', '--interfaces_vlans', help='read interfaces vlans from the spreadsheet and update in the switch', action='store_true')
parser.add_argument('-c', '--continious',
                    help='repeat activated tasks after 10 seconds (default, unless time is specified)', action='store_true')


args = parser.parse_args()
configFile = args.config
waitTime = args.time
config = {}
with open(configFile, 'r') as f:
    for line in f:
        (key, val) = line.split(':')
        config[key] = val.strip('\n')


# =================== Logger ===================

# Creates basic logger
logger = colorlog.getLogger()
# Sets logging level (options: DEBUG, INFO, WARNING, ERROR, CRITICAL)
logger.setLevel(colorlog.colorlog.logging.INFO)
# Adds coloring to the logger messages
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter())
logger.addHandler(handler)

# ===================JSON pretty print ===================
# Sets pretty print settings for JSON output to console
pp = pprint.PrettyPrinter(indent=1, stream=None)

# =================== Google sheet access ===================


def googleAuthorize():
    # Sets access to Google spreadsheets and Google drive
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    # Imports the JSON access token and extracts credential
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        args.api, scope)
    # Athorization with extracted credentials
    token = gspread.authorize(credentials)
    logger.info(' - Google Cloud API authorization successful')
    return(token)


# Initial authorization at program start
gc = googleAuthorize()

# Extracts data from the spreadsheet
switchConfigs = gc.open(config['spreadsheet'])
vlanList = switchConfigs.worksheet('Vlan List')
vlanPorts = switchConfigs.worksheet(
    'Interfaces VLAN Allocation and Descriptions')
interfacesMacTable = switchConfigs.worksheet('MAC addresses table')
interfacesStatusTable = switchConfigs.worksheet('Interfaces status table')


# =======================BEGIN FUNCTIONS DESCRIPTION======================


def setInterfaceDescriptions():
    # Reads interfaces description from the spreadsheet and writes to the switch
    logger.info('===========================================')
    logger.info(' - Updating interfaces descriptions...')
    vlanPortsRec = vlanPorts.get_all_records()
    for port in vlanPortsRec:
        portsDescription.set_description('Ethernet {}'.format(
            port['Port']), value=port['Description'])
    logger.info(' - Interfaces descriptions updated')


def createVlans():
    # Reads vlan list and names from the spreadsheet and writes to the switch
    logger.info('===========================================')
    logger.info(' - Updating vlan table...')
    vlanListRec = vlanList.get_all_records()
    vlans = connectedSwitch.api('vlans')
    vlans.autorefresh = True
    for vlan in vlanListRec:
        vlans.create(vlan['Vlan ID'])
        vlans.set_name(vlan['Vlan ID'], name=vlan['Vlan Name'])
    logger.info(' - Vlan table updated')


def setInterfaceVlans():
    # Reads interfaces vlans list from the spreadsheet and writes to the switch
    logger.info('===========================================')
    logger.info(' - Updating interface vlans...')
    currentVlans = portsVlans.getall()
    vlanPortsRec = vlanPorts.get_all_records()
    for port in vlanPortsRec:
        try:
            if str(port['Vlan']) != str(currentVlans['Ethernet{}'.format(port['Port'])]['access_vlan']):
                logger.warning(
                    '   - Modifying port {} - new access Vlan {}'.format(port['Port'], port['Vlan']))
                portsVlans.set_access_vlan('Ethernet {}'.format(
                    port['Port']), value=port['Vlan'])
            else:
                pass
        except KeyError:
            pass
    logger.info(' - Interface vlans updated')


def getInterfacesState():
    # Reads interfaces statuses and mac address table from the switch and writes to the spreadsheet
    logger.info('===========================================')
    logger.info(' - Updating interfaces status table..')

    getIterfaces = connectedSwitch.enable('show interfaces status')
    interfacesStatus = getIterfaces[0]['result']['interfaceStatuses']
    macAdrTable = connectedSwitch.enable('show mac address-table')
    unicastMacAdrTable = macAdrTable[0]['result']['unicastTable']['tableEntries']
    lldpTable = connectedSwitch.enable('show lldp neighbors detail')
    lldpTable = lldpTable[0]['result']['lldpNeighbors']

    header = ['bandwidth',
              'description', 'duplex', 'interfaceType', 'lineProtocolStatus', 'linkStatus', 'macAddress', 'entryType']
    # Define the cell range
    cellRange = interfacesStatusTable.range('A2:M100')

    # Sort by interface name
    interfaceList = []
    for interface in interfacesStatus.keys():
        interfaceList.append(interface)
    interfaceList.sort()

    # Flatten the list of dicts into a list of values in order
    flattened_test_data = []

    # ===================

    for i in interfaceList:
        for entry in unicastMacAdrTable:
            for value in entry.values():
                if value == i:
                    interfacesStatus[i].update(
                        {'macAddress': entry['macAddress']})
                    interfacesStatus[i].update(
                        {'entryType': entry['entryType']})
    # ===================

    for i in interfaceList:
        flattened_test_data.append(i)
        try:
            flattened_test_data.append(
                interfacesStatus[i]['vlanInformation']['vlanId'])
        except KeyError:
            flattened_test_data.append('Routed')

        for j in header:
            try:
                flattened_test_data.append(interfacesStatus[i][j])
            except KeyError:
                flattened_test_data.append('N/A')

    # ===================

        try:
            flattened_test_data.append(
                lldpTable[i]['lldpNeighborInfo'][0]['chassisId'])
        except IndexError:
            flattened_test_data.append('N/A')
        except KeyError:
            flattened_test_data.append('N/A')
        try:
            flattened_test_data.append(
                lldpTable[i]['lldpNeighborInfo'][0]['neighborInterfaceInfo']['interfaceId'])
        except IndexError:
            flattened_test_data.append('N/A')
        except KeyError:
            flattened_test_data.append('N/A')
        try:
            flattened_test_data.append(
                lldpTable[i]['lldpNeighborInfo'][0]['ttl'])
        except IndexError:
            flattened_test_data.append('N/A')
        except KeyError:
            flattened_test_data.append('N/A')

    # Send flattened list to the cell range to be re-rendered as a table
    for i, cell in enumerate(cellRange):
        try:
            cell.value = flattened_test_data[i]
        except IndexError:
            pass

    interfacesStatusTable.update_cells(cellRange)
    logger.info(' - Interfaces status table updated')


def wait(message):
    # Introduces delay between task repetition and emergency delay after API quota error
    if message == 'api':
        logger.error(
            ' - API quota exceeded! Waiting for 100 seconds before restarting...')
        for i in range(100, 0, -1):
            sys.stdout.write(str(i)+' ')
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write('\n')
    elif message == 'wait':
        logger.info('===========================================')
        logger.info(
            ' - Tasks completed. Waiting for {} seconds before restarting...'.format(waitTime))
        for i in range(waitTime, 0, -1):
            sys.stdout.write(str(i)+' ')
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write('\n')

# ====================================END FUNCTIONS DESCRIPTION====================

# =================================== MAIN FUNCTION ==============================


# First - connect to the switch and check connection and eAPI
connect = pyeapi.client.connect(
    transport='https', host=config['ip'], username=config['username'], password=config['password'])
logger.info(
    ' - Trying to connect to {} using provided username and password'.format(config['ip']))
connectedSwitch = pyeapi.client.Node(connect)
hostname = connectedSwitch.enable('show hostname')
logger.info(' - Succsessfully connected to ' +
            hostname[0]['result']['hostname'])
version = connectedSwitch.enable('show version')
logger.info(pp.pprint(version[0]['result']))
# Second - read initial data from the switch
vlans = connectedSwitch.api('vlans')
portsVlans = connectedSwitch.api('switchports')
portsDescription = connectedSwitch.api('interfaces')

# Start executing selected tasks when continious flag is not set

if args.vlans_list and not args.continious:
    createVlans()

if args.interfaces_description and not args.continious:
    setInterfaceDescriptions()

if args.interfaces_vlans and not args.continious:
    setInterfaceVlans()

if args.interfaces_status and not args.continious:
    getInterfacesState()

if not args.continious:
    logger.info('===========================================')
    logger.info(' - All tasks finished. Exiting...')

# Tasks repetition when continious flag is set
# Each task can be interrupted by the Google API exhaustion error. 1 minute wait is introduced.

try:
    while args.continious:
        logger.info(' - ' + str(datetime.now().replace(microsecond=0)))
        logger.info(' - Succsessfully connected to ' +
                    hostname[0]['result']['hostname'])
        if args.vlans_list:
            try:
                createVlans()
            except gspread.exceptions.APIError:
                wait('api')
                del gc
                gc = googleAuthorize()
        if args.interfaces_description:
            try:
                setInterfaceDescriptions()
            except gspread.exceptions.APIError:
                wait('api')
                del gc
                gc = googleAuthorize()
        if args.interfaces_vlans:
            try:
                setInterfaceVlans()
            except gspread.exceptions.APIError:
                wait('api')
                del gc
                gc = googleAuthorize()
        if args.interfaces_status:
            try:
                getInterfacesState()
            except gspread.exceptions.APIError:
                wait('api')
                del gc
                gc = googleAuthorize()
        wait('wait')
        del gc
        gc = googleAuthorize()
except KeyboardInterrupt:
    logger.info('Stopped')
