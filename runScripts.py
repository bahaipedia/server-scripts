import argparse
import subprocess

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run AWStats processing scripts.')
    parser.add_argument('--server', type=str, help='Specify the server location')
    parser.add_argument('--file', type=str, help='Specify the file to process')
    parser.add_argument('--force', action='store_true', help='Force processing of the specified file')
    parser.add_argument('--script', nargs='+', help='Specify script(s) to run (e.g., summary)')
    return parser.parse_args()

def run_script(script_name, args):
    command = ['python3', f'{script_name}.py']
    if args.server:
        command.extend(['--server', args.server])
    if args.file:
        command.extend(['--file', args.file])
    if args.force:
        command.append('--force')
    subprocess.run(command)

def main():
    args = parse_arguments()
    
    # List of available scripts
    available_scripts = ['summary', 'pages', 'browsers']  # Add other scripts as needed

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
