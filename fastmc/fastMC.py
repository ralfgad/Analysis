import sys
import argparse
import pandas   as pd

import antea.database.load_db  as db
import antea.mcsim   .errmat   as errmat
import antea.mcsim   .errmat3d as errmat3d
import antea.mcsim   .fastmc3d as fmc
import antea.io      .mc_io    as mcio

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('first_file' , type = int, help = "first file (inclusive)"    )
    parser.add_argument('n_files'    , type = int, help = "number of files to analize")
    parser.add_argument('matrix_path',             help = "path of the error matrix"  )
    parser.add_argument('events_path',             help = "input files path"          )
    return parser.parse_args()


DataSiPM     = db.DataSiPMsim_only('petalo', 0)
DataSiPM_idx = DataSiPM.set_index('SensorID')


arguments     = parse_args(sys.argv)
start         = arguments.first_file
numb_of_files = arguments.n_files
table_folder  = arguments.matrix_path
folder        = arguments.events_path

err_r_phot_file      = table_folder + '/errmat_r_phot_like.npz'
err_r_compt_file     = table_folder + '/errmat_r_compt_like.npz'
err_phi_phot_file    = table_folder + '/errmat_phi_phot_like.npz'
err_phi_compt_file   = table_folder + '/errmat_phi_compt_like.npz'
err_z_phot_file      = table_folder + '/errmat_z_phot_like.npz'
err_z_compt_file     = table_folder + '/errmat_z_compt_like.npz'
err_t_th_phot_file0  = table_folder + '/errmat_t_thr0.5pes_phot_like.npz'
err_t_th_compt_file0 = table_folder + '/errmat_t_thr0.5pes_compt_like.npz'
err_t_th_phot_file1  = table_folder + '/errmat_t_thr1.0pes_phot_like.npz'
err_t_th_compt_file1 = table_folder + '/errmat_t_thr1.0pes_compt_like.npz'
err_t_th_phot_file2  = table_folder + '/errmat_t_thr1.5pes_phot_like.npz'
err_t_th_compt_file2 = table_folder + '/errmat_t_thr1.5pes_compt_like.npz'

errmat_r_phot      = errmat.errmat(err_r_phot_file)
errmat_r_compt     = errmat.errmat(err_r_compt_file)
errmat_phi_phot    = errmat3d.errmat3d(err_phi_phot_file)
errmat_phi_compt   = errmat3d.errmat3d(err_phi_compt_file)
errmat_z_phot      = errmat3d.errmat3d(err_z_phot_file)
errmat_z_compt     = errmat3d.errmat3d(err_z_compt_file)
errmat_t_th_phot0  = errmat.errmat(err_t_th_phot_file0)
errmat_t_th_compt0 = errmat.errmat(err_t_th_compt_file0)
errmat_t_th_phot1  = errmat.errmat(err_t_th_phot_file1)
errmat_t_th_compt1 = errmat.errmat(err_t_th_compt_file1)
errmat_t_th_phot2  = errmat.errmat(err_t_th_phot_file2)
errmat_t_th_compt2 = errmat.errmat(err_t_th_compt_file2)


for file_number in range(start, start+numb_of_files):

    sim_file  = folder + f'/full_body_phantom.{file_number}.pet.h5'
    out_file0 = folder + f'/fastsim_tof_thr_charge/full_body_phantom_reco_thr0.5pes.{file_number}.h5'
    out_file1 = folder + f'/fastsim_tof_thr_charge/full_body_phantom_reco_thr1.0pes.{file_number}.h5'
    out_file2 = folder + f'/fastsim_tof_thr_charge/full_body_phantom_reco_thr1.5pes.{file_number}.h5'

    try:
        particles = mcio.load_mcparticles(sim_file)
    except:
        print(f'File {sim_file} not found!')
        continue
    hits   = mcio.load_mchits(sim_file)

    events = particles.event_id.unique()

    reco = pd.DataFrame(columns=['event_id',
                                 'true_energy',
                                 'true_r1',
                                 'true_phi1',
                                 'true_z1',
                                 'true_t1',
                                 'true_r2',
                                 'true_phi2',
                                 'true_z2',
                                 'true_t2',
                                 'phot_like1',
                                 'phot_like2',
                                 'reco_r1',
                                 'reco_phi1',
                                 'reco_z1',
                                 'reco_t1',
                                 'reco_r2',
                                 'reco_phi2',
                                 'reco_z2',
                                 'reco_t2'])

    for evt in events:

        evt_df0 = fmc.simulate_reco_event(evt, hits, particles, errmat_r_phot,
                                          errmat_phi_phot, errmat_z_phot, errmat_t_th_phot0, errmat_r_compt,
                                          errmat_phi_compt, errmat_z_compt, errmat_t_th_compt0, 0.95)
        reco0 = pd.concat([reco, evt_df0])

        evt_df1 = fmc.simulate_reco_event(evt, hits, particles, errmat_r_phot,
                                          errmat_phi_phot, errmat_z_phot, errmat_t_th_phot1, errmat_r_compt,
                                          errmat_phi_compt, errmat_z_compt, errmat_t_th_compt1, 0.95)
        reco1 = pd.concat([reco, evt_df1])

        evt_df1 = fmc.simulate_reco_event(evt, hits, particles, errmat_r_phot,
                                          errmat_phi_phot, errmat_z_phot, errmat_t_th_phot2, errmat_r_compt,
                                          errmat_phi_compt, errmat_z_compt, errmat_t_th_compt2, 0.95)
        reco1 = pd.concat([reco, evt_df1])


    store = pd.HDFStore(out_file0, "w", complib=str("zlib"), complevel=4)
    store.put('reco', reco0, format='table', data_columns=True)
    store.close()

    store = pd.HDFStore(out_file1, "w", complib=str("zlib"), complevel=4)
    store.put('reco', reco1, format='table', data_columns=True)
    store.close()

    store = pd.HDFStore(out_file2, "w", complib=str("zlib"), complevel=4)
    store.put('reco', reco2, format='table', data_columns=True)
    store.close()