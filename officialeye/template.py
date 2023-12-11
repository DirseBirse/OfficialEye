import os

import click
# noinspection PyPackageRequirements
import cv2
import numpy as np

from officialeye.cli_utils import export_and_show_image
from officialeye.feature import TemplateFeature
from officialeye.keypoint import TemplateKeypoint
from officialeye.matcher import Matcher


class Template:
    def __init__(self, yaml_dict: dict, path_to_template: str, /):
        self._path_to_template = path_to_template
        self.name = yaml_dict["name"]
        self._source = yaml_dict["source"]
        self.height, self.width, _ = self.load_source_image().shape
        self._keypoints = [
            TemplateKeypoint(f, self) for f in yaml_dict["keypoints"]
        ]
        self._features = [
            TemplateFeature(f, self) for f in yaml_dict["features"]
        ]

    def _get_source_image_path(self) -> str:
        path_to_template_dir = os.path.dirname(self._path_to_template)
        path = os.path.join(path_to_template_dir, self._source)
        return os.path.normpath(path)

    def load_source_image(self):
        return cv2.imread(self._get_source_image_path(), cv2.IMREAD_COLOR)

    def _show(self, img):
        for feature in self._features:
            img = feature.draw(img)
        for keypoint in self._keypoints:
            img = keypoint.draw(img)
        return img

    def show(self):
        img = self.load_source_image()
        img = self._show(img)
        export_and_show_image(img)

    def _generate_keypoint_visualization(self):
        kp_vis = np.full((self.height, self.width), 0xff, dtype=np.uint8)

        for kp in self._keypoints:
            kp_img = kp.to_image()
            kp_vis[kp.y:kp.y+kp.h, kp.x:kp.x+kp.w] = kp_img

        return kp_vis

    def generate_keypoint_visualization(self, /):
        mp = self._generate_keypoint_visualization()
        export_and_show_image(mp)

    def apply(self, target, /):
        # find all patterns in the target image
        # img = target.copy()

        with click.progressbar(length=len(self._keypoints) + 2, label="Matching") as bar:

            matcher = Matcher(target, debug_mode=True)  # TODO: debug handling

            bar.update(1)

            for i, kp in enumerate(self._keypoints):
                matcher.add_keypoint(kp)
                bar.update(2 + i)

            matcher.match()

        # output_path = "debug.png"
        # cv2.imwrite(output_path, img)
        # click.secho(f"Pattern-matching success. Exported '{output_path}'.", bg="green", bold=True)

        # homography = cv2.getPerspectiveTransform(np.float32(source_points), np.float32(destination_points))
        # target_transformed = cv2.warpPerspective(target, np.float32(homography), (self.width, self.height),
        # flags=cv2.INTER_LINEAR)
        # target_transformed = self._show(target_transformed)

        # output_path = "transformed.png"
        # cv2.imwrite(output_path, target_transformed)
        # click.secho(f"Success. Exported '{output_path}'.", bg="green", bold=True)

    def __str__(self):
        return f"{self.name} ({self._source}, {len(self._features)} features)"
