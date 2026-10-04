"""ثبت agentهای چندپروفایلی."""

from . import autonomous as _autonomous  # noqa: F401
from . import coding as _coding  # noqa: F401
from . import debug as _debug  # noqa: F401
from . import maintenance as _maintenance  # noqa: F401
from . import marketing as _marketing  # noqa: F401
from . import seo as _seo  # noqa: F401
from . import social as _social  # noqa: F401

__all__ = [
    "_autonomous",
    "_coding",
    "_debug",
    "_maintenance",
    "_marketing",
    "_seo",
    "_social",
]
