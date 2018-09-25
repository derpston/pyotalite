import ubinascii
import machine

def get_machine_id():
    return ubinascii.hexlify(machine.unique_id()).decode("ascii")
