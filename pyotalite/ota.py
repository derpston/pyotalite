import pyotalite.config as config
import pyotalite.util as util
import pyotalite.shittytar as shittytar
import pyotalite.urequests as requests

import uzlib
import os
import uhashlib
import ubinascii

# Strip trailing slashes from the base URL in the config, because
# MicroPython doesn't have os.path.join, which would avoid this.
 
config.update_base = config.update_base.strip("/")

def check_for_update():
    """Returns True if a different version is available."""
    current = get_current_version()
    offered = get_offered_version()
    print("Version check: %s vs %s" % (current, offered))
    return current != offered

def makedirs(path):
    """Make any directories necessary to make sure that `path` exists and is a directory."""
    basedir = ""
    for chunk in path.split("/"):
        basedir += "/" + chunk
        try:
            os.mkdir(basedir)
        except OSError as ex:
            pass

def do_update():
    current = get_current_version()
    version = get_ota_header()

    if version == None:
        print("OTA unavailable, no versions offered at all.")
        return True
    elif current == version:
        print("OTA unnecessary, current version matches available version.")
        return True

    print("OTA version mismatch.")
    
    # Download offered version
    # Verify signature
    # Extract new version

    update_url = "%s/%s" % (config.update_base, version)
    
    print("Fetching code: %s" % (update_url))
    response = requests.get(update_url)
    print("Got %d bytes" % len(response.content))
    if response.status_code in [200]:
        shittytar_content = response.content
        response.close()

        # Extract signature
        signature = ubinascii.hexlify(shittytar_content[:32]).decode("ascii")
        shittytar_content = shittytar_content[32:]

        # Verify signature
        h = uhashlib.sha256()
        h.update(shittytar_content)
        h.update(ubinascii.unhexlify(config.shared_secret))
        our_signature = ubinascii.hexlify(h.digest()).decode("ascii")
        
        print("Signatures: claimed=%s calculated=%s" % (signature, our_signature))
        if signature != our_signature:
            print("Signature verification FAILED! OTA aborted.")
            return False


        st = shittytar.ShittyTar(shittytar_content)

        # Verify integrity of the archive. Different from the signature
        # check above because a broken archive could have been signed and
        # distributed.
        st.verify()
        print("ShittyTar verification passed.")

        # TODO make new version directory. If it already exists, error out OR overwrite everything?
        try:
            os.mkdir("/versions/%s" % version)
        except OSError:
            # Probably already exists.
            pass

        for filename, content in st:
            # Write file to flash
            new_path = "/versions/%s/%s" % (version, filename) 
            print("Writing %s (%d bytes)" % (new_path, len(content)))

            # Make any necessary directories
            basedir = new_path[:new_path.rindex("/")]
            makedirs(basedir)

            fh = open(new_path, "w")
            fh.write(content)
            fh.close()

        # TODO update version.txt, OR delegate this responsibility to the new
        # code so we only reboot into the new code if it works.
        fh = open("/version.txt", "w")
        fh.write(version)
        fh.close()
    else:
        print("No update available, HTTP response %d" % (response.status_code))
 


def get_current_version():
    try:
        version = open("/version.txt").read()
    except OSError:
        version = None
    return version

def get_offered_version():
    version = get_ota_header()
    return version

def get_ota_header():
    machine_id = util.get_machine_id()

    manifest_url = "%s/%s.manifest" % (config.update_base, machine_id)

    print("Checking for an update: %s" % (manifest_url))
    response = requests.get(manifest_url)
    print("Got %d bytes" % len(response.content))
    if response.status_code in [200]:
        version = response.json()['version']
    else:
        print("No update available, HTTP response %d" % (response.status_code))
        version = None

    response.close()
    return version
