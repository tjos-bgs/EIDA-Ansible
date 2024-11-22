"""Script to convert dataless SEED files to seiscomp SCML"""
from collections import defaultdict
import shutil
import os,re
from pathlib import Path
import subprocess
import sys, glob
import smtplib
from email.message import EmailMessage

HOME_DIR     = Path('<redacted>')
SEISCOMP_DIR = HOME_DIR / 'seiscomp6' / 'seiscomp'
ADDRESSES    = "<redacted>"

def main(home_dir, seiscomp_dir):
    """Convert dataless seed files to seiscomp scml"""

    # Paths
    seisan_dir         = home_dir / 'seisan'
    seisan_archive_dir = seisan_dir / 'SDS'
    dataless_seed_dir  = seisan_dir / 'CAL' / 'GB_dataless'
    seiscomp_inventory = seiscomp_dir / 'etc' / 'inventory'
    extra_scml_dir     = home_dir / 'non_GB_scml'

    # Executables
    seiscomp = f'{seiscomp_dir}/bin/seiscomp'
    dlsv2inv = f'{seiscomp_dir}/bin/dlsv2inv'
    
    # Get list of stations in seiscomp SDS database
    station_list = get_stations(seisan_archive_dir)

    # Get list of dataless seed files for stations in list 
    dataless_seeds = get_dataless_seeds(station_list,dataless_seed_dir)

    # Check if files modified since last run date
    last_run_file = seiscomp_inventory / '.create_station_xml_last_run'

    # Exit with error if files unchanged - this prevents seiscomp update
    if not files_changed_since_last_run(dataless_seeds, last_run_file):
        print("Inventory files unchanged.")
        sys.exit(1)
		
    # Group dataless seed files by station and channel
    stations = defaultdict(lambda: defaultdict(list))
    got_sta =set()
    for dataless_seed in dataless_seeds:
        m = re.search('([A-Z0-9_]{5})(\w\w)_(\w)(_\d\d)?\.\d\d\d\d\-\d\d\-\d\d\-\d\d\d\d_SEED',str(dataless_seed))
        if (m):
            sta = m.group(1).strip("_")
            cha = m.group(2) + m.group(3)
            #if (m.group(4)): continue             # non 00 location codes 
        else:
            raise Exception("Unrecognised dataless: "+ str(dataless_seed))
        stations[sta][cha].append(dataless_seed)
        got_sta.add(sta)

    # Check for data without metadata
    miss_sta = station_list - got_sta
    if (miss_sta):
        print ("WARN: missing dataless seed files for:",end=" ")
        for sta in miss_sta:
            print(sta,end=" ")
        print()

    # Clear out inventory directory
    clean_inventory(seiscomp_inventory)

    # Put back any SCML files for temporary networks
    replace_extra_scml(seiscomp_inventory,extra_scml_dir)
	
    # Convert dataless files to seiscomp SCML in inventory directory
    convert_to_station_xml(stations, seiscomp_inventory, dlsv2inv)

    # Check for any missing lat and lon
    for xml_file in seiscomp_inventory.glob('*.xml'):
        if '<latitude>0</latitude>' in xml_file.read_text():
            print(f"WARN: {xml_file} has null lat/lon")

    # Update seiscomp inventory here so can catch exception
    cmd = [seiscomp, "update-config", "inventory"]
    try:
        output = subprocess.run(cmd,capture_output=True)
    except:
        raise Exception(seiscomp)
    if (output.returncode):
        raise Exception(' '.join(map(str,cmd)),str(output.stderr))

    last_run_file.touch()
    print("\nNow run: seiscomp restart")


def files_changed_since_last_run(files, last_run_file):
    """Check if files have changed since script was last run"""
    files_changed = max(f.stat().st_mtime for f in files)
    try:
        last_run_time = last_run_file.stat().st_mtime
    except FileNotFoundError:
        # Set very old time to ensure that update runs
        last_run_time = 0
    return files_changed > last_run_time


