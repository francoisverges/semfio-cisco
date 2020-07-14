import argparse
import sys
import json
import serial
import time
from time import sleep


def send_to_console(ser: serial.Serial, command: str, wait_time: float = 0.4):
    command_to_send = command + "\r"
    ser.write(command_to_send.encode('utf-8'))
    sleep(wait_time)
    print(ser.read(ser.inWaiting()).decode('utf-8'), end="")


def configure_APoS(configs: dict):
    with serial.Serial('/dev/tty.AirConsole-68-raw-serial', timeout=1) as ser:
        print(f"Connecting to {ser.name}...")

        # Initial Connection
        ser.write(b'\r')
        ser.write(b'end\r')
        sleep(0.5)
        send_to_console(ser, "", wait_time=1)

        # Move to the enable mode
        send_to_console(ser, "enable")

        # Rename AP based on MAC address
        ap_mac = configs['ap']['mac']
        ap_mac_formatted = '.'.join(ap_mac[i:i+4] for i in range(0, len(ap_mac), 4))
        ap_default_name = "AP" + ap_mac_formatted
        command = f"ap name {ap_default_name} name {configs['ap']['name']}"
        send_to_console(ser, command)

        # Moving to the configuration mode
        send_to_console(ser, "conf t")

        # Synchronize logging on the console Connection
        send_to_console(ser, "line console 0")
        send_to_console(ser, "logging sync")
        send_to_console(ser, "exit")

        # Configure the EWC name
        command = f"hostname {configs['ewc']['name']}"
        send_to_console(ser, command)

        # Configure the static IP address of the controller
        send_to_console(ser, "interface gigabitEthernet 0")
        command = f"ip address {configs['ewc']['ip']} 255.255.255.0\r"
        send_to_console(ser, f"ip address {configs['ewc']['ip']} 255.255.255.0")

        # Create admin username and password
        command = f"username {configs['ewc']['username']} privilege 15 password {configs['ewc']['password']}"
        send_to_console(ser, command, wait_time=1)

        # Configure the AP profile
        send_to_console(ser, "ap profile default-ap-profile")
        command = f"mgmtuser username {configs['ewc']['username']} password 0 {configs['ewc']['password']} secret 0 {configs['ewc']['password']}"
        send_to_console(ser, command, wait_time=1)

        # Configure the WLANs
        i = 1
        for wlan in configs['wlans']:
            send_to_console(ser, f"wlan {wlan['name']} {i} \"{wlan['ssid']}\"")
            send_to_console(ser, "no security wpa akm dot1x")
            send_to_console(ser, f"security wpa psk set-key ascii 0 {wlan['psk']}")
            send_to_console(ser, "security wpa akm psk")
            send_to_console(ser, "no shutdown")
            send_to_console(ser, "exit")
            i += 1

        # Configure the Wireless Profile Policy
        for wlan in configs['wlans']:
            send_to_console(ser, f"wireless profile policy {wlan['name']}")
            send_to_console(ser, "no central association")
            send_to_console(ser, "no central dhcp")
            send_to_console(ser, "no central switching")
            send_to_console(ser, "http-tlv-caching")
            send_to_console(ser, "session-timeout 86400")
            send_to_console(ser, "no shutdown")
            send_to_console(ser, "exit")

        # Configure the Default Policy Tag
        send_to_console(ser, "wireless tag policy default-policy-tag")
        for wlan in configs['wlans']:
            send_to_console(ser, f"wlan {wlan['name']} policy {wlan['name']}")
        send_to_console(ser, "exit")

        # Configure Global Encryption
        send_to_console(ser, "service password-encryption")
        send_to_console(ser, "password encryption aes")
        send_to_console(ser, f"key config-key newpass {configs['ewc']['password']}")
        send_to_console(ser, "end")

        # Wait for the AP to join the controller again
        print("\rWaiting for the AP to join the controller (it takes about 1min)", end="")
        sleep(1)
        for i in range(0, 10):
            sys.stdout.write(".")
            sys.stdout.flush()
            sleep(1)
        print("\r")

        # Configure AP Radio Settings
        if configs['ap']['fra_ap'] == "true":
            command_channel = f"ap name {configs['ap']['name']} dot11 dual-band channel {configs['ap']['band_fra']['channel']}"
            command_txpower = f"ap name {configs['ap']['name']} dot11 dual-band txpower {configs['ap']['band_fra']['tx-power']}"
        else:
            command_channel = f"ap name {configs['ap']['name']} dot11 24ghz channel {configs['ap']['band_24']['channel']}"
            command_txpower = f"ap name {configs['ap']['name']} dot11 24ghz txpower {configs['ap']['band_24']['tx-power']}"
        send_to_console(ser, command_channel)
        send_to_console(ser, command_txpower)
        command = f"ap name Survey-AP dot11 5ghz channel {configs['ap']['band_5']['channel']}"
        send_to_console(ser, command)
        command = f"ap name Survey-AP dot11 5ghz txpower {configs['ap']['band_5']['tx-power']}"
        send_to_console(ser, command)

        # Configure the static IP address of the AP
        command = f"ap name {configs['ap']['name']} static-ip ip-address {configs['ap']['ip']} netmask {configs['ap']['netmask']} gateway {configs['ap']['gateway']}\r"
        send_to_console(ser, command)

        # Save Configurations
        send_to_console(ser, "write memory")


def main():
    parser = argparse.ArgumentParser(description='Configures a Mist AP for an APoS site survey')
    parser.add_argument('config', metavar='config_file', type=argparse.FileType(
        'r'), help='file containing all the configuration information')
    args = parser.parse_args()
    configs = json.load(args.config)
    configure_APoS(configs)


if __name__ == '__main__':
    start_time = time.time()
    print('** Setting up APoS AP')
    main()
    run_time = time.time() - start_time
    print("\n** Time to run: %s sec" % round(run_time, 2))
