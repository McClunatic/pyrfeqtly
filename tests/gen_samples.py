import datetime
import pathlib
import time

import numpy as np


def main():
    sample_sources = ['sine', 'cosine']
    sample_dir = pathlib.Path(__file__).parent / 'files'
    sample_dir.mkdir(exist_ok=True)

    now = time.time()
    t = np.arange(720.)
    try:
        while True:
            dt = time.time() - now
            for sample_src in sample_sources:
                if sample_src == 'sine':
                    func = np.sin
                    freq = 0.5
                    ampl = 2
                else:
                    func = np.cos
                    freq = 0.3
                    ampl = 1
                stamp = datetime.datetime.now().strftime(
                    '%Y.%m.%d.%H.%M.%S.%f')
                sample_npy = sample_dir / f'{sample_src}_{stamp}.npy'
                with open(sample_npy, 'wb') as npy_file:
                    a = ampl * func(freq * (dt + t * np.pi / 180.))
                    np.save(npy_file, a)
                time.sleep(0.1)
            time.sleep(0.8)
    except KeyboardInterrupt:
        return 0
    except Exception:
        return 1


if __name__ == '__main__':
    main()
