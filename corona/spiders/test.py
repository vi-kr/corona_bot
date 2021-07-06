from datetime import datetime
import os
import pathlib

print((str(pathlib.Path(__file__).resolve().parents[2]) + os.path.sep + "data"
                    + os.path.sep + datetime.now().strftime("%Y%m%d") + ".csv"))
