# Em src/goldiscovery/main.py

from src.goldiscovery.core.discovery import start_discovery
import time

if __name__ == '__main__':
    start_time = time.time()

    start_discovery()

    end_time = time.time()
    print(f"\nTempo total de execução: {end_time - start_time:.2f} segundos.")