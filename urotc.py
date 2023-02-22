#!/usr/bin/env python3
import openstack
import sys
import os
import time
import re

from datetime import datetime
from argparse import ArgumentParser, Action

try:
  import winreg
  import requests
  has_winreg = True
except ModuleNotFoundError:
  has_winreg = False

def state_vm(c, vmname, args):
  srv = c.compute.find_server(vmname)
  if not srv:
    sys.stderr.write('{vmname}: VM not found\n'.format(vmname=vmname))
    sys.exit(16)
  srv = c.compute.get_server(srv)

  if not 'status' in srv:
    sys.stderr.write('Unable to determine VM status for {vmname}\n'.format(vmname=vmname))
    sys.exit(19)

  if args.mode == 'start':
    if srv['status'] != 'ACTIVE':
      c.compute.start_server(srv)
      srv = c.compute.wait_for_server(srv)
      print('Started vm {}'.format(vmname))
    else:
      print('vm {} is already started'.format(vmname))
  elif args.mode == 'stop':
    if srv['status'] != 'SHUTOFF':
      c.compute.stop_server(srv)
      srv = c.compute.wait_for_server(srv,status='SHUTOFF')
      print('Stopped vm {}'.format(vmname))
    else:
      print('vm {} is already stopped'.format(vmname))
  elif args.mode == 'reboot':
    if srv['status'] == 'ACTIVE':
      if args.forced:
        c.compute.reboot_server(srv,'HARD')
        print('HARD booting vm {name}'.format(name=vmname))
      else:
        c.compute.reboot_server(srv,'SOFT')
        srv = c.compute.wait_for_server(srv,status='REBOOT',wait=500)
        print('Rebooting vm {name}'.format(name=vmname))
        srv = c.compute.wait_for_server(srv,status='ACTIVE')
        print('Rebooted vm {name}'.format(name=vmname))
    else:
      print('vm {} is not in an active state'.format(vmname))


def show_vm(c, vmname, args):
  inst = c.compute.find_server(vmname)
  if not inst:
    sys.stderr.write('{vmname}: VM not found\n'.format(vmname=vmname))
    sys.exit(17)
  inst = c.compute.get_server(inst)
  
  t = dict(inst)
  if 'addresses' in t:
    t['ipv4'] = []
    t['mac'] = {}
    t['nets'] = []
    for netid in t['addresses']:
      t['nets'].append(netid)
      for a in t['addresses'][netid]:
        if 'OS-EXT-IPS-MAC:mac_addr' in a:
          t['mac'][a['OS-EXT-IPS-MAC:mac_addr']] = a['OS-EXT-IPS-MAC:mac_addr']
        t['ipv4'].append('{addr} ({type})'.format(addr=a['addr'],type=a['OS-EXT-IPS:type']))
    t['ipv4'] = ', '.join(t['ipv4'])
    t['mac'] =', '.join(t['mac'])
    t['nets'] = ', '.join(t['nets'])
  if 'flavor' in t:
    t['vcpus'] = t['flavor']['vcpus']
    t['ram'] = t['flavor']['ram']
    t['flavor_name'] = t['flavor']['original_name']
  for ts in ('created_at','launched_at','updated_at'):
    if not ts in t: continue
    if t[ts] is None: continue
    if t[ts].endswith('Z'):
      t[ts] = t[ts][:-1] + "+00:00"
    nk = ts[:-3] + "_ago"
    tt = int(time.time() - datetime.fromisoformat(t[ts]).timestamp())
    if tt > 86400:
      i = int(tt / 86400)
      if i == 1:
        txt = 'one day'
      else:
        txt = '{:,} days'.format(i)
    elif tt > 3600:
      i = int(tt/3600)
      if i == 1:
        txt = 'one hour'
      else:
        txt = '{} hours'.format(i)
    elif tt > 60:
      i = int(tt/60)
      if i == 1:
        txt = 'one minute'
      else:
        txt = '{} minutes'.format(i)
    else:
      txt = 'a few seconds'
    txt = txt + ' ago'
    t[nk] = txt

  if args.format:
    fmt = args.format
  else:
    print('{:16} {:5} {:>10} {:8} {}'.format('name','vcpus','ram','status','ip'))
    fmt = '{name:16} {vcpus:5} {ram:10,} {status:8} {ipv4} [{updated_ago}]'
  print(fmt.format(**t))