# Get list of dataless seed files to convert to SCML
def get_dataless_seeds(station_list,dataless_seed_dir):
    """Return list of dataless seed files.""" 
    dataless_seeds = [f for f in dataless_seed_dir.iterdir()
                    if f.name.endswith('SEED')
                    and f.name[:5].strip('_') in station_list]     
    return dataless_seeds


# List all stations in SDS database for wanted network codes 
# Stations don't want to share are excluded in fdsnws_filter.ini
def get_stations(seisan_archive_dir):
    """Return list of stations in the archive."""
    # Find stations by checking SDS for these networks
    wanted_nets = [ "GB","UR","BN" ]
    station_list = set()
    for net in wanted_nets:
        for dir in (glob.iglob(f'{seisan_archive_dir}/*/{net}/*')):
            station_list.add(dir.split('/')[-1])
    return station_list


# Empty inventory directory or will get clashes and crash the sync
def clean_inventory(dirpath):
    """Remove all files in dirpath except last_run file"""
    print(f'Removing existing files from {dirpath}')
    for inventory_file in dirpath.rglob('*'):
        if not inventory_file.name.endswith('_last_run'):
            os.remove(inventory_file)

# After inventory directory been emptied put back scml for extra networks
def replace_extra_scml(seiscomp_inventory,extra_scml_dir):
    """Put back scml files want to keep"""
    print(f'Replacing files from {extra_scml_dir}')
    for file_name in os.listdir(extra_scml_dir):
        full_file_name = os.path.join(extra_scml_dir, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, seiscomp_inventory)

# Create one SCML file per channel
def convert_to_station_xml(stations, inventory_path, dlsv2inv):
    """Convert dataless seed to station scml at given inventory path."""

    # Want to add DOI for network to SCML
    doi_comment = '<text>{"type":"DOI","value":"10.7914/av8j-nc83"}</text><id>FDSNXML:Identifier/0</id>'

    for sta, chans in stations.items():
        for cha, dataless_seeds in chans.items():
            # concatenate dataless seeds for channel in chronological order
            with (open("temp.dataless","wb") as outfile):
                dataless_seeds.sort()
                for dataless_seed in (dataless_seeds):
                    with (open(dataless_seed,"rb") as infile):
                        shutil.copyfileobj(infile, outfile)
		   
            # Convert dataless to station xml
            xmlfile = inventory_path / f'{sta}.{cha}.xml'
            cmd = f'{dlsv2inv} temp.dataless {xmlfile}'
            try:
                output = subprocess.run(cmd,shell=True,capture_output=True)
            except:
                raise Exception(dlsv2inv)
            if (output.returncode):
                raise Exception(' '.join(map(str,cmd)),str(output.stderr))

            # Add DOI tag if network is GB
            try:
                f = open(xmlfile)
            except:
                raise Exception(f"Can't open {xmlfile}")
            with f:
                line = f.read()

            m = re.search('<network publicID="Network/[\d\.]*" code="([A-Z][A-Z])">',line)
            if not m:
               raise Exception(f"No <network> found in {xmlfile}")
            if (m.group(1) == "GB"):
                # First shared tag is for network, subsequent one for station, only want DOI for network
                (line,nsub) = re.subn('</shared>',f'</shared><comment>{doi_comment}</comment>',line,1)
                if not nsub:
                    raise Exception(f"No </shared> tags in {xmlfile}")
                with open(xmlfile,"w") as f:
                    f.write(line)
                
# Email on error
def email_error(message):
    """Email if there is a problem."""

    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = 'EIDA create_station_xml'
    msg['From'] = '<redacted>'
    msg['To'] = ADDRESSES
     
    smtp_server = smtplib.SMTP('localhost')
    smtp_server.send_message(msg)
    smtp_server.quit()

if __name__ == '__main__':
    try:
       main(HOME_DIR, SEISCOMP_DIR)

    except Exception as err:
        print(f'ERROR: {err}')
        email_error(str(err))
        sys.exit(1) 
