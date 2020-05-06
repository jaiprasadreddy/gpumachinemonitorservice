
import json
import os
import socket
import time
from datetime import datetime
from time import sleep

import numpy as np
import requests
from pynvml import *

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
###CHOOSE NAMESPACE PARMETERS HERE###
my_NameSpace = "DeepLearningMonitor"

### CHOOSE PUSH INTERVAL ####
sleep_interval = 30
webhook_url="https://hooks.slack.com/services/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"
WaitTimeIdeal = 20  # in minutes
Gaptime = 10  # in minutes
### CHOOSE STORAGE RESOLUTION (BETWEEN 1-60) ####
store_reso = 60

# Instance information

TIMESTAMP = datetime.now().strftime("%Y-%m-%dT%H")
TMP_FILE = "/tmp/GPU_TEMP"
TMP_FILE_SAVED = TMP_FILE + TIMESTAMP


def getPowerDraw(handle):
    try:
        powDraw = nvmlDeviceGetPowerUsage(handle) / 1000.0
        powDrawStr = "%.2f" % powDraw
    except NVMLError as err:
        powDrawStr = handleError(err)
    return powDrawStr


def getTemp(handle):
    try:
        temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
    except NVMLError as err:
        temp = handleError(err)
        PUSH_TO_CW = False
    return temp


def getUtilization(handle):
    try:
        util = nvmlDeviceGetUtilizationRates(handle)
        gpu_util = str(util.gpu)
        mem_util = str(util.memory)
    except NVMLError as err:
        error = handleError(err)
        gpu_util = error
        mem_util = error
    return util, gpu_util, mem_util


nvmlInit()
deviceCount = nvmlDeviceGetCount()

def gpu_details(deviceCount):
    cnt = []
    for i in range(deviceCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        util, gpu_util, mem_util = getUtilization(handle)
        cnt.append(int(util.memory))
    return cnt

def main():
    try:
        start = time.time()
        while True:
            cnt = gpu_details(deviceCount)
            if np.sum(np.array(cnt) > 40):
                start = time.time()
                print("more usage")
            else:
                idealtime = time.time() - start
                if idealtime > WaitTimeIdeal * 60.0:
                    send_slack_msg(
                        slack_data=
                            "Machine IP: {0} , GPU utilization : {1}% from past 20min is less than 40%, machine will shutdown after {2} minutes".format(
                                IPAddr, np.max(cnt),Gaptime
                            )
                        , webhook_url = webhook_url
                    )
                    sleep(Gaptime * 60)
                    cnt = gpu_details(deviceCount)
                    if np.sum(np.array(cnt) > 40):
                        start = time.time()
                    else:
                        text = "GPU Machine Stopped: {}".format(IPAddr)
                        send_slack_msg(text,webhook_url)
                        os.system("sudo shutdown now")
        sleep(sleep_interval)
    except Exception as e:
        raise(e)
def send_slack_msg(slack_data, webhook_url):
    print(slack_data)
    response = requests.post(webhook_url, data=json.dumps({"text":slack_data}), headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    text = "GPU Machine Started: {}".format(IPAddr)
    send_slack_msg(text,webhook_url)
    main()
