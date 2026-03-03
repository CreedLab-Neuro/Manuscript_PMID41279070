#IMPORTING LIBRARIES:
#these are libraries used for ALL plotting functions in FED3 Viz,
#so some may be redundant!

import datetime
import datetime as dt
import os

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from difflib import SequenceMatcher
from matplotlib.ticker import AutoMinorLocator
from pandas.plotting import register_matplotlib_converters
from scipy import stats

register_matplotlib_converters()

#CODE TO LOAD FED DATA FROM A DIRECTORY

class FED3_File():
    """Class used by FED3 Viz to .csv and .xlsx FED3 Files"""
    def __init__(self,directory):
        """
        Reads FED3 data, adds variables, and assigns attributes
        based on recording.  Will fail if there are no logged rows.

        Parameters
        ----------
        directory : str
            Path to the FED3 file (.csv or .xlsx)

        Raises
        ------
        Exception
            An Exception is raised when reading the file fails; generally
            occurs if the file is not tabular or if it is missing the
            FED3 "MM:DD:YYYY hh:mm:ss" column.
        """
        self.directory = os.path.abspath(directory).replace('\\','/')
        self.fixed_names = ['Device_Number',
                            'Battery_Voltage',
                            'Motor_Turns',
                            'Session_Type',
                            'Event',
                            'Active_Poke',
                            'Left_Poke_Count',
                            'Right_Poke_Count',
                            'Pellet_Count',
                            'Retrieval_Time',]
        self.needed_names = ['Pellet_Count',
                             'Left_Poke_Count',
                             'Right_Poke_Count',]

        self.basename = os.path.basename(directory)
        splitext = os.path.splitext(self.basename)
        self.filename = splitext[0]
        self.extension = splitext[1].lower()
        self.foreign_columns=[]
        try:
            read_opts = {'.csv':pd.read_csv, '.xlsx':pd.read_excel}
            func = read_opts[self.extension]
            self.data = func(directory,
                                parse_dates=True,
                                index_col='MM:DD:YYYY hh:mm:ss')
            for column in self.data.columns:
                for name in self.fixed_names:
                    likeness = SequenceMatcher(a=column, b=name).ratio()
                    if likeness > 0.85:
                        self.data.rename(columns={column:name}, inplace=True)
                        break
                    self.foreign_columns.append(column)
        except Exception as e:
            raise e
        self.missing_columns = [name for name in self.needed_names if
                                name not in self.data.columns]
        self.events = len(self.data.index)
        self.end_time = pd.Timestamp(self.data.index.values[-1])
        self.start_time = pd.Timestamp(self.data.index.values[0])
        self.duration = self.end_time-self.start_time
        self.add_elapsed_time()
        self.add_binary_pellet_count()
        self.reassign_events()
        self.add_interpellet_intervals()
        self.add_correct_pokes()
        self.handle_retrieval_time()
        self.handle_poke_time()
        self.mode = self.determine_mode()
        self.group = []

    def __repr__(self):
        """Shows the directory used to make the file."""
        return 'FED3_File("' + self.directory + '")'

    def add_elapsed_time(self):
        """pandas Timedelta relative to starting point for each row.
        Stored in new Elapsed_Time column"""
        events = self.data.index
        elapsed_times = [event - self.start_time for event in events]
        self.data['Elapsed_Time'] = elapsed_times

    def add_binary_pellet_count(self):
        """Convert cumulative pellet count to binary value for each row.
        Stored in new Binary_Pellets column."""
        if "Pellet_Count" not in self.data.columns:
            self.data['Binary_Pellets'] = np.nan
            return
        self.data['Binary_Pellets'] = self.data['Pellet_Count'].diff()
        pos = self.data.columns.get_loc('Binary_Pellets')
        pos2 = self.data.columns.get_loc('Pellet_Count')
        self.data.iloc[0,pos] = self.data.iloc[0, pos2]

    def add_interpellet_intervals(self):
        """Compute time between each pellet retrieval.
        Stored in new Interpellet_Intervals column.  When loading
        concatenated files (from load.fed_concat()), first IPIs for
        the concatenated files are skipped."""
        inter_pellet = np.array(np.full(len(self.data.index),np.nan))
        c=0
        for i,val in enumerate(self.data['Binary_Pellets']):
            if val == 1:
                if c == 0:
                    c = i
                else:
                    inter_pellet[i] = (self.data.index[i] -
                                       self.data.index[c]).total_seconds()/60
                    c = i
        self.data['Interpellet_Intervals'] = inter_pellet
        if 'Concat_#' in self.data.columns:
            if not any(self.data.index.duplicated()): #this can't do duplicate indexes
                #thanks to this answer https://stackoverflow.com/a/47115490/13386979
                dropped = self.data.dropna(subset=['Interpellet_Intervals'])
                pos = dropped.index.to_series().groupby(self.data['Concat_#']).first()
                self.data.loc[pos[1:],'Interpellet_Intervals'] = np.nan

    def add_correct_pokes(self):
        """Compute whether each poke was correct or not.  This process returns
        numpy NaN if files are in the older format (only pellets logged).  Stored
        in a new Correct_Poke column, also creates Binary_Left_Pokes and
        Binary_Right_Pokes."""
        df = self.data
        a = 'Left_Poke_Count' not in df.columns
        b = 'Right_Poke_Count' not in df.columns
        if any((a, b)):
            df['Correct_Poke'] = np.nan
            return
        df['Binary_Left_Pokes']  = df['Left_Poke_Count'].diff()
        df['Binary_Right_Pokes'] = df['Right_Poke_Count'].diff()
        df.iloc[0,df.columns.get_loc('Binary_Left_Pokes')] = df['Left_Poke_Count'][0]
        df.iloc[0,df.columns.get_loc('Binary_Right_Pokes')] = df['Right_Poke_Count'][0]
        df['Correct_Poke'] = df.apply(lambda row: self.is_correct_poke(row), axis=1)
        df['Correct_Poke'] = df['Correct_Poke'].astype(float)

    def is_correct_poke(self,row):
        """For each poke event against the active poke column to verify correctness."""
        try:
            if row['Event'] == 'Poke':
                return (row['Active_Poke'] == 'Left' and row['Binary_Left_Pokes'] == 1 or
                        row['Active_Poke'] == 'Right' and row['Binary_Right_Pokes'] )
            else:
                return np.nan
        except:
            return np.nan

    def determine_mode(self):
        """Find the recording mode of the file.  Returns the mode as a string."""
        mode = 'Unknown'
        column = pd.Series()
        for name in ['FR','FR_Ratio',' FR_Ratio','Mode','Session_Type']:
            if name in self.data.columns:
                column = self.data[name]
        if not column.empty:
            if all(isinstance(i,int) for i in column):
                if len(set(column)) == 1:
                    mode = 'FR' + str(column[0])
                else:
                    mode = 'PR'
            elif 'PR' in column[0]:
                mode = 'PR'
            else:
                mode = str(column[0])
        return mode

    def handle_retrieval_time(self):
        """Convert the Retrieval_Time column to deal with non-numeric entries.
        Currently, all are converted to np.nan.  No longer tries to convert
        NaN values to 0 (see commented out section)"""
        if 'Retrieval_Time' not in self.data.columns:
            self.data['Retrieval_Time'] = np.nan
            return
        self.data['Retrieval_Time'] = pd.to_numeric(self.data['Retrieval_Time'],errors='coerce')
        # try:
        #     self.data.loc[(self.data['Event'] == 'Pellet') &
        #                   pd.isnull(self.data['Retrieval_Time']), 'Retrieval_Time'] = 0
        # except:
        #     pass

    def reassign_events(self):
        """Reassign the "Event" column based on changes in the pellet and poke
        counts.  Catches some errors with improper event logging.  Weekly tries
        and exits if errors encountered."""
        try:
            events = ["Pellet" if v else 'Poke' for v in self.data['Binary_Pellets']]
            self.data['Event'] = events
        except:
            pass

    def handle_poke_time(self):
        """Creates a dummy poke time column if one hasn't been created (newer
        FED feature as of Fall 2020."""
        if 'Poke_Time' not in self.data.columns:
            self.data['Poke_Time'] = np.nan

