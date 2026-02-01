#
# This file is part of wytham-logparser
# (https://github.com/I-Bouros/wytham-logparser.git)
# which is released under the BSD 3-clause license. See accompanying LICENSE.md
# for copyright notice and full license details.
#
"""Processing script for the logger data from [1]_ .

It complies the number of realised contacts recorded between certain dates into
a unified framework.

References
----------
.. [1]

"""

import os
import pandas as pd
import time
from time import mktime
import datetime
import glob


def read_full_logger_data(log_file: str):
    """
    Parses the txt document containing the full logger data
    and retain only mouse contact events.

    Parameters
    ----------
    log_file : str
        The name of the logger data file used.

    Returns
    -------
    pandas.Dataframe
        Dataframe of the recognised trigger event data.

    """
    # Extract unprocessed logger data from the given logger file
    data = pd.read_csv(
        os.path.join(os.path.dirname(__file__), log_file),
        header=1)

    # Retain only those entries constituting recognised trigger events by a
    # chipped rodent, marked as motion_det 3
    contact_data = data[data['motion_det'] == 3]

    return contact_data


def process_logger_data(
        data: pd.DataFrame,
        tag_data: pd.DataFrame,
        trap_data: pd.DataFrame,
        different_tag_list: list):
    """
    Computes the daily total rainfall between the given dates.

    Parameters
    ----------
    data : pandas.Dataframe
        Dataframe of the recognised tag reading trigger events for a
        given trap.
    tag_data : pandas.Dataframe
        Dataframe of the tag ID for all tagged animals on the grid.
    trap_data : pandas.Dataframe
        Dataframe of the position on the grid of an given trap on any
        given day.
    different_tag_list : list
        List of known tags that are not part of the project.

    Returns
    -------
    pandas.Dataframe
        Processed total daily precipitation levels in a given region as
        a dataframe.

    """
    # Process times of triggers into a consistent datetime format
    data['Time'] = [process_dates(x) for x in data['date']]
    data = data.sort_values('Time')

    # Keep only those columns we need from the large logger data file
    data = data[['Time', 'LoggerID', 'TagID']]

    # Create empty dataframe with prescribed column names
    # This will be the trigger dataframe once filled
    triggers = pd.DataFrame(columns=[
        'time', 'LoggerPosition', 'RodentID',
        'RodentSpecies', 'RodentSex'])

    # For each unique time entry in the logger data ...
    for t in data['Time'].unique():
        # ... extract only those entries pertaining to that particular
        # time entry
        daily_data = data[data['Time'] == t]

        # If there are no error signals ...
        if find_rodent_id(tag_data, daily_data,
                          different_tag_list) != 'error':
            # ... identify the logger position of the trigger,
            # the rodent ID triggering the trap, its sex and species...
            newrow = pd.DataFrame([{
                'time': t,
                'LoggerPosition': find_trap_pos(trap_data, daily_data),
                'RodentID': find_rodent_id(tag_data, daily_data,
                                           different_tag_list)[0],
                'RodentSpecies': find_rodent_id(tag_data, daily_data,
                                                different_tag_list)[1],
                'RodentSex': find_rodent_id(tag_data, daily_data,
                                            different_tag_list)[2]
            }])
            # and save the details as a new entry in the empty trigger
            # dataframe we created above
            triggers = pd.concat([triggers, newrow])

    # Finally reshape the time entries into a readable format
    triggers['Time'] = [
        datetime.datetime.fromtimestamp(mktime(d))
        for d in triggers['time']]

    return triggers


def process_dates(date: str):
    """
    Processes dates into `datetime` format.

    Parameters
    ----------
    date : str
        Date (date/month/year hour:min:sec) as it appears in the data frame.

    Returns
    -------
    datetime.datetime
        Date processed into correct format.

    """
    # We split the date and time formats based on what each number in the
    # string pertains to
    struct = time.strptime(date, '%d/%m/%y %H:%M:%S')
    return struct


def find_trap_pos(trap_data: pd.DataFrame,
                  daily_data: pd.DataFrame):
    """
    Identifies the position of a given trap on the grid on a particular date
    given the trap ID.

    Parameters
    ----------
    trap_data : pandas.Dataframe
        Dataframe of the position on the grid of an given trap on any
        given day.
    daily_data : pandas.Dataframe
        Dataframe of the recognised tag reading trigger event for a
        given timepoint.

    Returns
    -------
    str
        Position of the trap on the grid on the specified date.
    """
    dates = []

    # We split the date and time formats based on what each number in the
    # string pertains to
    for date in trap_data['Date']:
        try:
            dates.append(time.strptime(date, '%d/%m/%Y'))
        except ValueError:
            dates.append(time.strptime(date, '%d/%m/%y'))
    # Add these reformatted dates and times as a separate column
    trap_data['Time'] = dates

    # Subset only those entries in the trap position dataframe matching the
    # logger ID at the given trigger event
    current_trap_all_positions = trap_data[
        trap_data['Logger_ID'] == daily_data['LoggerID'].values[0]]

    # Find where the current trap is positioned
    current_trap_all_positions['processed-date'] = [
        x[:3] for x in current_trap_all_positions['Time']]

    return current_trap_all_positions[
        current_trap_all_positions['processed-date'] >= daily_data[
            'Time'].values[0][:3]]['Grid_Cell'].iloc[0]


