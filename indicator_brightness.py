#!/usr/bin/python

"""
This module provides a Unity indicator to adjust screen brightness by software,
using xrandr, on desktop computers with no hardware support for this feature.

This indicator should not be used on laptops as the software method is not as
power efficient as the hardware one.

Created on 21 sept. 2016

@author: hilault

"""

# Copyright (C) 2016  Hilault
# This software is based heavily on code from the following projects
# - indicator-brightness by Erwin Rohde (https://launchpad.net/indicator-brightness)
# xrandr calls are borrowed from the following projects:
# - brightness-control by Ravikiran Janardhana (https://github.com/ravikiranj/brightness-control)
# - Brightness Controller by Amit Seal Ami (https://github.com/lordamit/Brightness)
# Many thanks to their authors.

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
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import subprocess
import re
import os.path
import time

import gtk
import gobject
import appindicator

import dbus.service
from dbus.mainloop.glib import DBusGMainLoop


#==============================================================================
# Utils
#==============================================================================

HOME = os.path.expanduser("~")


def closest(num, steps):
    """ Get step closest to num """
    return min(steps, key=lambda x: abs(x-num))


def linspace(start, stop, nvals):
    """ See numpy.linspace """
    if nvals < 2:
        return stop
    diff = (float(stop) - start)/(nvals - 1)
    return [int(diff*i) + start for i in range(nvals)]


def get_active_monitor():
    """ Get active monitor identifier """
    output = subprocess.check_output(
        "xrandr -q | grep ' connected' | cut -d ' ' -f1", shell=True
    )
    if output:
        monitor = output.split('\n')[0]
    return monitor


#==============================================================================
# Optional DBusObject
#==============================================================================

class DBusObject(dbus.service.Object):
    """ DBus object interface in order to use session key bindings for changing
    brightness

    """

    def __init__(self, brightness_indicator, conn=None, object_path=None,
                 bus_name=None):
        self._indicator = brightness_indicator
        super(self.__class__, self).__init__(conn=conn, object_path=object_path,
                                             bus_name=bus_name)

    @dbus.service.method('com.ubuntu.indicator.xrandr')
    def brightness_down(self):
        """ Decrease brightness via indicator """
        self._indicator.brightness_down()

    @dbus.service.method('com.ubuntu.indicator.xrandr')
    def brightness_up(self):
        """ Increase brightness via indicator """
        self._indicator.brightness_up()


#==============================================================================
# Interface
#==============================================================================

class BrightnessIndicator(appindicator.Indicator):
    """ Main indicator class """

    def __init__(self, maxsteps):
        self._conf_path = os.path.join(HOME, ".xrand_brightness.sav")
        self._brightness_settings = linspace(20, 100, maxsteps)
        self._brightness_settings.append(100)
        self._monitor = get_active_monitor()
        self._curr_brightness = self.load_brightness()
        super(self.__class__, self).__init__(
            "indicator-xrandr",
            os.path.dirname(os.path.realpath(__file__)) +
            "/notification-display-brightness-full.svg",
            appindicator.CATEGORY_HARDWARE
        )
        # time.sleep(5)
        self.set_brightness(self._curr_brightness)

    def create_menu(self):
        """ Create dynamically menu on demand """
        curr_brightness = self.get_curr_brightness()
        menu = gtk.Menu()
        for i in range(len(self._brightness_settings)-1, -1, -1):
            buf = "%d" % i
            if i == curr_brightness:
                buf = u"%d \u2022" % i
            menu_items = gtk.MenuItem(buf)
            menu.append(menu_items)
            menu_items.connect("activate", self.menuitem_response, buf)
            menu_items.show()
        # show the items
        self.set_menu(menu)

    def save_brightness(self):
        """ Save brightness in local config file """
        with open(self._conf_path, "w") as sav_file:
            sav_file.write('%d' % self._curr_brightness)

    def load_brightness(self):
        """ Load brightness from local config file """
        try:
            with open(self._conf_path, "r") as sav_file:
                val = int(sav_file.read())
        except (ValueError, IOError):
            val = 100
        return val

    def menuitem_response(self, _, buf):
        """ Set action when menu is activated """
        buf = re.sub('[^\d]', '', buf)  # pylint: disable=W1401
        self.set_brightness(self._brightness_settings[int(buf)])

    def get_curr_brightness(self):
        """ Get current brightness from xrandr """
        try:
            output = subprocess.check_output(
                "xrandr --verbose | grep -i brightness | cut -f2 -d ' '",
                shell=True
            )
            if output:
                curr_brightness = int(float(output.split('\n')[0])*100)
            num = closest(curr_brightness, self._brightness_settings)
        except:
            num = 0
        return self._brightness_settings.index(num)

    def set_brightness(self, brightness):
        """ Set brightness via xrandr for active monitor """
        val = float(brightness)/100
        cmd = "xrandr --output %s --brightness %.2f" % (self._monitor, val)
        subprocess.check_output(cmd, shell=True)
        self._curr_brightness = brightness
        self.save_brightness()
        self.create_menu()

    def brightness_up(self):
        """ Increase brightness """
        curr_brightness = self.get_curr_brightness()
        curr_brightness = curr_brightness + 1
        if curr_brightness > len(self._brightness_settings)-1:
            curr_brightness = len(self._brightness_settings)-1
        self.set_brightness(self._brightness_settings[curr_brightness])

    def brightness_down(self):
        """ Decrease brightness """
        curr_brightness = self.get_curr_brightness()
        curr_brightness = curr_brightness-1
        if curr_brightness == -1:
            curr_brightness = 0
        self.set_brightness(self._brightness_settings[curr_brightness])

    def unlock_handler(self, *args, **kwargs):
        """ Inspect the bus for lock/unlock session messages.

        This is required to re-apply current brightness when session is locked-
        unlocked, or when switching account.

        """
        str_, bus_array = args
        try:
            job = str(bus_array[0])
            if (str_ == "stopping" and
                    job == 'JOB=unity-panel-service-lockscreen'):
                time.sleep(0.1)
                self.set_brightness(self._curr_brightness)
        except IndexError:
            return


# =============================================================================
# Main
# =============================================================================

def main():
    """ Main function """
    indicator = BrightnessIndicator(10)
    indicator.set_status(appindicator.STATUS_ACTIVE)
    # Start loop and create service object
    DBusGMainLoop(set_as_default=True)
    loop = gobject.MainLoop()
    session_bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.ubuntu.indicator.xrandr",
                                    bus=session_bus)
    DBusObject(indicator, object_path="/adjust", bus_name=bus_name)
    # Monitor session lock/unlock events
    session_bus.add_signal_receiver(indicator.unlock_handler,
                                    dbus_interface='com.ubuntu.Upstart0_6',
                                    member_keyword='EventEmitted')
    loop.run()


if __name__ == "__main__":
    main()
