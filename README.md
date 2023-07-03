<div align="center">

# smartctl2mqtt

*Send smartctl data to MQTT.*

</div>

## Installation

#### Clone repository and install requirements

    git clone ...
    cd smartctl2mqtt
    pip3 install -r requirements.txt

#### Install smartmontools

    apt-get install smartmontools

## Run

    python3 run.py

## Usage

```
usage: smartctl2mqtt [-h] [-b BROKER] [-p PORT] [-c CLIENT_ID] [-t TOPIC_PREFIX] [-v]

Send smartctl data to MQTT

options:
  -h, --help            show this help message and exit
  -b BROKER, --broker BROKER
                        MQTT broker address
  -p PORT, --port PORT  MQTT broker port
  -c CLIENT_ID, --client-id CLIENT_ID
                        MQTT client ID
  -t TOPIC_PREFIX, --topic-prefix TOPIC_PREFIX
                        MQTT topic prefix
  -v, --verbose         Enable verbose output
```