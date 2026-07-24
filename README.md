# Image Service for Realsense D405 for BD Spot

Docker Image to run on the **Core I/O** of a Boston Dynamics Spot to host a **service** for accessing a **Realsense D405 Camera**.



## Build

Build on the Core I/O:

1. Go to permanent Folder:
    ```bash
    cd /data/
    ```
2. Clone Repo (with sudo)
    ```bash
    sudo git clone https://github.com/J0STR/spot_realsense_service.git
    ```
3. Move to project folder
    ```bash
    cd spot_realsense_service/
    ```
4. Build:
    ```bash
    sudo docker build -t d405_service -f Dockerfile.l4t .
    ```
5. Launch:
    ```bash
    sudo docker run -it   --network=host   --privileged   -v /dev/bus/usb:/dev/bus/usb   -v /opt/payload_credentials:/opt/payload_credentials:ro   --entrypoint /bin/bash   d405_service
    ```



## Test

- [Guide](https://dev.bostondynamics.com/python/examples/tester_programs/readme#testing-an-image-service)
- Service name: 'realsense-service'
