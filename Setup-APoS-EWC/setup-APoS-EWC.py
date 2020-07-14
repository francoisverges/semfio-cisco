import argparse
import json
import serial
import time
from time import sleep


def main():
    parser = argparse.ArgumentParser(description='Configures a Mist AP for an APoS site survey')
    parser.add_argument('config', metavar='config_file', type=argparse.FileType(
        'r'), help='file containing all the configuration information')
    args = parser.parse_args()
    configs = json.load(args.config)

    with serial.Serial('/dev/tty.AirConsole-68-raw-serial', timeout=1) as ser:
        print(f"Connecting to {ser.name}...")

        # Initial Connection
        ser.write(b'\r')
        # ser.write(b'end\r')
        # sleep(0.5)
        ser.write(b'\r')
        sleep(1)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Move to the enable mode
        ser.write(b'enable\r')
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Rename AP based on MAC address
        ap_mac = configs['ap']['mac']
        ap_mac_formatted = '.'.join(ap_mac[i:i+4] for i in range(0, len(ap_mac), 4))
        ap_default_name = "AP" + ap_mac_formatted
        command = f"ap name {ap_default_name} name {configs['ap']['name']}\r"
        ser.write(command.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Moving to the configuration mode
        ser.write(b'conf t\r')
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure the EWC name
        command = f"hostname {configs['ewc']['name']}\r"
        ser.write(command.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure the static IP address of the controller
        ser.write(b'interface gigabitEthernet 0\r')
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        command = f"ip address {configs['ewc']['ip']} 255.255.255.0\r"
        ser.write(command.encode('utf-8'))
        sleep(5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Create admin username and password
        command = f"username {configs['ewc']['username']} privilege 15 password {configs['ewc']['password']}\r"
        ser.write(command.encode('utf-8'))
        sleep(1)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure the AP profile
        ser.write(b"ap profile default-ap-profile\r")
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        command = f"mgmtuser username {configs['ewc']['username']} password 0 {configs['ewc']['password']} secret 0 {configs['ewc']['password']}\r"
        ser.write(command.encode('utf-8'))
        sleep(1)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure the WLANs
        i = 1
        for wlan in configs['wlans']:
            command = f"wlan {wlan['name']} {i} \"{wlan['ssid']}\"\r"
            ser.write(command.encode('utf-8'))
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"no security wpa akm dot1x\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            command = f"security wpa psk set-key ascii 0 {wlan['psk']}\r"
            ser.write(command.encode('utf-8'))
            sleep(0.5)
            ser.write(b"security wpa akm psk\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"no shutdown\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"exit\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            i += 1

        # Configure the Wireless Profile Policy
        for wlan in configs['wlans']:
            command = f"wireless profile policy {wlan['name']}\r"
            ser.write(command.encode('utf-8'))
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"no central association\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"no central dhcp\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"no central switching\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"http-tlv-caching\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"session-timeout 86400\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"no shutdown\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
            ser.write(b"exit\r")
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure the Default Policy Tag
        ser.write(b"wireless tag policy default-policy-tag\r")
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        for wlan in configs['wlans']:
            command = f"wlan {wlan['name']} policy {wlan['name']}\r"
            ser.write(command.encode('utf-8'))
            sleep(0.5)
            print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        ser.write(b"exit\r")
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure Global Encryption
        ser.write(b"service password-encryption\r")
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        ser.write(b"password encryption aes\r")
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        command = f"key config-key newpass {configs['ewc']['password']}\r"
        ser.write(command.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        ser.write(b"end\r")
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure AP Radio Settings
        if configs['ap']['fra_ap'] == "true":
            command_channel = f"ap name {configs['ap']['name']} dot11 dual-band channel {configs['ap']['band_fra']['channel']}\r"
            command_txpower = f"ap name {configs['ap']['name']} dot11 dual-band txpower {configs['ap']['band_fra']['tx-power']}"
        else:
            command_channel = f"ap name {configs['ap']['name']} dot11 24ghz channel {configs['ap']['band_24']['channel']}\r"
            command_txpower = f"ap name {configs['ap']['name']} dot11 24ghz txpower {configs['ap']['band_24']['tx-power']}"
        ser.write(command_channel.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        ser.write(command_txpower.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        command = f"ap name Survey-AP dot11 5ghz channel {configs['ap']['band_5']['channel']}\r"
        ser.write(command.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')
        command = f"ap name Survey-AP dot11 5ghz txpower {configs['ap']['band_5']['tx-power']}\r"
        ser.write(command.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Configure the static IP address of the AP
        command = f"ap name {configs['ap']['name']} static-ip ip-address {configs['ap']['ip']} netmask {configs['ap']['netmask']} gateway {configs['ap']['gateway']}\r"
        ser.write(command.encode('utf-8'))
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')

        # Save Configurations
        ser.write(b"write memory\r")
        sleep(0.5)
        print(ser.read(ser.inWaiting()).decode('utf-8'), end='')


if __name__ == '__main__':
    start_time = time.time()
    print('** Setting up APoS AP')
    main()
    run_time = time.time() - start_time
    print("\n** Time to run: %s sec" % round(run_time, 2))
