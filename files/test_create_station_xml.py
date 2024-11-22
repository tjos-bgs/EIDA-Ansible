"""Unit tests for create_station_xml.py"""
import os
from pathlib import Path
import time

import pytest

import create_station_xml as csx

NAMES = ['HAS-NO-DATA_HH_N.0001-01-01-0000_SEED',
         'GAL1_HH_N.2009-02-16-0000_SEED',
         'GAL1_HH_Z.2006-08-24-0000_SEED',
         'GAL1_HH_Z.2009-02-16-0000_SEED',
         'HPK__HH_N.2009-02-16-0000_SEED',
         'HPK__HH_Z.2006-08-24-0000_SEED',
         'AU08_HH_E.2016-03-19-0000_SEED',
         'AU08_HH_N.2016-03-19-0000_SEED',
         'AU08_HH_Z.2016-03-19-0000_SEED',
         ]

STATION_DIRS = ['GB/GAL1', 'GB/HPK', 'GB/HAS_NO_HEADER', 'UR/AU08']

EXPECTED_INVENTORY = [
    'GAL1.xml',
    'HPK.xml',
    'AU08.xml',
    '.create_station_xml_last_run']


def test_main(dirs_before, monkeypatch):
    """Run end-to-end test of main method."""
    # Get test directories
    seisan_archive, seiscomp_inventory = dirs_before
    # Arrange file patching
    monkeypatch.setattr(csx, 'convert_to_station_xml', _mock_convert)
    # Confirm fixtures worked correctly
    assert (set(os.listdir(seisan_archive / 'CAL' / 'GB_dataless')) ==
            set(NAMES))

    # Act
    csx.main(seisan_archive, seiscomp_inventory)

    # Assert
    assert set(os.listdir(seiscomp_inventory)) == set(EXPECTED_INVENTORY)


def test_main_no_last_run_file(dirs_before, monkeypatch):
    """Run end-to-end test of main method.  Removing the last_run file should
    cause conversion to be run and new last_run file to be created."""
    # Get test directories
    seisan_archive, seiscomp_inventory = dirs_before
    # Arrange file patching
    monkeypatch.setattr(csx, 'convert_to_station_xml', _mock_convert)
    # Confirm fixtures worked correctly
    assert (set(os.listdir(seisan_archive / 'CAL' / 'GB_dataless')) ==
            set(NAMES))

    # Act
    os.remove(seiscomp_inventory / '.create_station_xml_last_run')
    csx.main(seisan_archive, seiscomp_inventory)

    # Assert
    assert set(os.listdir(seiscomp_inventory)) == set(EXPECTED_INVENTORY)


def test_main_recent_last_run_file(dirs_before, monkeypatch):
    """Run end-to-end test of main method.  Updating the last_run file should
    cause conversion to be skipped."""
    # Get test directories
    seisan_archive, seiscomp_inventory = dirs_before
    # Arrange file patching
    monkeypatch.setattr(csx, 'convert_to_station_xml', _mock_convert)
    # Confirm fixtures worked correctly
    assert (set(os.listdir(seisan_archive / 'CAL' / 'GB_dataless')) ==
            set(NAMES))

    # Act
    (seiscomp_inventory / '.create_station_xml_last_run').touch()

    with pytest.raises(SystemExit):
        # Script should finish with error if nothing to do
        csx.main(seisan_archive, seiscomp_inventory)

    # Assert that nothing was done
    pre_existing = {'.create_station_xml_last_run', 'delete_me'}
    assert set(os.listdir(seiscomp_inventory)) == pre_existing


@pytest.fixture(scope='function')
def dirs_before(tmpdir):
    """Create example files directory"""
    # Create example inventory (pre-existing files should be removed)
    seiscomp_inventory = Path(tmpdir.mkdir('inventory'))
    with open(seiscomp_inventory / 'delete_me', 'w') as f:
        f.write('Delete me!')

    # Add last_run file with older timestamp than archive files
    last_run_file = seiscomp_inventory / '.create_station_xml_last_run'
    last_run_file.touch()
    time.sleep(0.1)

    # Create dummy archive
    seisan_archive = Path(tmpdir.mkdir('seisan'))
    seisan_header_dir = seisan_archive / 'CAL' / 'GB_dataless'
    seisan_header_dir.mkdir(parents=True, exist_ok=True)
    seisan_data_dir = seisan_archive / 'SDS' / '2019'
    seisan_data_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy header files
    for name in NAMES:
        with open(seisan_header_dir / name, 'w') as f:
            f.write(name)

    # Create dummy data directories
    for station_dir in STATION_DIRS:
        (seisan_data_dir / station_dir).mkdir(parents=True, exist_ok=True)

    return (seisan_archive, seiscomp_inventory)


def _mock_convert(station, seed_headers, inventory_path):
    outfile = inventory_path / f"{station}.xml"
    # Create a mocked outfile
    with open(outfile, 'a') as f:
        for seed_header in seed_headers:
            f.write(seed_header.name + '\n')
