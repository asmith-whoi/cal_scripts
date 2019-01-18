import sys
import csv
from datetime import datetime as dt
import json
import numpy as np

# Limit display of floats to 8 decimal places and suppress sci notation
np.set_printoptions(precision=8, suppress=True)

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

##
## Constants
## =========
LOWER_WL_LIMIT = 217.0  # constant
UPPER_WL_LIMIT = 240.0  # constant

##
## Function definitions
## ====================
def get_user(prompt, response_type):
    """
    Bare bones user input validation. If string, must not be empty.
    If integer or float, must actually be (or be converted to) that.
    Also handles simple Y or N with defaults.

    prompt - Text to display as user prompt
    response_type - str, defaultY, defaultN, int or float
    """
    while True:
        response = input(prompt)
        if response_type == "str":
            if not response:
                print("Whoa! You didn't enter anything.")
                continue
        elif response_type == "defaultY":
            if not response in "YyNn":
                print("Whoa! That's not a valid answer.")
                continue
            elif response in "Yy":
                return True
            else:
                return False
        elif response_type == "defaultN":
            if not response in "YyNn":
                print("Whoa! That's not a valid answer.")
                continue
            elif response in "Nn":
                return False
            else:
                return True
        elif response_type =="int":
            try:
                response = int(response)
            except ValueError:
                print("Whoa! That's not a number.")
                continue
        elif response_type =="float":
            try:
                response = float(response)
            except ValueError:
                print("Whoa! That's not a number.")
                continue
        return response

def reader_checks_passed(*args):
    """
    Simple tests for successful parsing of cal file.

    args - all fields parsed from the input file. First two will be
    srting, rest are lists.
    """
    # check if any fields are empty...
    if not all(arg for arg in args):
        return False
    # check if lists are different length...
    if not all(len(arg) == len(args[2]) for arg in args[3:]):
        return False
    # checks passed...
    return True
    
def load_cal_file():
    """
    Reads a vendor cal file and returns the desired values. Prompts
    user for input file.
    """
    wl = []     # wavelength bins
    eno3 = []   # nitrate extinction coefficients
    eswa = []   # seawater extinction coefficients
    di = []     # deionized water reference spectra

    cal_temp = ""

    filedate = ""

    while True:
        # Prompt user to select the source cal file...
        infile = filedialog.askopenfilename(title="Select the instrument calibration file...")
        if not infile:
            if not get_user("Would you like to cancel? Enter Y or [N]... ", "defaultN"):
                continue
            else:
                return False
            
        # Open the file and parse out the needed values. If the file
        # format ever changes, or the corrupt, this may do some
        # unexpected things...
        with open(infile, "r") as csv_in:
            reader = csv.reader(csv_in)
            # Read file row by row...
            for row in reader:
                # NUTNR cal files may have multiple creation dates in
                # the header. The first one denotes the most recent
                # calibration update, and is the one we want...
                if "creation time" in row[1] and not filedate:
                    filedate = dt.strptime(row[1][19:], "%d-%b-%Y %H:%M:%S")
                # Find the calibration temperature...
                elif row[1].startswith("T_CAL_SWA"):
                    cal_temp = row[1][10:].strip()
                # Rows beginning with E contain the values we seek...
                elif row[0] == "E":
                    wl.append(float(row[1]))
                    eno3.append(float(row[2]))
                    eswa.append(float(row[3]))
                    di.append(float(row[5]))

        # Do a few checks on the parsed values...
        if reader_checks_passed(cal_temp, filedate, wl, eno3, eswa, di):
            # Checks passed, return our values...
            return cal_temp, filedate, wl, eno3, eswa, di
        else:
            # Checks failed, user can try again or cancel...
            print("Whoa! I couldn't parse that file.")
            if get_user("Would you like to select another calibration file? Enter [Y] or N... ", "defaultY"):
                # User wants to try again...
                continue
            else:
                # User cancels...
                return False

def save_cal_file(cal_data, serial_number, lwl, uwl):
    """
    Writes calibration data to a new file in the required format. Prompts
    user for output file.

    cal_data - tuple returned by load_cal_file()
    serial_number - user-provided string
    lwl - lower wl limit CONSTANT
    uwl - upper wl limit CONSTANT
    """
    cal_temp, filedate, wl, eno3, eswa, di = cal_data

    fname_sn = serial_number[-4:].zfill(5)
    fname_date = filedate.strftime("%Y%m%d")

    while True:
        outfile = filedialog.asksaveasfilename(initialfile=("CGINS-NUTNRB-%s__%s.csv" % (fname_sn, fname_date)), defaultextension=".csv")
        # User cancelled...
        if not outfile:
            if not get_user("Would you like to cancel? Enter Y or [N]... ", "defaultN"):
                continue
            else:
                return False

        # Filename was chosen by user...
        with open(outfile, 'w', newline='') as newfile:
            writer = csv.writer(newfile)
            writer.writerow(["serial", "name","value","notes"])
            writer.writerow([serial_number, "CC_cal_temp", cal_temp,""])
            writer.writerow([serial_number, "CC_di", json.dumps(di),""])
            writer.writerow([serial_number, "CC_eno3", json.dumps(eno3), ""])
            writer.writerow([serial_number, "CC_eswa", json.dumps(eswa), ""])
            writer.writerow([serial_number, "CC_lower_wavelength_limit_for_spectra_fit", lwl, ""])
            writer.writerow([serial_number, "CC_upper_wavelength_limit_for_spectra_fit", uwl, ""])
            writer.writerow([serial_number, "CC_wl", json.dumps(wl), ""])

            print("New calibration file saved successfully. You should examine the file for errors.")
            return True

def main():
    """Main program logic"""
    while True:
        # Prompt user for serial number...
        serial_number = get_user("Enter the NUTNR-B serial number... ", "str")

        # A suddenly appearing dialog window might be confusing.
        # Prepare user for what is about to happen...
        input("In the next step, select the vendor provided calibration file. Press ENTER to continue...")

        # Get the values we want from the calibration file...
        cal_data = load_cal_file()
        if not cal_data:
            # User cancelled...
            break

        input("In the next step, you will save the new formatted calibration file. Press ENTER to continue...")
        
        if not save_cal_file(cal_data, serial_number, LOWER_WL_LIMIT, UPPER_WL_LIMIT):
            print("Operation cancelled")

        # Prompt user to create a new cal file...
        if get_user("Would you like to create a new calibration file? [Y] or N... ", "defaultY"):
            continue

        print("Good bye!")
        return

##
## Main
## ====

if __name__ == "__main__":
    main()
