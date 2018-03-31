#!/usr/bin/python

"""
This module provides a way to call indicator-xrandr service from command line.

Put this script in one of your keyboard shortcuts to control
indicator-xrandr-brightness

Created on 21 sept. 2016

@author: hilault

"""

# Copyright (C) 2016  Hilault
# Copyright (C) 2013  Erwin Rohde Many thanks to Jan Simon for setting up and
# maintaining this indicator in launchpad. Dbus code heavily borrowed from
# https://github.com/majorsilence/pygtknotebook/tree/master/examples/dbus
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA.

import argparse

import dbus


def set_brightness(args):
    """ set brightness up (--up) or down (--down) """
    bus = dbus.SessionBus()
    proxy = bus.get_object('com.ubuntu.indicator.xrandr', '/adjust')
    control_interface = dbus.Interface(proxy, 'com.ubuntu.indicator.xrandr')
    if args.up:
        control_interface.brightness_up()
    if args.down:
        control_interface.brightness_down()


#===============================================================================
# Main
#===============================================================================

def main():
    """ Main function """
    parser = argparse.ArgumentParser(
        description="Adjust screen brightness through dbus and indicator-"
                    "xrandr."
    )
    parser.add_argument('--up', action='store_true', help="Brightness up")
    parser.add_argument('--down', action='store_true', help="Brightness down")
    args = parser.parse_args()
    set_brightness(args)


if __name__ == "__main__":
    main()
