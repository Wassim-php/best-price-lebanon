from scraping.adapters.souq961 import Souq961Adapter
from scraping.adapters.ayoub import AyoubComputersAdapter

ADAPTERS = {
    "961souq": Souq961Adapter(),
    "ayoubcomputers": AyoubComputersAdapter(),
}
