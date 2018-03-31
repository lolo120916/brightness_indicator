#!/usr/bin/python

# With this indicator you can set your screen brightness in Unity.
#
# Copyright (C) 2011  Erwin Rohde Many thanks to Jan Simon for setting up and
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
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import subprocess
import re
import os.path


import gtk
import appindicator

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop


#==============================================================================
# Module variables
#==============================================================================

# Depends on gnome-settings-daemon
MAXSTEPS = 15
INDICATOR = None
MAX_BRIGHTNESS = 100
BRIGHTNESS_SETTINGS = None


#==============================================================================
# Utils
#==============================================================================

def closest(num, steps):
    """ Get step closest to num """
    return min(steps, key=lambda x: abs(x-num))


#==============================================================================
# Optional DBusObject
#==============================================================================

class DBusObject(dbus.service.Object):
    """ DBus object interface in order to use session key bindings for changing
    brightness

    """

    @dbus.service.method(dbus_interface='com.ubuntu.indicator.brightness',
                         in_signature='', out_signature='')
    def brightness_down(self):
        brightness_down()

    @dbus.service.method(dbus_interface='com.ubuntu.indicator.brightness',
                         in_signature='', out_signature='')
    def brightness_up(self):
        brightness_up()


#==============================================================================
# Module interface
#==============================================================================

def menuitem_response(w, buf):
    """ Set action when menu is activated """
    buf = re.sub('[^\d]', '', buf)  # pylint: disable=W1401
    set_brightness(str(BRIGHTNESS_SETTINGS[int(buf)]))


def scroll_wheel_icon(w, m, d):
    if int(d) == int(gtk.gdk.SCROLL_DOWN):
        brightness_down()
    elif int(d) == int(gtk.gdk.SCROLL_UP):
        brightness_up()


def brightness_up():
    curr_brightness = get_curr_brightness()
    curr_brightness = curr_brightness + 1
    if curr_brightness > len(BRIGHTNESS_SETTINGS)-1:
        curr_brightness = len(BRIGHTNESS_SETTINGS)-1
    set_brightness(str(BRIGHTNESS_SETTINGS[curr_brightness]))


def brightness_down():
    curr_brightness = get_curr_brightness()
    curr_brightness = curr_brightness-1
    if curr_brightness == -1:
        curr_brightness = 0
    set_brightness(str(BRIGHTNESS_SETTINGS[curr_brightness]))


def set_brightness(brightness):
    val = float(brightness)/MAX_BRIGHTNESS
    subprocess.call(
        ['pkexec',
         '/usr/lib/gnome-settings-daemon/gsd-backlight-helper',
         '--set-brightness', "%s" % brightness]
        )
    create_menu(INDICATOR)


def get_curr_brightness():
    try:
        p = subprocess.Popen(
            ['pkexec', '/usr/lib/gnome-settings-daemon/gsd-backlight-helper',
             '--get-brightness'], stdout=subprocess.PIPE
        )
        curr_brightness = int(p.communicate()[0])
        num = closest(curr_brightness, BRIGHTNESS_SETTINGS)
    except:
        num = 0
    return BRIGHTNESS_SETTINGS.index(num)


def get_brightness_settings():
    bs = range(0, MAX_BRIGHTNESS, MAX_BRIGHTNESS/MAXSTEPS)
    bs.append(MAX_BRIGHTNESS)
    return bs


def create_menu(ind):
    curr_brightness = get_curr_brightness()
    menu = gtk.Menu()
    for i in range(len(BRIGHTNESS_SETTINGS)-1, -1, -1):
        buf = "%d" % i
        if i == curr_brightness:
            buf = u"%d \u2022" % i
        menu_items = gtk.MenuItem(buf)
        menu.append(menu_items)
        menu_items.connect("activate", menuitem_response, buf)
        menu_items.show()
    # show the items
    ind.set_menu(menu)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    INDICATOR = appindicator.Indicator(
        "indicator-brightness",
        os.path.dirname(os.path.realpath(__file__)) +
        "/notification-display-brightness-full.svg",
        appindicator.CATEGORY_HARDWARE
    )
    INDICATOR.set_status(appindicator.STATUS_ACTIVE)
    INDICATOR.connect("scroll-event", scroll_wheel_icon)
    BRIGHTNESS_SETTINGS = get_brightness_settings()
    create_menu(INDICATOR)

    # Start DBus Service, listen for brightness up/down signals
    # dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    # DBusGMainLoop(set_as_default=True)
    # session_bus = dbus.SessionBus()
    # name = dbus.service.BusName("com.ubuntu.indicator.brightness", session_bus)
    # object_ = DBusOappindicator.Indicatorbject(session_bus, "/adjust")

    gtk.main()
