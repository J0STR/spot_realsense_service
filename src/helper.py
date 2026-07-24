from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.api import image_pb2
from bosdyn.api import image_service_pb2_grpc
from bosdyn.client.image_service_helpers import (VisualImageSource, CameraBaseImageServicer)

from src.realsense import RealSenseD405

    
def make_webcam_image_service(bosdyn_sdk_robot, service_name, logger=None):
    image_sources = []
    web_cam = RealSenseD405()
    img_src = VisualImageSource(web_cam.image_source_name, web_cam, rows=web_cam.rows,
                                cols=web_cam.cols,
                                pixel_formats=[image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8,
                                                image_pb2.Image.PIXEL_FORMAT_RGB_U8])
    image_sources.append(img_src)
    return CameraBaseImageServicer(bosdyn_sdk_robot, service_name, image_sources, logger)

def run_service(bosdyn_sdk_robot, port, service_name, logger=None):
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server
    service_servicer = make_webcam_image_service(bosdyn_sdk_robot,
                                                 service_name,
                                                 logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)

def add_web_cam_arguments(parser):
    parser.add_argument(
        '--device-name',
        help=('Image source to query. If none are passed, it will default to the first available '
              'source.'), nargs='*', default=['0'])