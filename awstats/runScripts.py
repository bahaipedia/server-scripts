import argparse
import subprocess
import os
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database credentials from .env
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Database connection
def get_database_connection():
    return mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run AWStats processing scripts.')
    parser.add_argument('--server', type=str, help='Specify the server location')
    parser.add_argument('--file', type=str, help='Specify the file to process')
    parser.add_argument('--force', action='store_true', help='Force processing of the specified file')
    parser.add_argument('--website', type=str, help='Specify the website name')
    parser.add_argument('--script', nargs='+', help='Specify script(s) to run (e.g., summary)')
    return parser.parse_args()

def has_file_been_processed(cursor, filename, server_id, last_modified, force):
    if force:
        return False
    cursor.execute("""
        SELECT last_modified FROM file_tracking
        WHERE filename = %s AND server_id = %s
    """, (filename, server_id))
    result = cursor.fetchone()
    return result and result[0] == last_modified

def update_file_tracking(cursor, filename, server_id, last_modified):
    cursor.execute("""
        INSERT INTO file_tracking (filename, server_id, last_modified, processed_date)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE last_modified = VALUES(last_modified), processed_date = VALUES(processed_date)
    """, (filename, server_id, last_modified, datetime.now().replace(microsecond=0)))

def run_script(script_name, args):
    command = ['python3', f'{script_name}.py']
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
    args = parse_arguments()
    connection = get_database_connection()
    cursor = connection.cursor()

    # List of available scripts
    available_scripts = ['summary', 'urls'] 

    directories = [
        '/var/lib/awstats',
        '/home/private/server_stats/frankfurt',
        '/home/private/server_stats/saopaulo',
        '/home/private/server_stats/singapore'
    ]

    if args.server:
        directories = [dir for dir in directories if args.server in dir]
        if not directories:
            print(f"No directory found for server '{args.server}'.")
            return

    # Process specified or all files in the directories
    for directory in directories:
        server_id = get_server_id(directory)
        if server_id is None:
            print(f"Server ID not found for directory '{directory}'.")
            continue

        filenames = [args.file] if args.file else os.listdir(directory)
        for filename in filenames:
            if filename.endswith('.txt') and 'awstats' in filename:
                file_path = os.path.join(directory, filename)
                last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).replace(microsecond=0)

                # Check if the file has already been processed
                if has_file_been_processed(cursor, filename, server_id, last_modified, args.force):
                    print(f"File {filename} has already been processed.")
                    continue

                # Run specified scripts or all available scripts
                scripts_to_run = args.script if args.script else available_scripts
                for script in scripts_to_run:
                    if script in available_scripts:
                        run_script(script, args)
                    else:
                        print(f"Script '{script}' not found in available scripts.")

                # Update file tracking after processing
                update_file_tracking(cursor, filename, server_id, last_modified)

    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
