from __future__ import annotations

import os
import random
from concurrent.futures import Future
from typing import Dict, List, TYPE_CHECKING, Iterable

import numpy as np

# noinspection PyProtectedMember
from officialeye._api.template.supervision_result import SupervisionResult
# noinspection PyProtectedMember
from officialeye._api.template.supervisor import ISupervisor
# noinspection PyProtectedMember
from officialeye._api.image import IImage
# noinspection PyProtectedMember
from officialeye._api.template.template import ITemplate
# noinspection PyProtectedMember
from officialeye._internal.feedback.verbosity import Verbosity
from officialeye._internal.context.singleton import get_internal_context, get_internal_afi
from officialeye._internal.template.image import InternalImage
from officialeye._internal.template.utils import load_mutator_from_dict
from officialeye._internal.timer import Timer
from officialeye.error.errors.general import ErrOperationNotSupported, ErrInvalidIdentifier
from officialeye.error.errors.supervision import ErrSupervisionCorrespondenceNotFound
from officialeye.error.errors.template import (
    ErrTemplateInvalidFeature,
    ErrTemplateInvalidKeypoint
)

from officialeye._internal.template.matching_result import InternalMatchingResult
from officialeye._internal.template.feature_class.loader import load_template_feature_classes
from officialeye._internal.template.feature_class.manager import FeatureClassManager
from officialeye._internal.template.feature import InternalFeature
from officialeye._internal.template.keypoint import InternalKeypoint
from officialeye._internal.template.template_data import TemplateData, TemplateDataFeature, TemplateDataKeypoint


if TYPE_CHECKING:
    from officialeye.types import ConfigDict
    # noinspection PyProtectedMember
    from officialeye._api.template.matcher import IMatcher
    # noinspection PyProtectedMember
    from officialeye._api.mutator import IMutator
    # noinspection PyProtectedMember
    from officialeye._api.analysis_result import AnalysisResult


_SUPERVISION_RESULT_FIRST = "first"
_SUPERVISION_RESULT_RANDOM = "random"
_SUPERVISION_RESULT_BEST_MSE = "best_mse"
_SUPERVISION_RESULT_BEST_SCORE = "best_score"


