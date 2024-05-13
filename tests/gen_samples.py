import datetime
import pathlib
import sys
import time

import numpy as np


def main():
    dir_name = 'samples'
    if len(sys.argv) > 1:
        dir_name = sys.argv[1]
    sample_dir = pathlib.Path(__file__).parent / dir_name
    sample_dir.mkdir(exist_ok=True)
    t = np.arange(720.)
    try:
        while True:
            stamp = datetime.datetime.now().strftime('%Y.%m.%d.%H.%M.%S.%f')
            sample_npy = sample_dir / f'{stamp}.npy'
            with open(sample_npy, 'wb') as npy_file:
                np.save(npy_file,
                        np.sin((t + 90. * time.time()) * np.pi / 180.))
            time.sleep(0.1)
    except KeyboardInterrupt:
        return 0
    except Exception:
        return 1


if __name__ == '__main__':
    main()
