#
# Prepare things
#
import os
import sys
from cryptography.fernet import Fernet

cfkey = Fernet.generate_key()
CFSTR = '{cfkey}'

if len(sys.argv) != 3:
  sys.stderr.write('Usage: {cmd} src dst\n'.format(cmd=sys.argv[0]))
  sys.exit(1)

with open(sys.argv[1],'r') as inp:
  script = inp.read()
  if script.find(CFSTR) == -1:
    sys.stderr.write('Error finding key string {CFSTR}\n'.format(CFSTR=CFSTR));
    sys.exit(2)

  i = script.find(CFSTR)
  while i != -1:
    script = script[:i] + str(cfkey) + script[i+len(CFSTR):]
    i = script.find(CFSTR, i + len(str(cfkey)) - len(CFSTR))
  
  with open(sys.argv[2],'w') as outp:
    outp.write(script)

