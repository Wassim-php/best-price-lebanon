import os

from django.conf import settings

from scraping.adapters.websites.ayoub import AyoubComputersAdapter
from scraping.adapters.websites.souq961 import Souq961Adapter
from scraping.adapters.websites.abdeltahan import AbedTahanAdapter
from scraping.adapters.websites.mobileleb import MobileLebAdapter
from scraping.adapters.websites.hicart import HiCartAdapter
from scraping.adapters.websites.outgeeked import OutGeekedAdapter
from scraping.adapters.websites.zoodmall import ZoodMallAdapter
from scraping.adapters.websites.phonefinity import PhonefinityAdapter
from scraping.adapters.websites.dslrzone import DslrZoneAdapter
from scraping.adapters.websites.ishtari import IshtariAdapter
from scraping.adapters.websites.beytech import BeytechAdapter
from scraping.adapters.websites.ezonelb import EzoneLbAdapter

def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


# Central adapter registry used by search and comparison endpoints.
# Keys are the public source identifiers accepted by the API.
ADAPTERS = {
    "961souq": Souq961Adapter(),
    "ayoubcomputers": AyoubComputersAdapter(),
    "abdeltahan": AbedTahanAdapter(),
    "mobileleb": MobileLebAdapter(),
    "outgeeked": OutGeekedAdapter(),
    "zoodmall": ZoodMallAdapter(),
    "phonefinity": PhonefinityAdapter(),
    "dslrzone": DslrZoneAdapter(),
    "ishtari": IshtariAdapter(),
    "beytech": BeytechAdapter(),
    "ezonelb": EzoneLbAdapter(),
}

# Disable HiCart in production by default.
disable_hicart = _env_bool("DISABLE_HICART_IN_PROD", True) and not settings.DEBUG
if not disable_hicart:
    ADAPTERS["hicart"] = HiCartAdapter()
