"""
The FlyEM tab "flattening" scripts are written to process an entire tab at a time,
processing all of the PNG files in that slab's directory, such as:

  /nrs/flyem/alignment/Z1217-19m/VNC/Sec02/zcorr/

If you want to flatten only a subset of the slices for the slab,
you can extract the slices of interest into a new directory,
renumber them starting from 0, and run the flattening code on that new directory.

This script is a little utility for preparing such directories of slice subsets,
referred to here as "substacks".

The directory and config file format is defined here using a template that can
be rendered using the "cookiecutter" tool[1].

Then the input slices are added to the substack directory via symlinks,
which are renumbered starting with 0.

To actually process the substack, see launch_flatten.py.

[1]: https://cookiecutter.readthedocs.io/en/latest/

EXAMPLE USAGE
-------------

    # Create a substack directory to process 100 slices
    # from the middle of VNC section 02
    python prepare_substack.py 2 10000 10100

"""
import os
import re
import sys
import glob
import json
import shutil
import argparse
import subprocess
from os.path import dirname, basename, abspath, join, exists, splitext

from cookiecutter.main import cookiecutter

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda iterable, *args, **kwargs: list(iterable)
    

COOKIECUTTER_PATH = join(dirname(__file__), "substack-cookiecutter")
TEMPLATE_PATH = join(COOKIECUTTER_PATH, "{{cookiecutter.substack_name}}")

DEFAULT_SLICE_DIR_PATTERN = "/nrs/flyem/alignment/{fly}/{region}/{tab_name}/zcorr"

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--fly', default='Z1217-19m')
    parser.add_argument('--region', default='VNC')
    parser.add_argument('--input-slice-dir', '-d')
    parser.add_argument('--substack-name', '-n')
    parser.add_argument('--parent-output-dir', '-o', default='.')
    parser.add_argument('--copy-input', '-c', action='store_true',
                        help='If provided, copy the input slices into the substack directory instead of symlinking them.')
    parser.add_argument('tab_number', type=int)
    parser.add_argument('start_slice', type=int, help="First slice index to process.")
    parser.add_argument('stop_slice', type=int, help="One-beyond the last slice to process")
    args = parser.parse_args()
    
    fly = args.fly
    region = args.region
    tab_name = f"Sec{args.tab_number:02d}"

    if not args.input_slice_dir:
        args.input_slice_dir = DEFAULT_SLICE_DIR_PATTERN.format(**locals())
    
    if not args.substack_name:
        args.substack_name = f"substack-{tab_name}-z{args.start_slice:05d}-z{args.stop_slice:05d}"
    
    if not exists(COOKIECUTTER_PATH):
        print(f"Cookiecutter directory doesn't exist: {COOKIECUTTER_PATH}", file=sys.stderr)
        sys.exit(1)
        
    if not exists(TEMPLATE_PATH):
        # As far as I can tell, there's no way to have cookiecutter
        # tell me what the final output path will be, so I have to hard-code
        # the 'substack_base_dir' format below.
        # In that case, I better make sure the template has the name I'm expecting. 
        print(f"Cookiecutter template doesn't exist or has the wrong name: {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)

    # The name of the rendered output directory (always equal to the substack_name)
    substack_base_dir = abspath(args.parent_output_dir) + '/' + args.substack_name
    substack_slice_dir = f"{substack_base_dir}/input_slices"

    # We use cookiecutter in completely non-interactive mode.
    # Overwrite every context key with our own values.
    cookiecutter_params = {
      "substack_name": args.substack_name,
      "substack_base_dir": substack_base_dir,
      "substack_slice_dir": substack_slice_dir,
      "fly": args.fly,
      "tab_name": tab_name,
      "bill_to": "flyem"
    }
    
    # Run cookiecutter
    print(f"Creating {substack_base_dir}")
    cookiecutter(COOKIECUTTER_PATH, no_input=True, extra_context=cookiecutter_params)

    os.makedirs(substack_slice_dir)
    os.makedirs(f"{substack_base_dir}/logs")

    # Dump the final cookiecutter params to the output,
    # for other scripts to use if necessary.
    with open(f'{substack_base_dir}/substack-params.json', 'w') as f:
        json.dump(cookiecutter_params, f)

    subprocess.run(f'chmod -R g+w {substack_base_dir}', shell=True, check=True)

    # Populate the input directory with symlinks to the original slices, but renumbered.
    print(f"Reading filenames in {args.input_slice_dir}")
    all_input_slices = glob.glob(f"{args.input_slice_dir}/*")
    all_input_slices = list(filter(lambda p: splitext(p)[1] in ('.png', '.tif'), all_input_slices))
    ext = splitext(all_input_slices[0])[1]
    
    indexed_slices = {}

    pat = re.compile(r"(\d+)")
    for p in all_input_slices:
        m = pat.search(basename(p))
        if not m:
            raise RuntimeError(f"Slice file doesn't seem to be numbered: {p}")

        index = int(m.groups()[0])
        indexed_slices[index] = abspath(p)

    if args.copy_input:
        print(f"Copying input files to {substack_slice_dir}")
    else:
        print(f"Creating symlinks in {substack_slice_dir}")

    for new_index, orig_index in tqdm([*enumerate(range(args.start_slice, args.stop_slice))]):
        src = indexed_slices[orig_index]
        dest = f"{substack_slice_dir}/{new_index:05d}{ext}"
        if args.copy_input:
            shutil.copyfile(src, dest)
        else:
            os.symlink(src, dest)

    print("DONE")


if __name__ == "__main__":
    main()
