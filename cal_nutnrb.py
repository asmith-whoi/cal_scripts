import sys
import csv
from datetime import datetime as dt

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

def go_again():
    """
    Ask if user wants to go again.
    """
    result = False
    response = input("Would you like to do another file? Y or [N]... ") or "n"
    if response in "Yy":
            result = True
    return result

   
def main():
    while True:
        # Prompt user for serial number...
        serial_number = input("Enter the NUTNR-B serial number... ")

        # Prompt user to select the source cal file...
        infile = filedialog.askopenfilename(title="Select the instrument calibration file...")
        if not infile:
            print("Operation cancelled!")
            if go_again():
                continue
            else:
                break
            
        wl = []     # wavelength bins
        eno3 = []   # nitrate extinction coefficients
        eswa = []   # seawater extinction coefficients
        di = []     # deionized water reference spectra

        lower_wl_limit = 217.0
        upper_wl_limit = 240.0

        filedate = ""
        
        with open(infile, "r") as csv_in:
            reader = csv.reader(csv_in)
            for row in reader:
                if "creation time" in row[1] and not filedate:
                    filedate = dt.strptime(row[1][19:], "%d-%b-%Y %H:%M:%S")
                elif row[1].startswith("T_CAL_SWA"):
                    cal_temp = row[1][10:].strip()
                elif row[0] == "E":
                    wl.append(row[1])
                    eno3.append(row[2])
                    eswa.append(row[3])
                    di.append(row[5])

        input("Operation complete. Press ENTER to save new cal file...")
                    
        fname_sn = serial_number[-4:].zfill(5)
        fname_date = filedate.strftime("%Y%m%d")
        outfile = filedialog.asksaveasfilename(initialfile=("CGINS-NUTNRB-%s__%s.csv" % (fname_sn, fname_date)), defaultextension=".csv")

        with open(outfile, 'w') as newfile:
            writer = csv.writer(newfile)
            writer.writerow(["serial", "name","value","notes"])
            writer.writerow([serial_number, "CC_cal_temp", cal_temp,""])
            writer.writerow([serial_number, "CC_di", di, ""])
            writer.writerow([serial_number, "CC_eno3", eno3, ""])
            writer.writerow([serial_number, "CC_eswa", eswa, ""])
            writer.writerow([serial_number, "CC_lower_wavelength_limit_for_spectra_fit", lower_wl_limit, ""])
            writer.writerow([serial_number, "CC_upper_wavelength_limit_for_spectra_fit", upper_wl_limit, ""])
            writer.writerow([serial_number, "CC_wl", wl, ""])

        if go_again():
            continue
        else:
            break
        
if __name__ == "__main__":
    main()
