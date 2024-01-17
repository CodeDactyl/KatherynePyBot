import random
from datetime import datetime

random.seed(datetime.fromisoformat("2023-11-16T23:04:29.576569"))
print(random.randint(0, 525600))
