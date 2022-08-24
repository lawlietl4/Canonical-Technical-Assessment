#!/usr/bin/env python

import argparse
import pathlib
import os
import psutil
import math

# Usage:
#   disk_cpu_load.py [ --max-load <load> ] [ --xfer <mebibytes> ]
#                    [ --verbose ] [ <device-filename> ]
#
# Parameters:
#  --max-load <load> -- The maximum acceptable CPU load, as a percentage.
#                       Defaults to 30.
#  --xfer <mebibytes> -- The amount of data to read from the disk, in
#                        mebibytes. Defaults to 4096 (4 GiB).
#  --verbose -- If present, produce more verbose output
#  <device-filename> -- This is the WHOLE-DISK device filename (with or
#                       without "/dev/"), e.g. "sda" or "/dev/sda". The
#                       script finds a filesystem on that device, mounts
#                       it if necessary, and runs the tests on that mounted
#                       filesystem. Defaults to /dev/sda.

global cpu_load
global total

def get_params():
    global max_load
    global xfer
    global total
    parser = argparse.ArgumentParser(description="Script to test CPU load imposed by a simple disk read operation")
    parser.add_argument("device", help="specify which block device to test (default: /dev/sda)", type=str, default="/dev/sda", nargs="?")
    parser.add_argument("--max-load", help="Changes maximum acceptable CPU load (default: 30)", type=int, default=30, dest='max_load')
    parser.add_argument("--xfer", help = "Amount of data to read from the disk in Mebibytes (default: 4096Mib)", type=int, default=4096, dest='xfer')
    parser.add_argument('-v', "--verbose", action='store_true', help = "Produces a verbose output")
    args = parser.parse_args()
    global disk_device
    disk_device = args.device
    max_load = args.max_load
    xfer = args.xfer
    if args.verbose:
        global verbose
        verbose = True
    else:
        if not pathlib.Path(disk_device).is_block_device():
            print(f"Unknown block device \"{disk_device}\"")
            parser.print_help()
    pass

def compute_cpu_load(start,end):
    global cpu_load
    global total
    __start_use = start
    __end_use = end
    __diff_idle = round(__end_use, 3) - round(__start_use, 3)
    __diff_total = __end_use - __start_use
    __diff_used = math.fabs(__diff_total - __diff_idle)

    if verbose:
        print(f"Start CPU time = {__start_use}")
        print(f"End CPU time = {__end_use}")
        print(f"CPU time used = {__diff_used}")
        print(f"Total elapsed time = {__diff_total}")

    if __diff_total != 0:
        cpu_load = math.trunc(__end_use)
    else:
        cpu_load = 0
    pass

get_params()
retval=0
print(f"Testing CPU load when reading {xfer} MiB from {disk_device}")
print(f"Maximum acceptable CPU load is {max_load}")
os.system(f"blockdev --flushbufs '{disk_device}'")
l1, l2, l3 = psutil.getloadavg()
start_load = (l3 / os.cpu_count()) * 100
if verbose:
    print("Beginning disk read....")
os.system(f'dd if={disk_device} of=/dev/null bs=1048576 count={xfer} status=none')
l1, l2, l3 = psutil.getloadavg()
end_load = (l3 / os.cpu_count()) * 100
if verbose:
    print("Disk read complete!")
compute_cpu_load(start_load, end_load)
print(f"Detected disk read CPU load is {cpu_load}")
if int(cpu_load) >= int(max_load) :
    retval=1
    print("""*** DISK CPU LOAD TEST HAS FAILED! ***""")
exit(f"exiting with status code: {retval}")
