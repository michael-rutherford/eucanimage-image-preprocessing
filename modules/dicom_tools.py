import os
#import numpy as np
#import pandas as pd
import random
import pydicom
#from typing import List

import cv2
from modules.piqe import piqe


class dicom_tools(object):

    def __init__(self, dicom_path: str):
        self.dicom_path = dicom_path
        self.dicom_files = os.listdir(dicom_path)

        results = []

        for folder_path in self.dicom_files:
            print(folder_path)
            #dicom_files = [f for f in os.listdir(folder_path) if f.endswith('.dcm')]

            #if not dicom_files:
            #    print("No DICOM files found in the folder")
            #else:
            #    # Read the first DICOM file and get the acquisition protocol variables
            #    result_dict = extract_acquisition_protocols(folder_path, dicom_files[0])
            #    results.append(result_dict)

            #    # Send file list to process the quality score
            #    piqe_avg_score = get_piqe_average(folder_path, dicom_files, result_dict)





    def extract_acquisition_protocols(self, folder_path: str, dicom_file: str) -> dict:

        all_list = ['PatientID','StudyInstanceUID','SeriesInstanceUID','Modality']

        ct_list = ['XRayTubeCurrentInmA',   # MA
                   'KVP',                   # KVP
                   'SliceThickness',        # Slice Thickness
                   'ConvolutionKernel'      # Convolution Kernel
                   ]

        mr_list = ['EchoTime',          # TE (Time to Echo)
                   'RepetitionTime',    # TR (Time to Repetition)
                   'EchoTrainLength',   # ETL (Echo Train Length)
                   'FlipAngle'          # Flip angle
                   ] 

        dicom_path = os.path.join(folder_path, dicom_file)

        extract_dict = {}
        extract_inc = 0

        dicom_dataset = pydicom.dcmread(dicom_path)
    
        extract_dict[extract_inc] = {}

        for tag in all_list:
            extract_dict[extract_inc][tag] = dicom_dataset.get(tag, None)

        if dicom_dataset.Modality == 'CT':
            for tag in ct_list:
                extract_dict[extract_inc][tag] = dicom_dataset.get(tag, None)
        elif dicom_dataset.Modality == 'MR':
            for tag in mr_list:
                extract_dict[extract_inc][tag] = dicom_dataset.get(tag, None)

        #extract_df = pd.DataFrame.from_dict(extract_dict,orient='index')
        return extract_dict


    def get_piqe(self, dataset: pydicom.Dataset) -> float:

        # Get the pixel data into a numpy array
        pixel_array = dataset.pixel_array

        # Normalizing pixel array if necessary
        pixel_array = cv2.normalize(pixel_array, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Open the image using OpenCV
        #cv2.imshow('DICOM image', pixel_array)

        # Wait for a key press and then close the image window
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

        Score, NoticeableArtifactsMask, NoiseMask, ActivityMask = piqe(pixel_array)
        print(f"Score: {Score:.2f}")

        return Score

    def get_piqe_average(self, folder_path: str, dicom_files: List, result_dict: dict) -> float:

        # Randomly select 10%, no less than 10 or length of list.
        list_length = len(dicom_files)
        sample_size = max(10, int(list_length*0.1))
        sample_size = min(sample_size, list_length)  # Ensure sample size does not exceed list length
        selected_files = random.sample(dicom_files, sample_size)

        scores = []
        for file in selected_files:
            dicom_path = os.path.join(folder_path, file)
            dicom_dataset = pydicom.dcmread(dicom_path)
            score = self.get_piqe(dicom_dataset)
            scores.append(score)

        # Calculate and print the average score
        average_score = sum(scores) / len(scores)
        print(f"Average PIQE Score: {average_score:.2f}")

        return average_score



#def main(folder_list: List) -> None:
#    # Get all the DICOM files in the folder

#    results = []

#    for folder_path in folder_list:
#        print(folder_path)
#        dicom_files = [f for f in os.listdir(folder_path) if f.endswith('.dcm')]

#        if not dicom_files:
#            print("No DICOM files found in the folder")
#        else:
#            # Read the first DICOM file and get the acquisition protocol variables
#            result_dict = extract_acquisition_protocols(folder_path, dicom_files[0])
#            results.append(result_dict)

#            # Send file list to process the quality score
#            piqe_avg_score = get_piqe_average(folder_path, dicom_files, result_dict)

#if __name__ == "__main__":
#    #folder_list = \
#    #    [r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\6415974217\06-09-1988-NA-ABDOMENPELVIS-29078\237.000000-PJN-15958',
#    #     r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\3209648408\09-23-1999-NA-CT UROGRAM-31798\3.000000-PARENCHYMAL PHASE Sep1999-95798']

#    folder_list = \
#        [r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\6415974217\06-09-1988-NA-ABDOMENPELVIS-29078\237.000000-PJN-15958',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\3209648408\09-23-1999-NA-CT UROGRAM-31798\3.000000-PARENCHYMAL PHASE Sep1999-95798',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\6774825273\09-11-2013-NA-XR CHEST AP PORTABLE for Scott Kaufman-73078\1.000000-NA-91318',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\6670427471\05-26-2000-NA-FORFILE CT ABD ANDOR PEL - CD-25398\5.000000-NEPHRO  4.0  B40f  M0.4-18678',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\8155012288\09-08-1999-NA-FORFILE CT CHABPEL - CD for 8155012288-44118\1.000000-SCOUT-12438',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\8732322741\01-05-2008-NA-MRI PROSTATE W WO CONTRAST-39318\4.000000-t2spcrstaxial oblProstate-50358',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\9189822998\02-15-1989-NA-CT HIP WO CONTRASTBILAT-50838\5865.000000-Surview Test-43798',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\9894340694\04-16-1997-NA-MRI ABDOMEN PELVIS WWO CONT-87318\6.000000-LIVER-KIDNEYTIFL2DAXIAL-30038',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\9894340694\04-16-1997-NA-MRI ABDOMEN PELVIS WWO CONT-87318\15.000000-LIVER-PELVISHASTEAXIALP-65398',
#        r'D:\Data03\MIDI\pseudo_set\synthetic\Pseudo-PHI-DICOM-Data\9894340694\04-16-1997-NA-MRI ABDOMEN PELVIS WWO CONT-87318\16.000000-LIVER-PELVISHASTESAGPOS-74838']




#    main(folder_list)