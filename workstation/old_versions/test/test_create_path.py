import numpy as np
import os
from importlib import reload
reload(create_path)

import create_path

paths, intersects = create_path.find_direct_paths(91, 207, map)