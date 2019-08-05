"""
Given a substack base directory created by prepare_substack.py,
launch a job on the LSF cluster to flatten it.

This is just a wrapper around bsub with the proper arguments.

EXAMPLE USAGE
-------------

    # First, prepare a substack directory (here, just 10 slices)
    python prepare_substack_dir.py 2 10000 10010
    
    # Then launch the job for that directory
    python launch_flatten.py --email-to bergs substack-Sec02-z10000-z10010

"""
import os
import json
import warnings
import argparse
import textwrap
import subprocess
from os.path import exists, abspath


FLATTEN_SCRIPT = '/groups/flyem/data/alignment/facefinder/src/hxadjustheightsurf/share/scripts/clusterLSFFlattenTwoSidesNoWeka.sh'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--email-to', '-e', help='Send email to this user upon job completion')
    parser.add_argument('substack_base_dir')
    args = parser.parse_args()

    args.substack_base_dir = abspath(args.substack_base_dir)
    with open(f'{args.substack_base_dir}/substack-params.json', 'r') as f:
        params = json.load(f)

    substack_base_dir = params['substack_base_dir']
    substack_name = params['substack_name']
    tab_name = params['tab_name']
    bill_to = params['bill_to']
    assert substack_base_dir == args.substack_base_dir, \
        "Mismatch between substack_base_dir from command-line and from substack-params.json"
    
    script_param_path = f"{substack_base_dir}/flatten/flattenParams.sh"
    assert exists(script_param_path), \
        f"Parameter script does not exist:\n{script_param_path}"

    log_path = f"{substack_base_dir}/logs/flatten.log"
    
    if os.environ['USER'] != 'flyem':
        warnings.warn("You aren't running as the 'flyem' user.  If something doesn't work, try re-running as flyem.")

    bsub_args = ["bsub"]
    bsub_args += ['-n 1']                                       # Use 1 slot
    bsub_args += [f'-J flatten_{substack_name}']                # job name
    bsub_args += [f'-env "PARAM_PATH={script_param_path}"']     # use this environment (only)
    bsub_args += [f'-P {bill_to}']                              # Bill to this project
    bsub_args += [f'-g "/{bill_to}/flatten/{tab_name}"']        # Job group
    bsub_args += [f'-o {log_path}']                             # Write to a log file 

    if args.email_to:
        bsub_args += [f'-u {args.email_to}']                    # Email this user when it's finished
        bsub_args += ['-N']                                     # Send email in addition to writing a log file (otherwise, -u is ignored when -o is present)
        bsub_args += ['-B']                                     # Also send an email when the job starts executing

    bsub_args += [f'{FLATTEN_SCRIPT} {script_param_path}']      # Command to execute

    bsub_cmd_pretty = ' \\\n  '.join(bsub_args)
    print("Launching job:\n")
    print(bsub_cmd_pretty)
    print("\n")

    bsub_cmd = ' '.join(bsub_args)
    bsub_output = subprocess.run(bsub_cmd, shell=True, check=True, capture_output=True)
    print(bsub_output.stdout.decode('utf-8'))

if __name__ == "__main__":
    main()
