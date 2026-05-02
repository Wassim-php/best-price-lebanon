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

ADAPTERS = {
        "961souq": Souq961Adapter(),
        "ayoubcomputers": AyoubComputersAdapter(),
        "abdeltahan": AbedTahanAdapter(),
        "mobileleb": MobileLebAdapter(),
        "hicart": HiCartAdapter(),
        "outgeeked": OutGeekedAdapter(),
        "zoodmall": ZoodMallAdapter(),
        "phonefinity": PhonefinityAdapter(),
        "dslrzone": DslrZoneAdapter(),
        "ishtari": IshtariAdapter(),
        "beytech": BeytechAdapter(),
        "ezonelb": EzoneLbAdapter(),

}
