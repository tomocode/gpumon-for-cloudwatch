FROM docker.io/nvidia/cuda:12.1.0-runtime-ubuntu22.04

RUN apt-get -qq update && \
    apt-get install -qq -y software-properties-common curl git && \
    apt-get install -qq -y python3.10 python3-pip && \
    ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    python -m pip install --no-cache-dir boto3 nvidia-ml-py3 requests

COPY gpumon.py gpumon.py

ENV interval=10
ENV log_path=/tmp/gpumon_stats
ENV resolution=60
ENV namespace=GPU/Container

CMD  ["/bin/sh", "-c", "python gpumon.py -i ${interval} -l ${log_path} -r ${resolution} -n ${namespace}"]
