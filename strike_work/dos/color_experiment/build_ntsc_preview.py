"""Build the local NTSC preview adapter against the project's GX source."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('gx_source', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='eco_ntsc_') as temporary:
    include = Path(temporary)
    for name in ['md_ntsc.c', 'md_ntsc.h', 'md_ntsc_config.h', 'md_ntsc_impl.h']:
        shutil.copyfile(args.gx_source/'core/ntsc'/name, include/name)
    # The custom blitter has no dependency on the GX global video bitmap.
    (include/'shared.h').write_text('')
    subprocess.run(['gcc', '-shared', '-fPIC', '-O2', '-I'+str(include),
                    str(root/'ntsc_preview.c'), '-lm', '-o', str(root/'preview.so')], check=True)
