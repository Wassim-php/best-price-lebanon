from scraping.adapters.websites.ayoub import AyoubComputersAdapter
from scraping.adapters.websites.souq961 import Souq961Adapter
from scraping.adapters.websites.abdeltahan import AbedTahanAdapter
from scraping.adapters.websites.mobileb import MobileLebAdapter

ADAPTERS = {
    "961souq": Souq961Adapter(),
    "ayoubcomputers": AyoubComputersAdapter(),
    "abdeltahan": AbedTahanAdapter(),
    "mobileleb": MobileLebAdapter(),
}
