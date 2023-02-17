#
# Example PRIV
#
import os
import sys
from cryptography.fernet import Fernet
import urotc

cfkey = {cfkey}
f = Fernet(cfkey)

def cfname():
  if getattr(sys,'frozen',False):
    run = sys.executable
  else:
    run = __file__
  run = os.path.abspath(run)
  dirname = os.path.dirname(run)
  basename = os.path.basename(run)
  # ~ print('dirname={dirname}'.format(dirname=dirname))
  # ~ print('basename={basename}'.format(basename=basename))

  if '.' in basename:
    # Remove file extension
    i = basename.find('.')
    if i > 0: basename = basename[:i]

  return dirname + os.path.sep + basename + '.cfg'


if len(sys.argv) == 2 and sys.argv[1] == 'encode':
  # encode strings...
  cfgfile = cfname()
  cfblob = ''
  for k in ('TOKEN_ID','TOKEN_PSK', 'DOMAIN', 'PROJECT', 'AUTH_URL', 'RESOURCE_ID'):
    cf = os.getenv(k)
    if not cf:
      sys.stderr.write('{k}: missing key\n'.format(k=k))
      continue
    cfblob += k +':'+cf +'\n'

  cfencr = f.encrypt(cfblob.encode())

  print('Writing to {cfgfile}'.format(cfgfile=cfgfile))
  with open(cfgfile,'wb') as fp:
    fp.write(cfencr)

  sys.exit(0)

def readcfg():
  cfgfile = cfname()
  opts = dict()
  with open(cfgfile,'rb') as fp:
    cfencr = fp.read()
    cfblob = f.decrypt(cfencr)
    
    for ln in cfblob.decode().split('\n'):
      ln = ln.strip()
      if  not ':' in ln: continue
      k = ln.split(':',1)
      opts[k[0]] =  k[1]

  return opts

#
# Actual run...
#
urotc.main(readcfg())

