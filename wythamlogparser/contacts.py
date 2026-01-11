#
# This file is part of wytham-logparse
# (https://github.com/I-Bouros/whytham-logparser.git)
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
import datetime
from datetime import timedelta


def read_trigger_data(trigger_file: str):
    """
    Parses the csv document containing all trigger events caused
    by recognised rodent tags across all traps.

    Parameters
    ----------
    trigger_file : str
        The name of the trigger data file used.

    Returns
    -------
    pandas.Dataframe
        Dataframe of the mouse trigger event data.

    """
    # Extract unprocessed trigger data from the given trigger file
    data = pd.read_csv(
        os.path.join(os.path.dirname(__file__), trigger_file),
        header=0)

    return data


def process_trigger_data(trigger_data: pd.DataFrame,
                         max_contact_time: float | int = 5):
    """
    Parameters
    ----------
    trigger_data : str
        Dataframe of the mouse trigger event data.
    max_contact_time : float or int
        Maximum time difference between two subsequent logger triggers by
        distinct rodents that still constitutes a contact. It is evaluated
        in minutes

    Returns
    -------
    pandas.Dataframe
        Dataframe of the mouse trigger event data.
    """
    # Process times of triggers into a consistent datetime format
    trigger_data['Processed-Time'] = [
        process_dates(x) for x in trigger_data['Time']]

    # Reorder data in terms of the processed datetime format trigger times
    # first, and logger poisition second
    trigger_data = trigger_data.sort_values(
        ['Processed-Time', 'LoggerPosition'])

    # Create empty dataframe with prescribed column names
    contacts = pd.DataFrame(columns=[
        'Time', 'Interval(min)', 'LoggerPosition',
        'Rodent1ID', 'Rodent1Species', 'Rodent1Sex',
        'Rodent2ID', 'Rodent2Species', 'Rodent2Sex',
        'ContactType'])

    # For each unique logger position in the sorted trigger data ...
    for site in trigger_data['LoggerPosition'].unique():
        # ... extract only those entries pertaining to that particular
        # logger site
        site_trigger_events = trigger_data[
            trigger_data['LoggerPosition'] == site]

        # Reorder these subset entries by their processed datetime format
        # trigger event time and ...
        site_trigger_events = site_trigger_events.sort_values('Processed-Time')
        for index in range(site_trigger_events.shape[0]):
            # If that entry is not the first one in the batch
            # and if this entry is within 'max_contact_time' from the previous
            # trigger, and the rodent causing this trigger differs from the
            # one causing the previous trigger...
            if index > 0 and (
                site_trigger_events['RodentID'].iloc[index-1] != site_trigger_events[  # noqa
                        'RodentID'].iloc[index]) and ((site_trigger_events[
                            'Processed-Time'].iloc[index] - site_trigger_events[  # noqa
                                'Processed-Time'].iloc[index-1]) < timedelta(
                                    minutes=max_contact_time)):
                # ... then we consider this a contact event and save the
                # details as a new entry in the empty contact matrix we
                # created above
                newrow = pd.DataFrame([{
                    'Time': site_trigger_events['Processed-Time'].iloc[
                        index-1],
                    'Interval(min)': (
                        site_trigger_events['Processed-Time'].iloc[index] -
                        site_trigger_events['Processed-Time'].iloc
                        [index-1]).total_seconds() // 60,
                    'LoggerPosition': site,
                    'Rodent1ID': site_trigger_events['RodentID'].iloc[index-1],
                    'Rodent1Species': site_trigger_events[
                        'RodentSpecies'].iloc[index-1],
                    'Rodent1Sex':  site_trigger_events[
                        'RodentSex'].iloc[index-1],
                    'Rodent2ID': site_trigger_events['RodentID'].iloc[index],
                    'Rodent2Species': site_trigger_events[
                        'RodentSpecies'].iloc[index],
                    'Rodent2Sex': site_trigger_events[
                        'RodentSex'].iloc[index],
                    'ContactType': contact_type(
                        site_trigger_events['RodentSpecies'].iloc[index-1],
                        site_trigger_events['RodentSpecies'].iloc[index]),
                }])
                contacts = pd.concat([contacts, newrow])

    return contacts


def contact_type(type_1: str, type_2: str):
    """
    Process type of contacts by species of rodents

    Parameters
    ----------
    type_1 : str
        Species of the first rodent.
    type_2 : str
        Species of the second rodent.

    Returns
    -------
    str
        Type of contact. Can be either 'Within species' or 'Between species'.

    """
    if type_1 == type_2:
        return 'Within species'
    else:
        return 'Between species'


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
    struct = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    return struct


def main(max_contact_time: float | int = 5):
    """
    Combines the timelines of deviation percentages and baseline
    activity-specific contact matrices to get weekly, region-specific
    contact matrices.

    Parameters
    ----------
    max_contact_time : float or int
        Maximum time difference between two subsequent logger triggers by
        distinct rodents that still constitutes a contact. It is evaluated
        in minutes.

    Returns
    -------
    csv
        Processed files for the baseline and region-specific time-dependent
        contact matrices for each different region found in the default file.

    """
    # Read entire trigger data
    trigger_data = read_trigger_data(os.path.join(
        os.path.dirname(__file__), '../parsed-data/Triggers.csv'))

    contacts = process_trigger_data(trigger_data, max_contact_time)

    # Reorder data in terms of the logger poisition first,
    # and the processed datetime format trigger times second
    contacts = contacts.sort_values(['LoggerPosition', 'Time'])

    # Keep only columns of interest
    contacts = contacts[['Time', 'Interval(min)', 'LoggerPosition',
                         'Rodent1ID', 'Rodent1Species', 'Rodent1Sex',
                         'Rodent2ID', 'Rodent2Species', 'Rodent2Sex',
                         'ContactType']]

    # Keep only one meeting event between the same rodents within the
    # same 'max_contact_time' minutes
    final_contacts = pd.DataFrame(columns=[
        'Time', 'Interval(min)', 'LoggerPosition',
        'Rodent1ID', 'Rodent1Species', 'Rodent1Sex',
        'Rodent2ID', 'Rodent2Species', 'Rodent2Sex',
        'ContactType'])

    for site in contacts['LoggerPosition'].unique():
        site_contact_events = contacts[
            contacts['LoggerPosition'] == site]

        site_contact_events = site_contact_events.sort_values('Time')

        for index in range(site_contact_events.shape[0]):
            if index > 0 and ((site_contact_events[
                'Time'].iloc[index] - site_contact_events['Time'].iloc[
                    index-1]) < timedelta(minutes=max_contact_time)) and (
                        site_contact_events['Rodent1ID'].iloc[index-1] in [
                            site_contact_events['Rodent1ID'].iloc[index],
                            site_contact_events['Rodent2ID'].iloc[index]]
                            ) and (site_contact_events['Rodent2ID'].iloc[
                                        index-1] in [site_contact_events[
                                            'Rodent1ID'].iloc[index],
                                            site_contact_events[
                                                'Rodent2ID'].iloc[index]]):
                continue
            else:
                final_contacts = pd.concat([final_contacts.T,
                                            site_contact_events.iloc[index]],
                                           axis=1).T.reset_index(drop=True)

    # Transform remaining contact dataframe entries to csv file
    final_contacts.to_csv(
        os.path.join(os.path.dirname(__file__), '../parsed-data/Contacts.csv'),
        index=False)


if __name__ == '__main__':
    main(max_contact_time=5)
