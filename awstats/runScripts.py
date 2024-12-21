import argparse
import subprocess
import os
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run AWStats processing scripts.')
    parser.add_argument('--server', type=str, help='Specify the server location')
    parser.add_argument('--file', type=str, help='Specify the file to process')
    parser.add_argument('--force', action='store_true', help='Force processing of the specified file')
    parser.add_argument('--website', type=str, help='Specify the website name')
    parser.add_argument('--script', nargs='+', help='Specify script(s) to run (e.g., summary)')
    return parser.parse_args()

def run_script(script_name, args):
    # Build the command with the full path to the script
    script_path = os.path.join(SCRIPT_DIR, f'{script_name}.py')
    command = ['python3', script_path]
    if args.server:
        command.extend(['--server', args.server])
    if args.file:
        command.extend(['--file', args.file])
    if args.force:
        command.append('--force')
    if args.website:
        command.extend(['--website', args.website])
    subprocess.run(command)

def main():
    global SCRIPT_DIR  # Set this as a global variable for use in other functions
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Change the current working directory to the script's location
    os.chdir(SCRIPT_DIR)

    args = parse_arguments()

    # List of available scripts
    available_scripts = ['summary', 'urls']  # Add others as necessary

    if args.script:
        # Run only the specified scripts
        for script in args.script:
            if script in available_scripts:
                run_script(script, args)
            else:
                print(f"Script '{script}' not found in available scripts.")
    else:
        # Run all scripts
        for script in available_scripts:
            run_script(script, args)

if __name__ == "__main__":
    main()
