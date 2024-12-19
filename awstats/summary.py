import os
import argparse
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

def get_server_id(directory):
    # Map directories to server IDs
    server_mapping = {
        '/var/lib/awstats': 1,
        '/home/private/server_stats/frankfurt': 2,
        '/home/private/server_stats/saopaulo': 4,
        '/home/private/server_stats/singapore': 3
    }
    return server_mapping.get(directory)

def get_website_id(cursor, website_name):
    # Check if website exists, else create it
    cursor.execute("SELECT id FROM websites WHERE name = %s", (website_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO websites (name) VALUES (%s)", (website_name,))
        return cursor.lastrowid
		
def parse_begin_map(file):
    # Parse the BEGIN_MAP section to get positions
    positions = {}
    for line in file:
        line = line.decode('utf-8').strip()
        if line.startswith('BEGIN_MAP'):
            continue
        elif line.startswith('END_MAP'):
            break
        else:
            parts = line.split()
            if len(parts) == 2 and parts[0].startswith('POS_'):
                positions[parts[0]] = int(parts[1])
    return positions

def parse_pos_general(file, pos_general_offset):
    # Extract TotalUnique from POS_GENERAL
    file.seek(pos_general_offset)
    total_unique = None
    for line in file:
        line = line.decode('utf-8').strip()
        if line.startswith('END_GENERAL'):
            break
        elif line.startswith('TotalUnique'):
            total_unique = int(line.split()[1])
    return total_unique

def parse_pos_day(file, pos_day_offset):
    # Extract daily data from POS_DAY
    file.seek(pos_day_offset)
    daily_data = []
    for line in file:
        line = line.decode('utf-8').strip()
        if line.startswith('END_DAY'):
            break
        elif not line.startswith('#') and not line.startswith('BEGIN_DAY'):
            parts = line.split()
            if len(parts) == 5:
                date_str, pages, hits, bandwidth, visits = parts
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                daily_data.append({
                    'year': year,
                    'month': month,
                    'day': day,
                    'pages': int(pages),
                    'hits': int(hits),
                    'bandwidth': int(bandwidth),
                    'number_of_visits': int(visits)
                })
    return daily_data

def process_file(cursor, file_path, server_id, force):
    filename = os.path.basename(file_path)

    with open(file_path, 'rb') as file:
        # Parse BEGIN_MAP to get positions
        positions = parse_begin_map(file)

        # Check if necessary positions are available
        if 'POS_GENERAL' not in positions or 'POS_DAY' not in positions:
            print(f"Required sections not found in {filename}")
            return

        # Parse POS_GENERAL to get TotalUnique
        total_unique = parse_pos_general(file, positions['POS_GENERAL'])

        # Parse POS_DAY to get daily data
        daily_data = parse_pos_day(file, positions['POS_DAY'])

    # Extract website name from filename
    website_name = '.'.join(filename.split('.')[1:-1])
    website_id = get_website_id(cursor, website_name)

    # Insert monthly TotalUnique into summary table
    if total_unique is not None and daily_data:
        year = daily_data[0]['year']
        month = daily_data[0]['month']
        day = 0
        cursor.execute("""
            INSERT INTO summary (website_id, server_id, year, month, day, unique_visitors)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE unique_visitors = VALUES(unique_visitors)
        """, (website_id, server_id, year, month, day, total_unique))

    # Insert daily data into summary table
    for data in daily_data:
        cursor.execute("""
            INSERT INTO summary (website_id, server_id, year, month, day, number_of_visits, pages, hits, bandwidth)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE number_of_visits = VALUES(number_of_visits),
            pages = VALUES(pages), hits = VALUES(hits), bandwidth = VALUES(bandwidth)
        """, (website_id, server_id, data['year'], data['month'], data['day'],
              data['number_of_visits'], data['pages'], data['hits'], data['bandwidth']))

    # Done
    print(f"Processed file {filename}.")

def main():
    parser = argparse.ArgumentParser(description='Process AWStats summary data.')
    parser.add_argument('--server', type=str, help='Specify the server location')
    parser.add_argument('--file', type=str, help='Specify the file to process')
    parser.add_argument('--force', action='store_true', help='Force processing of the file(s)')
    args = parser.parse_args()

    connection = get_database_connection()
    cursor = connection.cursor()

    directories = [
        '/var/lib/awstats',
        '/home/private/server_stats/frankfurt',
        '/home/private/server_stats/saopaulo',
        '/home/private/server_stats/singapore'
    ]

    if args.server:
        # Process only the specified server directory
        directories = [dir for dir in directories if args.server in dir]
        if not directories:
            print(f"No directory found for server '{args.server}'.")
            return

    for directory in directories:
        server_id = get_server_id(directory)
        if server_id is None:
            print(f"Server ID not found for directory '{directory}'.")
            continue
        if args.file:
            # Process only the specified file
            file_path = os.path.join(directory, args.file)
            if os.path.exists(file_path):
                process_file(cursor, file_path, server_id, args.force)
            else:
                print(f"File '{args.file}' not found in directory '{directory}'.")
        else:
            # Process all files in the directory
            for filename in os.listdir(directory):
                if filename.endswith('.txt') and 'awstats' in filename:
                    file_path = os.path.join(directory, filename)
                    process_file(cursor, file_path, server_id, args.force)

    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
