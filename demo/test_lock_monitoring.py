"""
Created on Sep 27, 2016

@author: lau
"""

# import gobject
import gtk
import dbus
from dbus.mainloop.glib import DBusGMainLoop

def filter_cb(bus, message):
    if message.get_member() != "EventEmitted":
        return
    args = message.get_args_list()
    if args[0] == "desktop-lock":
        print("Lock Screen")
    elif args[0] == "desktop-unlock":
        print("Unlock Screen")

DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
bus.add_match_string("type='signal',interface='com.ubuntu.Upstart0_6'")
bus.add_message_filter(filter_cb)
gtk.main()
# mainloop.run()
