import os
import json
import warnings
import argparse
import textwrap
import subprocess
from os.path import exists, abspath


FLATTEN_SCRIPT = '/groups/flyem/data/alignment/facefinder/src/hxadjustheightsurf/share/scripts/clusterLSFFlattenTwoSidesNoWeka.sh'


def main():
    parser = argparse.ArgumentParser()
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
    #job_id, queue_name, parse_bsub_output(bsub_output.stdout)


def parse_bsub_output(bsub_output):
    """
    Parse the given output from the 'bsub' command and return the job ID and the queue name.

    Example:
        
        >>> bsub_output = "Job <774133> is submitted to queue <spark>.\n"
        >>> job_id, queue_name = parse_bsub_output(bsub_output)
        >>> assert job_id == '774133'
        >>> assert queue_name == 'spark'
    """
    nonbracket_text = '[^<>]*'
    field_pattern = f"{nonbracket_text}<({nonbracket_text})>{nonbracket_text}"

    NUM_FIELDS = 2
    field_matches = re.match(NUM_FIELDS*field_pattern, bsub_output)

    if not field_matches:
        raise RuntimeError(f"Could not parse bsub output: {bsub_output}")

    job_id = field_matches.groups()[0]
    queue_name = field_matches.groups()[1]
    return job_id, queue_name


if __name__ == "__main__":
    main()
