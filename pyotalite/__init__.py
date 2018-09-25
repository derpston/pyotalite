import sys
import network
import time
import machine
import os

import pyotalite.config
import pyotalite.ota

def wifi_setup():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    print("Connecting to %s..." % (config.ssid))
    sta_if.connect(config.ssid, config.key)
    while not sta_if.isconnected():
        time.sleep(0.1)
    print("Connected: %s" % (str(sta_if.ifconfig())))
    
    ifconfig = sta_if.ifconfig()
    
    # Replace local DNS server with Google's because some routers don't respond to our DNS requests...
    sta_if.ifconfig((ifconfig[0], ifconfig[1], ifconfig[2], "8.8.8.8"))
    print("Updated: %s" % (str(sta_if.ifconfig())))
 

def main():
    wifi_setup()

    try:
        ota.do_update()
    except Exception as ex:
        print("OTA failed: %s: %s" % (ex.__class__.__name__, ex))
        sys.print_exception(ex)
    
    current_version = ota.get_current_version()
    
    print("Attempting to start version %s" % current_version)
    
    crash_count = 0
    
    while True:
        try:
            os.chdir("/versions")
            sys.path.append("/versions/%s" % current_version)
            exec("import %s" % current_version)
            exec("%s.main()" % current_version)
            print("Version %s exited. Probably wasn't supposed to do that." % current_version)
        except Exception as ex:
            # TODO catch this and try to do something else!
            # Report the failure? Reboot?
            # Keep a list of versions and failures, and try to switch to the next-oldest one that worked?
            sys.print_exception(ex)
       
        crash_count += 1
        print("Crashed %d times." % crash_count)
        if crash_count > 10:
            print("Crashed too many times, rebooting.")
            machine.reset()
    
        time.sleep(1)
        os.chdir("/")
    
    print("Halted.")
    while True:
        pass
