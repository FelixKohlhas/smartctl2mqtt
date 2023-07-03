#!/usr/bin/python

import argparse
import subprocess
import json
import paho.mqtt.client as mqtt

# Command-line argument parsing
parser = argparse.ArgumentParser(
    prog='smartctl2mqtt',
    description='Send smartctl data to MQTT'
)

# Add command-line arguments
parser.add_argument('-b', '--broker', default="localhost", help='MQTT broker address')
parser.add_argument('-p', '--port', default="1883", help='MQTT broker port')
parser.add_argument('-c', '--client-id', default="smartctl2mqtt", help='MQTT client ID')
parser.add_argument('-t', '--topic-prefix', default="smartctl2mqtt/", help='MQTT topic prefix')
parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

args = parser.parse_args()

def log_error(error, command, result):
    print("ERROR:", error)
    print("CMD:", ' '.join(command))
    if result.stdout:
        print(result.stdout.decode("utf-8"))
    if result.stderr:
        print(result.stderr.decode("utf-8"))

# MQTT client setup
client = mqtt.Client(args.client_id)
client.connect(args.broker, int(args.port))

# Run 'lsblk' command to get disk information
lsblk_command = ['lsblk', '--output', 'PATH,MODEL,SERIAL,SIZE,FSUSE%', '--json', '--tree']
result = subprocess.run(lsblk_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Check if 'lsblk' command succeeded
if result.returncode != 0:
    log_error("lsblk failed", lsblk_command, result)
    exit(1)

# Parse 'lsblk' output as JSON
result_json = json.loads(result.stdout)
disks = result_json.get('blockdevices')

# Process each disk
for disk in disks:
    topic = disk.get('serial')
    path = disk.get('path')

    # Run 'smartctl' command to get SMART data for the disk
    smartctl_command = ['sudo', '/usr/sbin/smartctl', '--info', '--all', '--json', '--nocheck', 'standby', path]
    result = subprocess.run(smartctl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Check if 'smartctl' command succeeded
    if result.returncode not in [0, 2]:
        log_error("smartctl failed", smartctl_command, result)
        continue

    # Parse 'smartctl' output as JSON
    result_json = json.loads(result.stdout)

    # Prepare data to be published
    data = {
        'state': 'unknown',
        'path': disk.get('path'),
        'model': disk.get('model'),
        'serial': disk.get('serial'),
        'size': disk.get('size'),
    }

    # Process partitions and their usage percentage
    for i, c in enumerate(disk.get('children')):
        usage_percentage = c.get('fsuse%')
        if usage_percentage:
            data['partition_%02d' % i] = int(usage_percentage.split('%')[0])

    # Update data based on 'smartctl' results
    smartctl_exit_status = result_json['smartctl']['exit_status']
    if smartctl_exit_status == 0:
        data['state'] = 'active'
        data['power_on_time'] = result_json.get('power_on_time', {}).get('hours')
        data['power_cycle_count'] = result_json.get('power_cycle_count')
        data['temperature'] = result_json.get('temperature', {}).get('current')

    if smartctl_exit_status == 2:
        try:
            msg = result_json['smartctl']['messages'][0]['string']
        except:
            msg = None

        if msg and 'STANDBY' in msg:
            data['state'] = 'standby'
        else:
            print("ERROR: unknown message")
            print("DISK:", path)
            print(msg)

    # Print verbose output if enabled
    if args.verbose:
        print("TOPIC:", "%s%s" % (args.topic_prefix, topic))
        print("DATA:", json.dumps(data))

    # Publish data to MQTT topic
    client.publish("%s%s" % (args.topic_prefix, topic), json.dumps(data))
