"""collect gpu metrics and put those metrics into log file and cloudwatch

usage:

python gpumon.py -i {time interval sec} -l {path to log} -r {resolution} --n {namespace}

"""

import requests
import boto3
import argparse
import os

from pynvml import (nvmlInit, nvmlDeviceGetCount, nvmlShutdown,
                    nvmlDeviceGetHandleByIndex, nvmlDeviceGetPowerUsage,
                    nvmlDeviceGetTemperature, NVML_TEMPERATURE_GPU,
                    nvmlDeviceGetUtilizationRates, NVMLError)
from datetime import datetime
from time import sleep

parser = argparse.ArgumentParser()
parser.add_argument(
    '-i',
    '--interval',
    dest='interval',
    default=10,
    type=int,
    help='sleep interval (times between collecting each metrics)')
parser.add_argument(
    '-l',
    '--log-path',
    dest='log_path',
    default='/tmp/gpumon_stats',
    type=str,
    help='path of gpumon logs (/tmp/stat will be /tmp/stats-2019-01-01T20)')
parser.add_argument('-r',
                    '--resolution',
                    dest='resolution',
                    default=60,
                    type=int,
                    help='resolution of storage in cloudwatch')
parser.add_argument('-n',
                    '--namespace',
                    dest='namespace',
                    default='DeepLearning',
                    type=str,
                    help='namespace of cloudwatch (default: DeepLearning)')

_ecs_metadata_cache = None


def _get_ecs_metadata():
    """Get ECS task metadata from ECS container metadata endpoint
    """
    global _ecs_metadata_cache
    if _ecs_metadata_cache is not None:
        return _ecs_metadata_cache

    try:
        # ECS container metadata endpoint v4
        ECS_METADATA_URI = os.environ.get('ECS_CONTAINER_METADATA_URI_V4')
        if ECS_METADATA_URI:
            response = requests.get(ECS_METADATA_URI + '/task')
            metadata = response.json()

            _ecs_metadata_cache = {
                'cluster': metadata.get('Cluster', 'unknown'),
                'service': metadata.get('ServiceName', 'unknown'),
                'availability_zone': metadata.get('AvailabilityZone', 'unknown')
            }
            return _ecs_metadata_cache
    except Exception as e:
        print(f"Failed to get ECS metadata: {e}")
        _ecs_metadata_cache = {}
    return _ecs_metadata_cache


def _get_cloudwatch_meta():
    """Get CloudWatch dimensions for ECS service level metrics
    """
    ecs_meta = _get_ecs_metadata()

    return [{
        'Name': 'Cluster',
        'Value': ecs_meta.get('cluster', 'unknown')
    }, {
        'Name': 'Service',
        'Value': ecs_meta.get('service', 'unknown')
    }]


def _format_metric(name, value, resolution, dimension, unit='None'):
    return {
        'MetricName': name,
        'Dimensions': dimension,
        'Unit': unit,
        'StorageResolution': resolution,
        'Value': value
    }


def _put_log(string, file_path):
    with open(file_path, 'a+') as f:
        f.write(string)


def get_gpu_power(handle):
    """get device power usage
    """

    return nvmlDeviceGetPowerUsage(handle) / 1000.0


def get_gpu_temperature(handle):
    """get current temperature of gpu
    """

    return nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)


def get_gpu_utilization(handle):
    """return utilization of gpu (including memory utilization)
    """

    return nvmlDeviceGetUtilizationRates(handle)


def put_metrics_to_log_file(gpu_num, power, temp, utilization, log_path):
    """put metric line into log file
    """
    try:
        _put_log(
            "gpu %d, gpu util: %s, mem util: %s, power usage: %s, temp: %s\n" %
            (gpu_num, utilization.gpu, utilization.memory, power, temp),
            log_path)
    except Exception as e:
        print("Cannot print to %s, %s" % (log_path, e))


def put_metrics_to_cloudwatch(power, temp, utilization, resolution,
                              cloudwatch, namespace):
    """Update CloudWatch metrics with ECS context"""
    dimension = _get_cloudwatch_meta()

    cloudwatch.put_metric_data(MetricData=[
        _format_metric('GPU Usage', utilization.gpu, resolution, dimension,
                       'Percent'),
        _format_metric('Memory Usage', utilization.memory, resolution,
                       dimension, 'Percent'),
        _format_metric('Power Usage (Watts)', power, resolution, dimension),
        _format_metric('Temperature (C)', temp, resolution, dimension),
    ],
        Namespace=namespace)


def main():
    args = parser.parse_args()

    nvmlInit()

    num_device = list(range(nvmlDeviceGetCount()))
    log_path = args.log_path + datetime.now().strftime('%Y-%m-%dT%H')

    # インスタンスメタデータの取得を簡略化
    region = _get_ecs_metadata().get('availability_zone', 'unknown')[:-1]
    cloudwatch = boto3.client('cloudwatch', region_name=region)

    try:
        while True:
            for gpu_num in num_device:
                put_metric = True
                handle = nvmlDeviceGetHandleByIndex(gpu_num)

                try:
                    power = get_gpu_power(handle)
                    temp = get_gpu_temperature(handle)
                    utilization = get_gpu_utilization(handle)
                except NVMLError as error:
                    _put_log("cannot collect metrics %s" % error, log_path)
                    put_metric = False

                if put_metric:
                    put_metrics_to_log_file(gpu_num, power, temp, utilization,
                                            log_path)
                    put_metrics_to_cloudwatch(power=power,
                                              temp=temp,
                                              utilization=utilization,
                                              resolution=args.resolution,
                                              cloudwatch=cloudwatch,
                                              namespace=args.namespace)

            sleep(args.interval)
    finally:
        nvmlShutdown()


if __name__ == "__main__":
    main()