#HELPER FUNCTIONS (CIRCADIAN PLOTS)

def resample_get_yvals(df, value, retrieval_threshold=None):
    """
    Function for passing to the apply() method of pandas Resampler or
    DataFrameGroupBy object.  Computes an output for each bin of binned
    FED3 data.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame of FED3 data (loaded by FED3_Viz.load.FED3_File)
    value : str
        String signalling what output to compute for each bin.  Options are:
        'pellets','retrieval time','interpellet intervals','correct pokes',
        'errors','correct pokes (%)','errors (%)','poke bias (correct - error)',
        'poke bias (left - right)', & 'poke bias (correct %)'

    Returns
    -------
    output : float or int
        Computed value (for each bin of df)
    """
    possible = ['pellets','retrieval time','interpellet intervals',
                'correct pokes','errors','correct pokes (%)','errors (%)',
                'poke bias (correct - error)', 'poke bias (left - right)',
                'poke bias (correct %)',]
    assert value in possible, 'Value not understood by daynight plot: ' + value
    #in use
    if value == 'poke bias (correct %)':
        value = 'correct pokes (%)'
    if value == 'pellets':
        output = df['Binary_Pellets'].sum()
    elif value == 'retrieval time':
        output = df['Retrieval_Time'].copy()
        if retrieval_threshold:
            output.loc[output>=retrieval_threshold] = np.nan
        output = output.mean()
    elif value == 'interpellet intervals':
        output = df['Interpellet_Intervals'].mean()
    elif value == 'correct pokes':
        output = list(df['Correct_Poke']).count(True)
    elif value == 'errors':
        output = list(df['Correct_Poke']).count(False)
    elif value == 'correct pokes (%)':
        try:
            correct = (list(df['Correct_Poke']).count(True))
            incorrect = (list(df['Correct_Poke']).count(False))
            output = correct/(correct+incorrect) * 100
        except ZeroDivisionError:
            output = np.nan
    elif value == 'errors (%)':
        try:
            correct = (list(df['Correct_Poke']).count(True))
            incorrect = (list(df['Correct_Poke']).count(False))
            output = incorrect/(correct+incorrect)*100
        except ZeroDivisionError:
            output = np.nan
    #outdated
    elif value == 'poke bias (correct - error)':
        output = list(df['Correct_Poke']).count(True) - list(df['Correct_Poke']).count(False)
    elif value == 'poke bias (left - right)':
        output = df['Binary_Left_Pokes'].sum() - df['Binary_Right_Pokes'].sum()
    return output


