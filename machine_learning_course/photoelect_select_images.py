import sys
import argparse
import datetime
import numpy             as np
import pandas            as pd
import matplotlib.pyplot as plt

import antea.reco.reco_functions   as rf
import antea.reco.mctrue_functions as mcf

from antea.io.mc_io import load_mchits
from antea.io.mc_io import load_mcparticles
from antea.io.mc_io import load_mcsns_response

"""
python photoelect_select_images.py 22 1 /Users/carmenromoluque/Desktop/ full_body_iradius380mm_z200cm_depth4cm_pitch7mm /Users/carmenromoluque/Desktop/
"""

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('first_file' , type = int, help = "first file (inclusive)"     )
    parser.add_argument('n_files'    , type = int, help = "number of files to analize" )
    parser.add_argument('events_path',             help = "input files path"           )
    parser.add_argument('file_name'  ,             help = "name of input files"        )
    parser.add_argument('data_path'  ,             help = "output files path"          )
    return parser.parse_args()

def needed_info_to_plot(pos, q):
    pos_cyl = rf.from_cartesian_to_cyl(np.array(pos)).transpose()
    barycenter_touched_sns_cyl = np.average(pos_cyl, axis=1, weights=q)
    dist_between_sns_phi = 0.01707387 #rad
    dist_between_sns_z   = 7. #mm (pitch)
    range_phi = (barycenter_touched_sns_cyl[1] - 10*dist_between_sns_phi,
                 barycenter_touched_sns_cyl[1] + 10*dist_between_sns_phi)
    range_z   = (barycenter_touched_sns_cyl[2] - 10*dist_between_sns_z,
                 barycenter_touched_sns_cyl[2] + 10*dist_between_sns_z)
    return pos_cyl, range_z, range_phi

def hist_matrix_z_phi(evt, pos_cyl, q, range_z, range_phi):
    hist = plt.hist2d(pos_cyl[2], pos_cyl[1], bins=(20, 20), range=(range_z, range_phi), weights=q)
    return hist

arguments  = parse_args(sys.argv)
start      = arguments.first_file
numb       = arguments.n_files
eventsPath = arguments.events_path
file_name  = arguments.file_name
data_path  = arguments.data_path

phot_images     = []
evt_ids         = []
min_touched_sns = 50
threshold       = 2

evt_file = f"{data_path}/full_body_4cmdepth_phot_images_{start}_{numb}_{threshold}"

for number in range(start, start+numb):
    number_str = "{:03d}".format(number)
    filename  = f"{eventsPath}/{file_name}.{number_str}.pet.h5"
    try:
        sns_response = load_mcsns_response(filename)
    except ValueError:
        print(f'File {filename} not found')
        continue
    except OSError:
        print(f'File {filename} not found')
        continue
    except KeyError:
        print(f'No object named MC/waveforms in file {filename}')
        continue
    print(f'Analyzing file {filename}')

    particles    = load_mcparticles(filename)
    hits         = load_mchits     (filename)
    sens_pos     = pd.read_hdf     (filename, 'MC/sensor_positions')

    DataSiPM     = sens_pos.rename(columns={"sensor_id": "SensorID","x": "X", "y": "Y", "z": "Z"})
    DataSiPM_idx = DataSiPM.set_index('SensorID')

    sel_df = rf.find_SiPMs_over_threshold(sns_response, threshold=threshold)
    events = particles.event_id.unique()

    for evt in events:
        images = []
        ### Select photoelectric events only
        evt_parts = particles[particles.event_id == evt]
        evt_hits  = hits     [hits     .event_id == evt]
        select, true_pos = mcf.select_photoelectric(evt_parts, evt_hits)
        if not select: continue
        waveforms = sel_df[sel_df.event_id == evt]
        id1, id2, pos1, pos2, q1, q2 = rf.assign_sipms_to_gammas(waveforms, true_pos, DataSiPM_idx)

        if len(id1)>min_touched_sns:
            pos1_cyl, range_z1, range_phi1 = needed_info_to_plot(pos1, q1)
            h1 = hist_matrix_z_phi(evt, pos1_cyl, q1, range_z1, range_phi1)
            if len(np.nonzero(h1[0].flatten())[0])>min_touched_sns:
                images.append(h1[0])

        elif len(id2)>min_touched_sns:
            pos2_cyl, range_z2, range_phi2 = needed_info_to_plot(pos2, q2)
            h2 = hist_matrix_z_phi(evt, pos2_cyl, q2, range_z2, range_phi2)
            if len(np.nonzero(h2[0].flatten())[0])>min_touched_sns:
                images.append(h2[0])
        else:continue
        evt_ids.append(evt)
        phot_images.append(np.array(images))

a_phot_images = np.array(phot_images)
np.savez(evt_file, evt_ids=evt_ids, phot_images=a_phot_images)

print(datetime.datetime.now())