def find_rodent_id(tag_data: pd.DataFrame,
                   daily_data: pd.DataFrame,
                   different_tag_list: list):
    """
    Identifies the rodent based on the tag ID.

    Parameters
    ----------
    tag_data : pandas.Dataframe
        Dataframe of the tag ID for all tagged animals on the grid.
    daily_data : pandas.Dataframe
        Dataframe of the recognised tag reading trigger event for a
        given timepoint.
    different_tag_list : list
        List of known tags that are not part of the project.

    Returns
    -------
    list
        List of the ID, species and sex of the identified rodent.
    """
    # Find correct animal based on the multiple tags it can have
    if daily_data['TagID'].values[0][-6:] in tag_data['Tag1'].values:
        rodent = tag_data[
            (tag_data['Tag1'] == daily_data['TagID'].values[0][-6:])]
    elif daily_data['TagID'].values[0][-6:] in tag_data['Tag2'].values:
        rodent = tag_data[
            (tag_data['Tag2'] == daily_data['TagID'].values[0][-6:])]
    elif daily_data['TagID'].values[0][-6:] in tag_data['Tag3'].values:
        rodent = tag_data[
            (tag_data['Tag3'] == daily_data['TagID'].values[0][-6:])]
    elif daily_data['TagID'].values[0][-6:] in tag_data['Tag4'].values:
        rodent = tag_data[
            (tag_data['Tag4'] == daily_data['TagID'].values[0][-6:])]
    # If the tag is among the non-recongnised list, the code throws an error
    elif daily_data['TagID'].values[0][-6:] in different_tag_list:
        return 'error'

    # This will print the current Tag ID from the logger data
    print(daily_data['TagID'])

    return (rodent['Animal'].values[0], rodent['Species'].values[0],
            rodent['Sex'].values[0])


def main(list_log_file: list):
    """
    Combines the timelines of deviation percentages and baseline
    activity-specific contact matrices to get weekly, region-specific
    contact matrices.

    Parameters
    ----------
    list_log_file : list
        List of all the names of the logger data files used.

    Returns
    -------
    txt
        Processed file of all trigger events caused by recognised rodent tags
        across all traps and timepoints.

    """
    # Read all tag data and all date-specific trap positions
    all_tags = pd.read_csv(
        os.path.join(os.path.dirname(__file__),
                     '../logger-data/MouseIDTrappingData.csv'),
        header=0)

    # Read all possible trap positions based by logger ID and time
    trap_position = pd.read_csv(
        os.path.join(os.path.dirname(__file__),
                     '../logger-data/EWYT_Project_Logger_Movements.csv'),
        header=0)

    # Read list of known tags not part of the project
    different_tag_list = pd.read_csv(os.path.join(
            os.path.dirname(__file__),
            '../logger-data/DifferentTags.txt'),
            header=None).values.tolist()[0]

    # For each logger data file ...
    for log_file in list_log_file:
        # ... we read in the file
        contact_data = read_full_logger_data(log_file)

        # Rename the columns of interest to match our naming conventions
        contact_data = contact_data.rename(columns={
            'datetime': 'date',
            'LOGGER_ID': 'LoggerID',
            'Tag_ID': 'TagID'})

        # Keep only columns of interest
        contact_data = contact_data[['date', 'LoggerID', 'TagID']]

        # Process logger data to produce all recognised triggers dataframe
        triggers = process_logger_data(contact_data, all_tags, trap_position,
                                       different_tag_list)

        # Keep only columns of interest
        triggers = triggers[['Time', 'LoggerPosition', 'RodentID',
                             'RodentSpecies', 'RodentSex']]

        # Reorder trigger data in terms of the time of trigger event
        triggers = triggers.sort_values('Time')

        # Transform recorded matrix of serial intervals to csv file
        triggers.to_csv(
            os.path.join(os.path.dirname(__file__),
                         '../parsed-data/Triggers.csv'),
            mode='a',
            index=False,
            header=False)


if __name__ == '__main__':
    # Add all logger numbers
    # Only a subset through the 'LoggerNumbers.txt'
    logger_no_list_df = pd.read_csv(os.path.join(
            os.path.dirname(__file__),
            '../logger-data/LoggerNumbers.txt'), header=None)

    logger_no_list = logger_no_list_df.values.tolist()[0]

    # # All loggers through the 'EWYT_Project_Logger_Movements.csv'
    # logger_no_list_df = pd.read_csv(
    #     os.path.join(os.path.dirname(__file__),
    #                  '../logger-data/EWYT_Project_Logger_Movements.csv'),
    #     header=0)

    # logger_no_list = logger_no_list_df['Logger_ID'].values.tolist()
    # print(logger_no_list)

    list_log_file = []
    # Parse through all the logger files matching the list criterion above
    for logger_no in logger_no_list:
        # Read logger file ...
        list_log_file = glob.glob(
            os.path.join(
                os.path.dirname(__file__),
                '../logger-data/{}/*-DATA-{}.txt'.format(logger_no, logger_no)
                ))

        # ... and process it into the Triggers.csv file
        main(list_log_file)