#PLOTTING FUNCTION:

def line_chronogram(FEDs, groups, circ_value, circ_error, circ_show_indvl, shade_dark,
                    lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Make a line plot showing the average 24 hour cycle of a value
    for Grouped devices.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    circ_value : str
        String value pointing to a variable to plot; any string accepted
        by resample_get_yvals()
    circ_error : str
        What error bars to show ("SEM", "STD", or "None")
    circ_show_indvl : bool
        Whether to show individual files as their own lines; if True, error
        bars will not be shown.
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to daynight_plot()'
    if circ_show_indvl:
        circ_error = "None"
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, group in enumerate(groups):
        group_vals = []
        for FED in FEDs:
            if group in FED.group:
                df = FED.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                byhour = df.groupby([df.index.hour])
                byhour = byhour.apply(resample_get_yvals,circ_value,retrieval_threshold)
                byhourday = df.groupby([df.index.hour,df.index.date])
                num_days_by_hour = byhourday.sum().index.get_level_values(0).value_counts()
                byhour = byhour.divide(num_days_by_hour, axis=0)
                new_index = list(range(lights_on, 24)) + list(range(0,lights_on))
                reindexed = byhour.reindex(new_index)
                reindexed.index.name = 'hour'
                if circ_value in ['pellets', 'correct pokes','errors']:
                    reindexed = reindexed.fillna(0)
                y = reindexed
                x = range(0,24)
                if circ_show_indvl:
                    ax.plot(x,y,color=colors[i],alpha=.3,linewidth=.8)
                group_vals.append(y)
        group_mean = np.nanmean(group_vals, axis=0)
        label = group
        error_shade = np.nan
        if circ_error == "SEM":
            error_shade = stats.sem(group_vals, axis=0,nan_policy='omit')
            label += ' (±' + circ_error + ')'
        elif circ_error == 'STD':
            error_shade = np.nanstd(group_vals, axis=0)
            label += ' (±' + circ_error + ')'
        if circ_show_indvl:
            error_shade = np.nan
        if "%" in circ_value:
            ax.set_ylim(0,100)
        x = range(24)
        y = group_mean
        ax.plot(x,y,color=colors[i], label=label)
        ax.fill_between(x, y-error_shade, y+error_shade, color=colors[i],
                        alpha=.3)
    ax.set_xlabel('Hours (since start of light cycle)')
    ax.set_xticks([0,6,12,18,24])
    ax.set_ylabel(circ_value)
    ax.set_title('Chronogram')
    if shade_dark:
        off = new_index.index(lights_off)
        ax.axvspan(off,24,color='gray',alpha=.2,zorder=0,label='lights off')
    ax.legend(bbox_to_anchor=(1,1),loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

#ARGUMENT VALUES:

fed1 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED001_091823_04_MSHAM.CSV")
fed2 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED002_091823_00_M_SHAM.CSV")
fed3 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED003_091823_05_MSNI.CSV")
fed4 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED004_091823_04_MSNI.CSV")
fed5 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED005_091823_05_FSHAM.CSV")
fed6 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED006_091823_07_FSHAM.CSV")
fed7 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED007_091823_00_FSNI.CSV")
fed8 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_HC_Melox/YHC_Melox_FED008_091823_02_FSNI.CSV")
fed9 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_2SecBandit/JMT_2sB_FED014_091123_00_MSNI.CSV")
fed10 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_2SecBandit/JMT_FED022_091123_01_M_SNI.CSV")
fed11 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED000_030623_01_FSNI.CSV")
fed12 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED000_030923_00_FSNI.CSV")
fed13 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED000_032523_01_FSHAM.CSV")
fed14 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED000_062123_01_MSNI.CSV")
fed15 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED001_030623_01_FSNI.CSV")
fed16 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED001_032523_01_FSHAM.CSV")
fed17 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED001_052023_01_MSNI.CSV")
fed18 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED001_053023_04_FSNI.CSV")
fed19 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED001_091123_02_FSHAM.CSV")
fed20 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED002_030623_01_MSNI.CSV")
fed21 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED002_032523_01_FSHAM.CSV")
fed22 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED002_052023_01_MSHAM.CSV")
fed23 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED002_091123_02_FSHAM.CSV")
fed24 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED002_092623_03_MSNI.CSV")
fed25 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED002_093023_00_MSNI.CSV")
fed26 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED002_100523_00_MSNI.CSV")
fed27 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED003_030623_01_MSHAM.CSV")
fed28 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED003_031123_00_MSHAM.CSV")
fed29 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED003_032523_01_FSNI.CSV")
fed30 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED003_052023_01_MSHAM.CSV")
fed31 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED003_091123_00_FSHAM.CSV")
fed32 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED003_092623_02_MSNI.CSV")
fed33 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED004_030623_01_MSHAM.CSV")
fed34 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED004_032523_01_FSNI.CSV")
fed35 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED004_052223_01_MSNI.CSV")
fed36 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED004_091123_01_FSHAM.CSV")
fed37 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED005_030923_00_MSHAM.CSV")
fed38 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED005_090723_Concat_MSNI.csv")
fed39 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED005_091223_04_FSHAM.CSV")
fed40 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED006_052923_01_FSHAM.CSV")
fed41 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED006_091123_01_FSNI.CSV")
fed42 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED007_091123_01_FSNI.CSV")
fed43 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED008_091123_01_FSNI.CSV")
fed44 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED009_091123_01_FSNI.CSV")
fed45 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED010_091123_01_FSNI.CSV")
fed46 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED011_091223_00_MSHAM.CSV")
fed47 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED012_091223_00_MSHAM.CSV")
fed48 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED015_091123_00_MSNI.CSV")
fed49 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED016_091123_00_MSNI.CSV")
fed50 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED018_091123_00_MSNI.CSV")
fed51 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED019_091223_05_MSHAM.CSV")
fed52 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED021_091223_00_MSHAM.CSV")
fed53 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED024_091223_00_Concat_MSNI.csv")
fed54 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_All/FED027_091223_00_MSHAM.CSV")
fed55 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED000_060524_01_F_SHAM.CSV")
fed56 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED002_060524_01_F_SNI.CSV")
fed57 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED003_060524_01_F_SNI.CSV")
fed58 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED004_060524_01_F_SNI.CSV")
fed59 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED005_060524_01_F_SNI.CSV")
fed60 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED006_060524_01_F_SNI.CSV")
fed61 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED010_060524_01_F_SHAM.CSV")
fed62 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED011_011001_41_F_SHAM.CSV")
fed63 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED012_060524_02_F_SHAM.CSV")
fed64 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED016_060524_01_F_SHAM.CSV")
fed65 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED027_060524_01_M_SNI.CSV")
fed66 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_JMT_ChronicSNI_PR/JMT_cPR_FED034_060524_01_M_SHAM.CSV")
fed67 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met1_FED001_031524_02_Initial.csv")
fed68 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met1_FED002_031524_03_Initial.csv")
fed69 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met1_FED003_031524_03_Initial.csv")
fed70 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met2_FED001_041224_02_Initial.csv")
fed71 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met2_FED002_041224_03_Initial.csv")
fed72 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met2_FED003_041224_03_Initial.csv")
fed73 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met2_FED013_041224_04_Initial.csv")
fed74 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_Ctrl_FR1_Met2_FED014_041224_00_Initial.csv")
fed75 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_SNI_FR1_Met1_FED007_031524_05_Initial.csv")
fed76 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_SNI_FR1_Met1_FED008_031624_02_Initial.csv")
fed77 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_SNI_FR1_Met2_FED007_041224_02_Initial.csv")
fed78 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_SNI_FR1_Met2_FED008_041224_02_Initial.csv")
fed79 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_SNI_FR1_Met2_FED009_041224_02_Initial.csv")
fed80 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_SNI_FR1_Met2_FED015_041224_02_Initial.csv")
fed81 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/F_SNI_FR1_Met2_FED016_041224_01_Initial.csv")
fed82 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_Ctrl_FR1_Met1_FED004_031524_05_Initial.csv")
fed83 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_Ctrl_FR1_Met1_FED005_031524_02_Initial.csv")
fed84 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_Ctrl_FR1_Met1_FED006_031524_04_Initial.csv")
fed85 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_Ctrl_FR1_Met2_FED004_041224_01_Initial.csv")
fed86 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_Ctrl_FR1_Met2_FED005_041224_01_Initial.csv")
fed87 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_Ctrl_FR1_Met2_FED006_041224_01_Initial.csv")
fed88 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_SNI_FR1_Met1_FED010_031524_04_Initial.csv")
fed89 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_SNI_FR1_Met1_FED011_031524_01_Initial.csv")
fed90 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_SNI_FR1_Met1_FED011_031824_03_Initial.csv")
fed91 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_SNI_FR1_Met1_FED012_031524_03_Initial.csv")
fed92 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_SNI_FR1_Met2_FED010_041224_02_Initial.csv")
fed93 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_SNI_FR1_Met2_FED011_041224_02_Initial.csv")
fed94 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_MetPre/M_SNI_FR1_Met2_FED012_041224_06_Initial.csv")
fed95 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_CE1r_FED004_020821_02_FSHAM.CSV")
fed96 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_F_FED005_082123_02.CSV")
fed97 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_F_FED005_090623_concat_00.CSV")
fed98 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_F_FED006_082123_02.CSV")
fed99 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_F_FED006_090623_01.CSV")
fed100 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED001_082123_03.CSV")
fed101 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED001_090523_01.CSV")
fed102 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED002_082223_01_concat_00.CSV")
fed103 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED002_090523_00.CSV")
fed104 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED003_082123_02.CSV")
fed105 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED003_090523_02.CSV")
fed106 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED004_082123_03.CSV")
fed107 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/Ctrl_M_FED004_090523_02.CSV")
fed108 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/FED004_013021_00_MSNI.CSV")
fed109 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/FED004_020821_02_MSNI.CSV")
fed110 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/FED005_020821_03_FSNI.CSV")
fed111 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/FED006_020221_02_FSNI.CSV")
fed112 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_Ctrl_M_FED001_072821_00.CSV")
fed113 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_Ctrl_M_FED002_072823_03.CSV")
fed114 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_Ctrl_M_FED003_073123_02.CSV")
fed115 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_Ctrl_M_FED004_072823_03.CSV")
fed116 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_SNI_M_FED005_072823_03.CSV")
fed117 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_SNI_M_FED006_072823_03.CSV")
fed118 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_SNI_M_FED007_072823_03.CSV")
fed119 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/rPR_SNI_M_FED008_072823_03.CSV")
fed120 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/SNI_M_FED007_082123_02.CSV")
fed121 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/FR1_YHC_rPr/SNI_M_FED008_082123_03.CSV")
fed122 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_Halo/YHC_Hal_FED001_042123_04_F_SHAM.CSV")
fed123 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_Halo/YHC_Hal_FED002_042123_04_F_SHAM.CSV")
fed124 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_Halo/YHC_Hal_FED003_042123_04_FSHAM.CSV")
fed125 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_Halo/YHC_Hal_FED004_042123_05_F_SHAM.CSV")
fed126 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_Halo/YHC_Hal_FED007_042123_02_MSHAM.CSV")
fed127 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_Halo/YHC_Hal_FED008_042123_01_M_SHAM.CSV")
fed128 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_Ctrl_F_CE6_FED000_041221_00.CSV")
fed129 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_Ctrl_F_CE6_FED003_041221_00.CSV")
fed130 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_Ctrl_F_CE6_FED005_041221_03.CSV")
fed131 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_Ctrl_F_CE7_FED001_042221_01.CSV")
fed132 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_SNI_F_CE3r2_FED003_033121_concat_00.CSV")
fed133 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_SNI_F_CE3r2_FED005_033121_01.CSV")
fed134 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_SNI_F_CE3r2_FED006_033121_04.CSV")
fed135 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_SNI_F_CE6_FED006_041221_00.CSV")
fed136 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_SNI_F_CE6_FED022_040621_03.CSV")
fed137 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_SNI_F_CE7_FED002_042221_03.CSV")
fed138 = FED3_File("C:/Users/meagh/Box/CreedLabBoxDrive/Jeremy/SNI_Dopamine_Paper/Figure1_SNIBehavior/FED_FR1/YHC_RevNeu/RevNeu_SNI_F_CE7_FED003_042221_02.CSV")

FEDs = [fed1, fed2, fed3, fed4, fed5, fed6, fed7, fed8, fed9, fed10, fed11, fed12, fed13, fed14, fed15, fed16, fed17, fed18, fed19, fed20, fed21, fed22, fed23, fed24, fed25, fed26, fed27, fed28, fed29, fed30, fed31, fed32, fed33, fed34, fed35, fed36, fed37, fed38, fed39, fed40, fed41, fed42, fed43, fed44, fed45, fed46, fed47, fed48, fed49, fed50, fed51, fed52, fed53, fed54, fed55, fed56, fed57, fed58, fed59, fed60, fed61, fed62, fed63, fed64, fed65, fed66, fed67, fed68, fed69, fed70, fed71, fed72, fed73, fed74, fed75, fed76, fed77, fed78, fed79, fed80, fed81, fed82, fed83, fed84, fed85, fed86, fed87, fed88, fed89, fed90, fed91, fed92, fed93, fed94, fed95, fed96, fed97, fed98, fed99, fed100, fed101, fed102, fed103, fed104, fed105, fed106, fed107, fed108, fed109, fed110, fed111, fed112, fed113, fed114, fed115, fed116, fed117, fed118, fed119, fed120, fed121, fed122, fed123, fed124, fed125, fed126, fed127, fed128, fed129, fed130, fed131, fed132, fed133, fed134, fed135, fed136, fed137, fed138]

groups = ['SHAM', 'SNI']

fed1.group.append("SHAM")
fed2.group.append("SHAM")
fed3.group.append("SNI")
fed4.group.append("SNI")
fed5.group.append("SHAM")
fed6.group.append("SHAM")
fed7.group.append("SNI")
fed8.group.append("SNI")
fed9.group.append("SNI")
fed10.group.append("SNI")
fed11.group.append("SNI")
fed12.group.append("SNI")
fed13.group.append("SHAM")
fed14.group.append("SNI")
fed15.group.append("SNI")
fed16.group.append("SHAM")
fed17.group.append("SNI")
fed18.group.append("SNI")
fed19.group.append("SHAM")
fed20.group.append("SNI")
fed21.group.append("SHAM")
fed22.group.append("SHAM")
fed23.group.append("SHAM")
fed24.group.append("SNI")
fed25.group.append("SNI")
fed26.group.append("SNI")
fed27.group.append("SHAM")
fed28.group.append("SHAM")
fed29.group.append("SNI")
fed30.group.append("SHAM")
fed31.group.append("SHAM")
fed32.group.append("SNI")
fed33.group.append("SHAM")
fed34.group.append("SNI")
fed35.group.append("SNI")
fed36.group.append("SHAM")
fed37.group.append("SHAM")
fed38.group.append("SNI")
fed39.group.append("SHAM")
fed40.group.append("SHAM")
fed41.group.append("SNI")
fed42.group.append("SNI")
fed43.group.append("SNI")
fed44.group.append("SNI")
fed45.group.append("SNI")
fed46.group.append("SHAM")
fed47.group.append("SHAM")
fed48.group.append("SNI")
fed49.group.append("SNI")
fed50.group.append("SNI")
fed51.group.append("SHAM")
fed52.group.append("SHAM")
fed53.group.append("SNI")
fed54.group.append("SHAM")
fed55.group.append("SHAM")
fed56.group.append("SNI")
fed57.group.append("SNI")
fed58.group.append("SNI")
fed59.group.append("SNI")
fed60.group.append("SNI")
fed61.group.append("SHAM")
fed62.group.append("SHAM")
fed63.group.append("SHAM")
fed64.group.append("SHAM")
fed65.group.append("SNI")
fed66.group.append("SHAM")
fed67.group.append("SHAM")
fed68.group.append("SHAM")
fed69.group.append("SHAM")
fed70.group.append("SHAM")
fed71.group.append("SHAM")
fed72.group.append("SHAM")
fed73.group.append("SHAM")
fed74.group.append("SHAM")
fed75.group.append("SNI")
fed76.group.append("SNI")
fed77.group.append("SNI")
fed78.group.append("SNI")
fed79.group.append("SNI")
fed80.group.append("SNI")
fed81.group.append("SNI")
fed82.group.append("SHAM")
fed83.group.append("SHAM")
fed84.group.append("SHAM")
fed85.group.append("SHAM")
fed86.group.append("SHAM")
fed87.group.append("SHAM")
fed88.group.append("SNI")
fed89.group.append("SNI")
fed90.group.append("SNI")
fed91.group.append("SNI")
fed92.group.append("SNI")
fed93.group.append("SNI")
fed94.group.append("SNI")
fed95.group.append("SHAM")
fed96.group.append("SHAM")
fed97.group.append("SHAM")
fed98.group.append("SHAM")
fed99.group.append("SHAM")
fed100.group.append("SHAM")
fed101.group.append("SHAM")
fed102.group.append("SHAM")
fed103.group.append("SHAM")
fed104.group.append("SHAM")
fed105.group.append("SHAM")
fed106.group.append("SHAM")
fed107.group.append("SHAM")
fed108.group.append("SNI")
fed109.group.append("SNI")
fed110.group.append("SNI")
fed111.group.append("SNI")
fed112.group.append("SHAM")
fed113.group.append("SHAM")
fed114.group.append("SHAM")
fed115.group.append("SHAM")
fed116.group.append("SNI")
fed117.group.append("SNI")
fed118.group.append("SNI")
fed119.group.append("SNI")
fed120.group.append("SNI")
fed121.group.append("SNI")
fed122.group.append("SHAM")
fed123.group.append("SHAM")
fed124.group.append("SHAM")
fed125.group.append("SHAM")
fed126.group.append("SHAM")
fed127.group.append("SHAM")
fed128.group.append("SHAM")
fed129.group.append("SHAM")
fed130.group.append("SHAM")
fed131.group.append("SHAM")
fed132.group.append("SNI")
fed133.group.append("SNI")
fed134.group.append("SNI")
fed135.group.append("SNI")
fed136.group.append("SNI")
fed137.group.append("SNI")
fed138.group.append("SNI")

circ_value = "pellets"
circ_error = "SEM"
circ_show_indvl = False
shade_dark = True
lights_on = 7
lights_off = 19

#CALLING THE FUNCTION

plot = line_chronogram(FEDs, groups, circ_value, circ_error, circ_show_indvl, shade_dark, lights_on, lights_off)