# wytham-logparser
This package is used for processing logger data files for the Wytham Woods rodent project.

## Input Folder (Logger Data)

All data files containing logger outputs are stored in the folder designated by the logger ID. For example, all data collected by the logger O80A are stored in the folder 080A. All logger files follow the same naming convention: *-DATA-loggerID.txt.

In this folder we also have the EWYT_Project_Logger_Movements.csv file, which contains all logger positions in the grid on the day of each grid reshuffling.

The MouseIDTrappingData.csv contains all the ID tags associated with each tagged rodent, as well as their sex and species information.

Finally, the LoggerNumbers.txt contains a list of all the logger IDs for which we wish to process the data, if fewer than the total number of loggers available on the grid; in this example case, it contains only the three loggers we included the logger data for, i.e. 080A, 080B and 080C.

## Output Folder (Parsed Data)

In this folder we have both the file including all the recongnised Triggers.csv from chipped rodents, as well as its more refined versions Contacts.csv, which contains all recognised contact events between the rodents, registered via the deployed loggers.

## Wythamlogger Folder

This folder contains the two python scipt to process the trigger (triggers.py) and contact events (contacts.py) respectively.

## Installation procedure
***
One way to install the module is to download the repositiory to your machine of choice and type the following commands in the terminal. 
```bash
git clone https://github.com/I-Bouros/wytham-logparser.git
cd ../path/to/the/file
```

A different method to install this is using `pip`:

```bash
pip install -e .
```

## Usage

To parse logger data, first run the triggers.py file. If you have already run this once and wish to rerun your analyses, erase all lines except the header, and add an empty row. Rerunning the script now will ensure correct formating of the file.

The second step, to transform raw trigger information into meaningful contact events, run the contacts.py file. You can change the maximum time between two triggers to still be considered a contact (expressed in minutes) in the last line of the code, in the 

```python
if __name__ == '__main__':
    main(max_contact_time=5)
```
section. It is in this section that we run the functions created at the top of the file. 
