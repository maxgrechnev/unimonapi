#!/usr/bin/env python

import argparse, getpass, json, sys, logging, unimonapi, traceback

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(message)s'
DEFAULT_ZABBIX_URL = 'http://localhost/zabbix'
JSON_INDENT = 2

super_parser = argparse.ArgumentParser(description='Zabbix command line interface')
subparsers = super_parser.add_subparsers(title='valid subcommands', help='action to be done', dest='action')

login_parser = argparse.ArgumentParser(add_help=False)
login_parser.add_argument('-u', '--url', default=DEFAULT_ZABBIX_URL, help='Zabbix URL')
login_parser.add_argument('-l', '--login', required=True, help='Zabbix user login')
login_parser.add_argument('-p', '--password', help='Zabbix user password')

import_parser = subparsers.add_parser('import', description='import Zabbix configuration via API', parents=[login_parser])
import_parser.add_argument('-f', '--file', required=True, help='import from file')
import_parser.add_argument('-s', '--skip', action='store_true', help='skip (do not import) configurations that already exist (update by default)')
import_parser.add_argument('-d', '--delete', action='store_true', help='delete existing configurations that are not in the import file')

export_parser = subparsers.add_parser('export', description='export Zabbix configuration via API', parents=[login_parser])
export_parser.add_argument('-f', '--file', help='export to file (defaults to stdout)')
export_parser.add_argument('-j', '--json', action='store_true', help='pretty-printed JSON object')
export_parser.add_argument('-t', '--temp', action='store_true', help='export auto-created/discovered/temporary configurations')

args = super_parser.parse_args()
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, stream=sys.stderr)

try:
    if not args.password:
        args.password = getpass.getpass('Zabbix user password: ', sys.stderr)

except BaseException:
    sys.stderr.write('Exit\n')
    sys.exit(0)

zabbix_api = unimonapi.ZabbixAPI(args.url, args.login, args.password)

if args.action == 'export':
    export_result = zabbix_api.export_config(args.temp)
    json_indent = JSON_INDENT if args.json else None

    if args.file:
        with open(args.file, 'w') as f:
            json.dump(export_result, f, indent=json_indent)
    else:
        json.dump(export_result, sys.stdout, indent=json_indent)
        sys.stdout.write('\n')

    logging.info('Configurations exported successfully')
else:
    with open(args.file, 'r') as f:
        config_to_import = json.load(f)

    zabbix_api.import_config(config_to_import, not args.skip, args.delete)
    logging.info('Configurations imported successfully')
