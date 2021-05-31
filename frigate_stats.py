#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import requests
import urllib3

urllib3.disable_warnings()

SECONDS_PER_BLOCK = (24 * 3600) / 4608


def str_escape(string):
    if string is None:
        return ""
    ret = string.replace(" ", "\\ ")
    ret = ret.replace(",", "\\,")
    #    ret = ret.replace(".", "\\.")
    ret = '"{}"'.format(ret)
    return ret


def float_convert(f):
    if f == "null" or f is None:
        return 0.0
    return float(f)


class FrigateEndpoint():
    def __init__(self, api):
        self.api = api
        self.data = self.get_data()
        self.version = str(self.data['service']['version'])
        self.camera_names = self._get_camera_names()

    def _get_camera_names(self):
        frigate_default = ['detection_fps', 'detectors', 'service']
        camera_names = [
            x for x in self.data.keys() if x not in frigate_default
        ]
        return camera_names

    def get_data(self):
        url = f"{self.api}"
        r = requests.get(url)
        return r.json()

    def print_stats(self):
        global_tags = {'version': self.version}
        camera_tags = ['capture_pid', 'pid']
        camera_values = [
            'camera_fps', 'detection_fps', 'process_fps', 'skipped_fps'
        ]
        detector_tags = ['pid', 'detection_start']
        detector_values = ['inference_speed']
        storage_tags = ['mount_type']
        storage_values = ['free', 'total', 'used']
        for camera_name in self.camera_names:
            if camera_name in self.data:
                camera = self.data[camera_name]
                tags = ",".join([
                    f"{k}={v}" for k, v in camera.items() if k in camera_tags
                ])
                if len(global_tags) > 0:
                    tags += ","
                    tags += ",".join(
                        [f"{k}={v}" for k, v in global_tags.items()])
                tags += f",name={camera_name}"
                values = ",".join([
                    f"{k}={float(v)}" for k, v in camera.items()
                    if k in camera_values
                ])
                print("frigate_cameras,{} {}".format(tags, values))
        for detector_name, detector in self.data['detectors'].items():
            tags = ",".join([
                f"{k}={v}" for k, v in detector.items() if k in detector_tags
            ])
            if len(global_tags) > 0:
                tags += ","
                tags += ",".join([f"{k}={v}" for k, v in global_tags.items()])
            tags += f",name={detector_name}"
            values = ",".join([
                f"{k}={float(v)}" for k, v in detector.items()
                if k in detector_values
            ])
            print("frigate_detectors,{} {}".format(tags, values))
        for storage_name, storage in self.data['service']['storage'].items():
            tags = ",".join(
                [f"{k}={v}" for k, v in storage.items() if k in storage_tags])
            if len(global_tags) > 0:
                tags += ","
                tags += ",".join([f"{k}={v}" for k, v in global_tags.items()])
            tags += f",name={storage_name}"
            values = ",".join([
                f"{k}={float(v)}" for k, v in storage.items()
                if k in storage_values
            ])
            print("frigate_storage,{} {}".format(tags, values))


def main():
    parser = argparse.ArgumentParser(
        description="Frigate stats exporter for telegraf")
    parser.add_argument('--api', help="Frigate api address")
    args = parser.parse_args()
    e = FrigateEndpoint(api=args.api)
    e.print_stats()


if __name__ == "__main__":
    main()
