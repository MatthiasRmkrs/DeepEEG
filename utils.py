!pip install mne
from mne import pick_types, viz, io, Epochs creat_info
from mne import channels, find_events, concatenate_raws
from mne import read_evokeds
from mne.time_frequency import tfr_morlet
from mne.io import RawArray
from mne.channels import read_montage

import pandas as pd
pd.options.display.max_columns = None
pd.options.display.precision = 4

import numpy as np
from numpy import genfromtxt

from collections import OrderedDict

import matplotlib.pyplot as plt
%matplotlib inline
plt.rcParams["figure.figsize"] = (12,12)

import keras
from keras import regularizers
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Activation, Input
from keras.layers import Flatten, Conv2D, MaxPooling2D, LSTM
from keras.callbacks import TensorBoard

from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight

import os
from glob import glob




#find the factors of a number |to add extra dimension for CNN|
def factors(n):
      return [i for i in range(1, n + 1) if not n%i]

#load in recorder data files
def load_data(filename,data_type='muse',plot_sensors=True,plot_raw=True,plot_raw_psd=True,stim_channel=False, ):  
 

    #load .vhdr files from brain vision recorder
    raw = io.read_raw_brainvision(filename, 
                            montage='standard_1020', 
                            eog=('HEOG', 'VEOG'), 
                            preload=True,stim_channel=stim_channel)

    #set sampling rate
    sfreq = raw.info['sfreq']
    print('Sampling Rate = ' + str(sfreq))

    #load channel locations
    print('Loading Channel Locations')
    if plot_sensors:
      raw.plot_sensors(show_names='True')

    ##Plot raw data
    if plot_raw:
      raw.plot(n_channels=16, block=True)

     #plot raw psd 
    if plot_raw_psd:
      raw.plot_psd(fmin=.1, fmax=100 ) 
  
    return raw, sfreq


#from eeg-notebooks
def load_muse_csv_as_raw(filename, sfreq=256., ch_ind=[0, 1, 2, 3],
                         stim_ind=5, replace_ch_names=None, verbose=1):
    """Load CSV files into a Raw object.

    Args:
        filename (str or list): path or paths to CSV files to load

    Keyword Args:
        subject_nb (int or str): subject number. If 'all', load all
            subjects.
        session_nb (int or str): session number. If 'all', load all
            sessions.
        sfreq (float): EEG sampling frequency
        ch_ind (list): indices of the EEG channels to keep
        stim_ind (int): index of the stim channel
        replace_ch_names (dict or None): dictionary containing a mapping to
            rename channels. Useful when an external electrode was used.

    Returns:
        (mne.io.array.array.RawArray): loaded EEG
    """

    n_channel = len(ch_ind)

    raw = []
    for fname in filename:
        # read the file
        data = pd.read_csv(fname, index_col=0)

        # name of each channels
        ch_names = list(data.columns)[0:n_channel] + ['Stim']

        if replace_ch_names is not None:
            ch_names = [c if c not in replace_ch_names.keys()
                        else replace_ch_names[c] for c in ch_names]

        # type of each channels
        ch_types = ['eeg'] * n_channel + ['stim']
        montage = read_montage('standard_1005')

        # get data and exclude Aux channel
        data = data.values[:, ch_ind + [stim_ind]].T

        # convert in Volts (from uVolts)
        data[:-1] *= 1e-6

        # create MNE object
        info = create_info(ch_names=ch_names, ch_types=ch_types,
                           sfreq=sfreq, montage=montage, verbose=verbose)
        raw.append(RawArray(data=data, info=info, verbose=verbose))

    # concatenate all raw objects
    raws = concatenate_raws(raw, verbose=verbose)

    return raws
  
#from eeg-notebooks load_data
def muse_load_data(data_dir, subject_nb=1, session_nb=1, sfreq=256.,
              ch_ind=[0, 1, 2, 3], stim_ind=5, replace_ch_names=None, verbose=1):
    """Load CSV files from the /data directory into a Raw object.

    Args:
        data_dir (str): directory inside /data that contains the
            CSV files to load, e.g., 'auditory/P300'

    Keyword Args:
        subject_nb (int or str): subject number. If 'all', load all
            subjects.
        session_nb (int or str): session number. If 'all', load all
            sessions.
        sfreq (float): EEG sampling frequency
        ch_ind (list): indices of the EEG channels to keep
        stim_ind (int): index of the stim channel
        replace_ch_names (dict or None): dictionary containing a mapping to
            rename channels. Useful when an external electrode was used.

    Returns:
        (mne.io.array.array.RawArray): loaded EEG
    """


    if subject_nb == 'all':
        subject_nb = '*'
    if session_nb == 'all':
        session_nb = '*'

    data_path = os.path.join(
            'eeg-notebooks/data', data_dir,
            'subject{}/session{}/*.csv'.format(subject_nb, session_nb))
    fnames = glob(data_path)

    return load_muse_csv_as_raw(fnames, sfreq=sfreq, ch_ind=ch_ind,
                                stim_ind=stim_ind,
                                replace_ch_names=replace_ch_names, verbose=verbose)





##Setup TensorFlow
#last part not working (curl)
#def SetupTensorFlow():
  #install ngork for tensorflow viz
  #!wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
  #!unzip ngrok-stable-linux-amd64.zip
  #import os
  ##run tensorboard
  #LOG_DIR = './log'
  #get_ipython().system_raw(
  #    'tensorboard --logdir {} --host 0.0.0.0 --port 6007 &'
  #    .format(LOG_DIR)
  #)

  #run ngork
  #get_ipython().system_raw('./ngrok http 6007 &')

  #get url
  #os.system(curl -s http://localhost:4040/api/tunnels | python3 -c \
  #    "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])")

  