def proxy_auto_cfg():
  REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
  REG_KEY_NAME = 'AutoConfigURL'
  registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                                       winreg.KEY_READ)
  value, regtype = winreg.QueryValueEx(registry_key, REG_KEY_NAME)
  winreg.CloseKey(registry_key)

  if not value: return None, None, None

  # Remove proxy configurations temporarily
  save={}
  for proxy in ('http_proxy', 'https_proxy'):
    save[proxy] = os.getenv(proxy)
    if save[proxy]: os.environ[proxy] = ''

  resp = requests.get(value)

  # Restore proxy config
  for proxy in ('http_proxy', 'https_proxy'):
    if save[proxy]: os.environ[proxy] = save[proxy]
  
  if not resp.ok: return None, value, None
  
  mv = re.search(r'PROXY (\d+\.\d+\.\d+\.\d+:\d+);', resp.text)
  proxy = mv[1] if mv else None

  return proxy, value, resp.text

def show_autocfg(args):
  proxy, url, jstext = proxy_auto_cfg()

  if url: print('// AutoConfigURL: {url}'.format(url=url))
  if proxy: print('// Recognized proxy: {proxy}'.format(proxy=proxy))
  if jstext and args.debug:
    print('// Contents:')
    print(jstext)

###################################################################
#
# Main command line
#
###################################################################

def main(opts=None):
  cli = ArgumentParser(prog='UrOTC',
                        description='Your OTC operational calls',
                        add_help = False)
  cli.add_argument('-d','--debug', help='Enable debugging',action='store_true')
  if has_winreg:
    cli.add_argument('--show-proxy-autocfg', dest='dump_autocfg', help='Show proxy autocfg script', action='store_true')
    cli.add_argument('-A','--proxy-autocfg', dest='autocfg', help='Automatically guess proxy', action='store_true')
  subs = cli.add_subparsers()

  start_cli = subs.add_parser('start', help='Start VM')
  start_cli.set_defaults(func = state_vm, forced = False, mode = 'start')

  stop_cli = subs.add_parser('stop', help='Stop VM')
  stop_cli.set_defaults(func = state_vm, forced = False, mode = 'stop')

  reboot_cli = subs.add_parser('reboot', help='Re-boot VM')
  reboot_cli.add_argument('-f','--forced', help='Hard Reboot', action='store_true')
  reboot_cli.set_defaults(func = state_vm, forced = False, mode = 'reboot')

  status_cli = subs.add_parser('status', help='Show current VM state')
  status_cli.add_argument('-F','--format', help='Format to print')
  status_cli.set_defaults(func = show_vm)

  args = cli.parse_args()
  if args.debug: openstack.enable_logging(debug=True)

  if 'func' in args:
    if opts:
      cf = opts
      if args.debug: sys.stderr.write('Configured from .cfg\n')
    else:
      if args.debug: sys.stderr.write('Configuring from ENV\n')
      cf = {}
      errs = []
      for k in ('TOKEN_ID','TOKEN_PSK', 'DOMAIN', 'PROJECT', 'AUTH_URL', 'RESOURCE_ID'):
        cf[k] = os.getenv(k)
        if not cf[k]: errs.append(k)

      if len(errs) > 0:
        sys.stderr.write('Missing environment variables: {vars}\n'.format( vars=str(errs) ))
        sys.exit(54)

    if has_winreg and args.autocfg:
      proxy, url, jstext = proxy_auto_cfg()
      if proxy:
        os.environ['http_proxy'] = 'http://{proxy}/'.format(proxy=proxy)
        os.environ['https_proxy'] = 'http://{proxy}/'.format(proxy=proxy)
        if args.debug:
          sys.stderr.write('Using proxy: {proxy}\n'.format(proxy=proxy))

    cloud = openstack.connect(auth = {
      "username": cf['TOKEN_ID'],
      "password": cf['TOKEN_PSK'],
      "project_name": cf['PROJECT'],
      "user_domain_name": cf['DOMAIN'],
      "auth_url": cf['AUTH_URL']
    })

    args.func(cloud, cf['RESOURCE_ID'], args)
  else:
    if has_winreg:
      if args.dump_autocfg:
        show_autocfg(args)
        sys.exit(0)
    if args.debug:
      if opts:
        sys.stderr.write('Configured from .cfg\n')
      else:
        sys.stderr.write('Configuring from ENV\n')
    cli.print_help()

if __name__ == '__main__':
  main()

