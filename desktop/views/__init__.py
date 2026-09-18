"""Desktop views package."""

from .home_view import HomeView
from .ping_pong_view import PingPongView
from .surround_view import SurroundView
from .vocal_remover_view import VocalRemoverView, BgmExtractorView, StemSeparatorView
from .vocal_extractor_view import VocalExtractorView
from .demucs_splitter_view import DemucsSplitterView

__all__ = [
    "HomeView",
    "PingPongView",
    "SurroundView",
    "VocalRemoverView",
    "BgmExtractorView",
    "StemSeparatorView",
    "VocalExtractorView",
    "DemucsSplitterView",
]
