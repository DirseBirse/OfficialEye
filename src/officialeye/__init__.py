"""
Root module.
"""

# Context
# noinspection PyProtectedMember
from officialeye._api.context import Context

# Config
# noinspection PyProtectedMember
from officialeye._api.config import Config, MutatorConfig, MatcherConfig, SupervisorConfig, InterpretationConfig

# Image-processing
# noinspection PyProtectedMember
from officialeye._api.image import IImage, Image

# Mutators
# noinspection PyProtectedMember
from officialeye._api.mutator import Mutator, IMutator

# Template-related
# noinspection PyProtectedMember
from officialeye._api.template.template import ITemplate, Template

# Regions, features and keypoints
# noinspection PyProtectedMember
from officialeye._api.template.region import IRegion, Region
# noinspection PyProtectedMember
from officialeye._api.template.feature import IFeature
# noinspection PyProtectedMember
from officialeye._api.template.keypoint import IKeypoint

# Matching-related imports
# noinspection PyProtectedMember
from officialeye._api.template.match import IMatch, Match
# noinspection PyProtectedMember
from officialeye._api.template.matcher import IMatcher, Matcher
# noinspection PyProtectedMember
from officialeye._api.template.matching_result import IMatchingResult

# Supervision-related imports
# noinspection PyProtectedMember
from officialeye._api.template.supervisor import ISupervisor, Supervisor
# noinspection PyProtectedMember
from officialeye._api.template.supervision_result import ISupervisionResult, SupervisionResult

# Interpretation-related imports
# noinspection PyProtectedMember
from officialeye._api.template.interpretation import IInterpretation, Interpretation
# noinspection PyProtectedMember
from officialeye._api.template.interpretation_result import IInterpretationResult

# Misc
# noinspection PyProtectedMember
from officialeye._api.future import Future, wait
