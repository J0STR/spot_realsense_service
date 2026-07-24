import time
import cv2
import numpy as np
import pyrealsense2 as rs
from numpy.typing import NDArray
from typing import Any

from bosdyn.api import image_pb2
from bosdyn.client.image_service_helpers import (CameraInterface, convert_RGB_to_grayscale)


class RealSenseD405(CameraInterface):
    """Provide access to the latest web cam data using openCV's VideoCapture."""

    def __init__(self, serial_number: str = "409122274688"):
        self.serial_number = serial_number
        self.width = 640
        self.height = 480
        self.fps = 30
        self.use_depth = False
        self.warmup_s = 1
        self.color_mode = "bgr"

        # needed from API:
        self.image_source_name = "D405_gripper"
        self.rows = int(self.height)
        self.cols = int(self.width)
        self.camera_exposure = None
        self.camera_gain = None

        self.latest_color_frame: NDArray[Any] | None = None
        self.latest_depth_frame: NDArray[Any] | None = None
        self.latest_timestamp: float | None = None
        
        self.rs_pipeline = rs.pipeline()
        self.rs_config = rs.config()
        self._configure_rs_pipeline_config()
        self.rs_profile = self.rs_pipeline.start(self.rs_config)
        

        start_time = time.time()
        while time.time() - start_time < self.warmup_s:
            time.sleep(0.1)
        print("cam connected")
        self.default_jpeg_quality = 75

    def blocking_capture(self):
        try:
            frame = self._read_from_hardware()
            color_frame_raw = frame.get_color_frame()
            color_frame = np.asanyarray(color_frame_raw.get_data())
            processed_color_frame = self._postprocess_image(color_frame)

            if self.use_depth:
                depth_frame_raw = frame.get_depth_frame()
                depth_frame = np.asanyarray(depth_frame_raw.get_data())
                processed_depth_frame = self._postprocess_image(depth_frame, depth_frame=True)

            capture_time = time.time()

            
            self.latest_color_frame = processed_color_frame
            if self.use_depth:
                self.latest_depth_frame = processed_depth_frame
            self.latest_timestamp = capture_time

        except Exception as e:
            raise RuntimeError(f"{self} exceeded maximum consecutive read failures.") from e

        return processed_color_frame, capture_time
        
        
    def image_decode(self, image_data, image_proto, image_req):
        pixel_format = image_req.pixel_format
        converted_image_data = image_data
        if pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
            converted_image_data = convert_RGB_to_grayscale(
                cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))

        if pixel_format == image_pb2.Image.PIXEL_FORMAT_UNKNOWN:
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8
        else:
            image_proto.pixel_format = pixel_format

        resize_ratio = image_req.resize_ratio
        quality_percent = image_req.quality_percent
        if resize_ratio < 0 or resize_ratio > 1:
            raise ValueError("Resize ratio %s is out of bounds." % resize_ratio)

        if resize_ratio != 1.0 and resize_ratio != 0:
            image_proto.rows = int(image_proto.rows * resize_ratio)
            image_proto.cols = int(image_proto.cols * resize_ratio)
            converted_image_data = cv2.resize(converted_image_data, (image_proto.cols, image_proto.rows), interpolation = cv2.INTER_AREA)
        
        # Set the image data.
        image_format = image_req.image_format
        if image_format == image_pb2.Image.FORMAT_RAW:
            image_proto.data = np.ndarray.tobytes(converted_image_data)
            image_proto.format = image_pb2.Image.FORMAT_RAW

        elif image_format == image_pb2.Image.FORMAT_JPEG or image_format == image_pb2.Image.FORMAT_UNKNOWN or image_format is None:
            quality = self.default_jpeg_quality
            if 0 < quality_percent <= 100:
                quality = quality_percent
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
            image_proto.data = cv2.imencode('.jpg', converted_image_data, encode_param)[1].tobytes()
            image_proto.format = image_pb2.Image.FORMAT_JPEG
        else:
            raise Exception(
            "Image format %s is unsupported." % image_pb2.Image.Format.Name(image_format))
        
    def _configure_rs_pipeline_config(self) -> None:
        """Creates and configures the RealSense pipeline configuration object."""
        rs.config.enable_device(self.rs_config, self.serial_number)

        if self.width and self.height and self.fps:
            self.rs_config.enable_stream(
                rs.stream.color, self.width, self.height, rs.format.rgb8, self.fps
            )
            if self.use_depth:
                self.rs_config.enable_stream(
                    rs.stream.depth, self.capture_width, self.capture_height, rs.format.z16, self.fps
                )
        else:
            self.rs_config.enable_stream(rs.stream.color)
            if self.use_depth:
                self.rs_config.enable_stream(rs.stream.depth)
        
    def _read_from_hardware(self):
        if self.rs_pipeline is None:
            raise RuntimeError(f"{self}: rs_pipeline must be initialized before use.")

        ret, frame = self.rs_pipeline.try_wait_for_frames(timeout_ms=10000)

        if not ret or frame is None:
            raise RuntimeError(f"{self} read failed (status={ret}).")

        return frame
    
    def _postprocess_image(self, image: NDArray[Any], depth_frame: bool = False) -> NDArray[Any]:
        if depth_frame:
            h, w = image.shape
        else:
            h, w, c = image.shape

            if c != 3:
                raise RuntimeError(f"{self} frame channels={c} do not match expected 3 channels (RGB/BGR).")

        if h != self.height or w != self.width:
            raise RuntimeError(
                f"{self} frame width={w} or height={h} do not match configured width={self.width} or height={self.height}."
            )

        processed_image = image
        if self.color_mode == "bgr":
            processed_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # if self.rotation in [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_180]:
        #     processed_image = cv2.rotate(processed_image, self.rotation)

        return processed_image
        