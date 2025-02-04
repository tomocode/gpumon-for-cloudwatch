# gpumon-for-cloudwatch
docker image that collect metrics about gpu and put those metrics to the cloudwatch (aws)

## Usage

### Build docker image

```bash
docker buildx build --platform linux/x86_64 -t gpumon-for-cloudwatch:latest .
```

## Run docker container

```bash
docker run -d --name gpumon-for-cloudwatch --gpus all gpumon-for-cloudwatch:latest
```