class InternalTemplate(ITemplate):

    def __init__(self, yaml_dict: Dict[str, any], path_to_template: str, /):
        super().__init__()

        self._path_to_template = path_to_template

        self._template_id = yaml_dict["id"]
        self._name = yaml_dict["name"]
        self._source = yaml_dict["source"]

        self._height, self._width, _ = self.get_image().load().shape

        self._source_mutators: List[IMutator] = [
            load_mutator_from_dict(mutator_dict) for mutator_dict in yaml_dict["mutators"]["source"]
        ]

        self._target_mutators: List[IMutator] = [
            load_mutator_from_dict(mutator_dict) for mutator_dict in yaml_dict["mutators"]["target"]
        ]

        self._keypoints: Dict[str, InternalKeypoint] = {}
        self._features: Dict[str, InternalFeature] = {}

        for keypoint_id in yaml_dict["keypoints"]:
            keypoint_dict = yaml_dict["keypoints"][keypoint_id]
            keypoint_dict["id"] = keypoint_id
            keypoint = InternalKeypoint(self.identifier, keypoint_dict)

            if keypoint.identifier in self._keypoints:
                raise ErrTemplateInvalidKeypoint(
                    f"while initializing keypoint '{keypoint_id}' of template '{self.identifier}'",
                    f"There is already a keypoint with the same identifier '{keypoint.identifier}'."
                )

            if keypoint.identifier in self._features:
                raise ErrTemplateInvalidKeypoint(
                    f"while initializing keypoint '{keypoint_id}' of template '{self.identifier}'",
                    f"There is already a feature with the same identifier '{keypoint.identifier}'."
                )

            self._keypoints[keypoint.identifier] = keypoint

        self._matching = yaml_dict["matching"]
        self._supervision = yaml_dict["supervision"]

        # load feature classes
        self._feature_class_manager = load_template_feature_classes(yaml_dict["feature_classes"], self.identifier)

        # load features
        for feature_id in yaml_dict["features"]:
            feature_dict = yaml_dict["features"][feature_id]
            feature_dict["id"] = feature_id
            feature = InternalFeature(self.identifier, feature_dict)

            if feature.identifier in self._keypoints:
                raise ErrTemplateInvalidFeature(
                    f"while initializing feature '{feature_id}' of template '{self.identifier}'",
                    f"There is already a keypoint with the same identifier '{feature.identifier}'."
                )

            if feature.identifier in self._features:
                raise ErrTemplateInvalidFeature(
                    f"while initializing feature '{feature_id}' of template '{self.identifier}'",
                    f"There is already a feature with the same identifier '{feature.identifier}'."
                )

            self._features[feature.identifier] = feature

        get_internal_context().add_template(self)

    def load(self):
        raise ErrOperationNotSupported(
            "when calling the load() method of an InternalTemplate instance.",
            "This method can only be called on a Template instance."
        )

    def analyze_async(self, /, *, target: IImage, interpretation_target: IImage | None = None) -> Future:
        raise ErrOperationNotSupported(
            "when calling the analyze_async() method of an InternalTemplate instance.",
            "This method can only be called on a Template instance."
        )

    def analyze(self, /, **kwargs) -> AnalysisResult:
        raise ErrOperationNotSupported(
            "when calling the analyze() method of an InternalTemplate instance.",
            "This method can only be called on a Template instance."
        )

    def _get_source_image_path(self) -> str:
        if os.path.isabs(self._source):
            return self._source
        path_to_template_dir = os.path.dirname(self._path_to_template)
        path = os.path.join(path_to_template_dir, self._source)
        return os.path.normpath(path)

    def get_image(self) -> IImage:
        return InternalImage(path=self._get_source_image_path())

    def get_mutated_image(self) -> IImage:
        img = self.get_image()
        img.apply_mutators(*self._source_mutators)
        return img

    @property
    def identifier(self) -> str:
        return self._template_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def keypoints(self) -> Iterable[InternalKeypoint]:
        for keypoint_id in self._keypoints:
            yield self._keypoints[keypoint_id]

    @property
    def features(self) -> Iterable[InternalFeature]:
        for feature_id in self._features:
            yield self._features[feature_id]

    def validate(self):
        for feature in self.features:
            feature.validate_feature_class()

    def get_template_data(self) -> TemplateData:
        return TemplateData(
            identifier=self.identifier,
            name=self.name,
            source=self._get_source_image_path(),
            width=self.width,
            height=self.height,
            features=[
                TemplateDataFeature(
                    identifier=f.identifier,
                    x=f.x,
                    y=f.y,
                    w=f.w,
                    h=f.h
                ) for f in self.features
            ],
            keypoints=[
                TemplateDataKeypoint(
                    identifier=k.identifier,
                    x=k.x,
                    y=k.y,
                    w=k.w,
                    h=k.h,
                    matches_min=k.matches_min,
                    matches_max=k.matches_max
                ) for k in self.keypoints
            ],
            source_mutators=self._source_mutators,
            target_mutators=self._target_mutators
        )

    def get_matcher(self, /) -> IMatcher:
        matcher_id = self._matching["engine"]
        matcher_config = self._matching["config"]
        return get_internal_context().get_matcher(matcher_id, matcher_config)

    def get_supervisor(self, /) -> ISupervisor:
        supervisor_id = self._supervision["engine"]
        supervisor_config_generic = self._supervision["config"]

        if supervisor_id in supervisor_config_generic:
            supervisor_config: ConfigDict = supervisor_config_generic[supervisor_id]
        else:
            get_internal_afi().warn(Verbosity.INFO, f"Could not find any configuration entries for the '{supervisor_id}' supervisor.")
            supervisor_config: ConfigDict = {}

        return get_internal_context().get_supervisor(supervisor_id, supervisor_config)

    def get_supervision_config(self) -> dict:
        return self._supervision["config"]

    def get_feature_classes(self) -> FeatureClassManager:
        return self._feature_class_manager

    def get_feature(self, feature_id: str, /) -> InternalFeature | None:

        if feature_id not in self._features:
            return None

        return self._features[feature_id]

    def get_keypoint(self, keypoint_id: str, /) -> InternalKeypoint | None:

        if keypoint_id not in self._keypoints:
            return None

        return self._keypoints[keypoint_id]

    def get_path(self) -> str:
        return self._path_to_template

    def _run_supervisor(self, keypoint_matching_result: InternalMatchingResult, /) -> SupervisionResult | None:

        supervisor = self.get_supervisor()
        supervisor.setup(self, keypoint_matching_result)

        supervision_result_choice_engine = self._supervision["result"]
        results: List[SupervisionResult] = list(supervisor.supervise(self, keypoint_matching_result))

        if len(results) == 0:
            return None

        if supervision_result_choice_engine == _SUPERVISION_RESULT_FIRST:
            return results[0]

        if supervision_result_choice_engine == _SUPERVISION_RESULT_RANDOM:
            return random.choice(results)

        if supervision_result_choice_engine == _SUPERVISION_RESULT_BEST_MSE:

            best_result = results[0]
            best_result_mse = best_result.get_weighted_mse()

            for result_id, result in enumerate(results):
                result_mse = result.get_weighted_mse()

                get_internal_afi().info(Verbosity.INFO_VERBOSE, f"Result #{result_id + 1} has MSE {result_mse}")

                if result_mse < best_result_mse:
                    best_result_mse = result_mse
                    best_result = result

            get_internal_afi().info(Verbosity.INFO_VERBOSE, f"Best result has MSE {best_result_mse}")

            return best_result

        if supervision_result_choice_engine == _SUPERVISION_RESULT_BEST_SCORE:

            best_result = results[0]
            best_result_score = best_result.get_score()

            for result_id, result in enumerate(results):
                result_score = result.get_score()

                get_internal_afi().info(Verbosity.INFO_VERBOSE, f"Result #{result_id + 1} has score {result_score}")

                if result_score < best_result_score:
                    best_result_score = result_score
                    best_result = result

            get_internal_afi().info(Verbosity.INFO_VERBOSE, f"Best result has score {best_result_score}")

            return best_result

        raise ErrInvalidIdentifier(
            "while running supervisor.",
            f"Invalid supervision result choice engine '{supervision_result_choice_engine}'."
        )

    def run_analysis(self, target: np.ndarray, /) -> SupervisionResult:
        # find all patterns in the target image

        _timer = Timer()

        with _timer:
            # apply mutators to the target image
            for mutator in self._target_mutators:
                target = mutator.mutate(target)

            # start matching
            matcher: IMatcher = self.get_matcher()
            matcher.setup(self)

            for keypoint in self.keypoints:
                get_internal_afi().info(Verbosity.DEBUG, f"Running matcher for keypoint '{keypoint.identifier}'.")
                assert isinstance(keypoint, InternalKeypoint)
                matcher.match(keypoint)

            keypoint_matching_result = InternalMatchingResult(self.identifier)

            for keypoint in self.keypoints:
                for match in matcher.get_matches_for_keypoint(keypoint):
                    keypoint_matching_result.add_match(match)

            if get_internal_context().visualization_generation_enabled():
                keypoint_matching_result.debug_print()

            keypoint_matching_result.validate()
            assert keypoint_matching_result.get_total_match_count() > 0

        get_internal_afi().info(
            Verbosity.INFO,
            f"Matching succeeded in {_timer.get_real_time():.2f} seconds of real time "
            f"and {_timer.get_cpu_time():.2f} seconds of CPU time."
        )

        with _timer:
            # run supervision to obtain correspondence between template and target regions
            supervision_result = self._run_supervisor(keypoint_matching_result)

        get_internal_afi().info(
            Verbosity.INFO,
            f"Supervision succeeded in {_timer.get_real_time():.2f} seconds of real time "
            f"and {_timer.get_cpu_time():.2f} seconds of CPU time."
        )

        if supervision_result is None:
            raise ErrSupervisionCorrespondenceNotFound(
                "while processing a supervision result.",
                f"Could not establish correspondence of the image with the '{self.identifier}' template."
            )

        # TODO: visualizations
        """
        if get_internal_context().visualization_generation_enabled():
            supervision_result_visualizer = SupervisionResultVisualizer(supervision_result, target)
            visualization = supervision_result_visualizer.render()
            get_internal_context().export_image(visualization, file_name="matches.png")
        """

        return supervision_result

    def __str__(self):
        return f"{self.name} ({self._source}, {len(self._keypoints)} keypoints, {len(self._features)} features)"
