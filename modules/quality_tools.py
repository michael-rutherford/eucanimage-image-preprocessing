import pydicom as dicom
from pydicom.multival import MultiValue
import cv2
import random
import json
from modules.piqe import piqe
from modules.xnat_tools import xnat_tools
from modules.log_helper import log_helper

import concurrent.futures as futures

class quality_tools(object):

    # ----------------------------
    # read dicom
    # ----------------------------
    def read_dicom(self, scan_file, exclude_pixels):

        dataset = None
        with scan_file.open() as dicom_file:

            dataset = dicom.dcmread(dicom_file, stop_before_pixels=exclude_pixels)

        return [scan_file, dataset]

    # ----------------------------
    # preprocess project
    # ----------------------------

    def preprocess_project(self, args, db_scan_list, log):
        
        return_results = []

        # ----------------------------
        # Multi-processing
        # Set the number of CPUs in the config file.
        # ----------------------------

        if args['multi_proc'] == True:
            
            workers = 60 if args['multi_proc_cpu'] > 60 else args['multi_proc_cpu'] if args['multi_proc_cpu'] >= 1 else 1

            with futures.ProcessPoolExecutor(max_workers=workers) as executor:

                futures_list = []

                # process scans
                for db_scan in db_scan_list:
                    futures_list.append(executor.submit(self.preprocess_scan, db_scan, args, log))

                for future in futures.as_completed(futures_list):
                    return_results.append(future.result())

        # ----------------------------
        # Single-processing
        # ----------------------------

        else:            
            # process scans
            for db_scan in db_scan_list:

                return_results.append(self.preprocess_scan(db_scan, args, log))

    # ----------------------------
    # preprocess scans
    # ----------------------------
    def preprocess_scan(self, scan, args, log):
        
        # get sort key
        def get_sort_key(x):
            dataset = x[1]
            if "InstanceNumber" in dataset:
                return dataset.InstanceNumber
            elif "ImagePositionPatient" in dataset:
                return dataset.ImagePositionPatient
            elif "SliceLocation" in dataset:
                return dataset.SliceLocation
            elif "AcquisitionTime" in dataset:
                return dataset.AcquisitionTime
            else:
                return dataset.SOPInstanceUID

        log = log_helper(log.start_time, log.prog_name, log.log_path, log.log_level)

        log.info(f'Processing scan {scan.scan_id}')

        try:

            xtools = xnat_tools(args['db_connect_string'], args['xnat_server'], args['xnat_user'], args['xnat_password'])

            edit_scan_list = xtools.get_db_scan_list(False, scan.project_name, scan.subject_label, scan.experiment_label, scan.scan_id)

            if len(edit_scan_list) > 0:
                edit_scan = edit_scan_list[0]

                # ??? Check whether this is best filter.
                if edit_scan.scan_modality in ['MR', 'CT', 'MG']:

                    # if reset or scan_quality or scan_acquisition is blank
                    if args['reset'] == True or not edit_scan.scan_quality or not edit_scan.scan_acquisition:

                        # get xnat scan element
                        xnat_scan = xtools.get_xnat_element(edit_scan.project_id, edit_scan.subject_id, edit_scan.experiment_id, edit_scan.scan_id)

                        # get dicom files
                        scan_files = xnat_scan.resources['DICOM'].files if 'DICOM' in xnat_scan.resources else None                    
                        datasets = []
                        if scan_files:

                            # ----------------------------
                            # Multi-threaded
                            # Warning - Maxes out CPU
                            # ----------------------------

                            if args['multi_thread'] == True:

                                # retrieve the header information from the DICOM files
                                with futures.ThreadPoolExecutor(max_workers=args['multi_thread_workers']) as executor:

                                    futures_list = []

                                    for scan_key, scan_file in scan_files.items():
                                        futures_list.append(executor.submit(self.read_dicom, scan_file, True))

                                    for future in futures.as_completed(futures_list):
                                        datasets.append(future.result())

                            # ----------------------------
                            # Single-threaded
                            # ----------------------------

                            else:
                                # retrieve the header information from the DICOM files
                                for scan_key, scan_file in scan_files.items():

                                    #with scan_file.open() as dicom_file:
                                        #dataset = dicom.dcmread(dicom_file, stop_before_pixels=True)
                                        #datasets.append([scan_file, dataset])
                                    datasets.append(self.read_dicom(scan_file, exclude_pixels=True))


                            # ----------------------------
                            # sort datasets by InstanceNumber, ImagePositionPatient, SliceLocation, AcquisitionTime, SOPInstanceUID
                            # ----------------------------
                            datasets.sort(key=get_sort_key)

                            # ----------------------------
                            # filter out scouts, localizers, b0s
                            # ----------------------------

                            # ensure not Scout or Localizer (Ignore first 3 slices, check Series description for "scout" or "localizer", check ImageType for "localizer")
                            # ensure not B0 bias correction (Check Series description or Sequence name for "b0")

                            # cut off first 3 slices
                            if len(datasets) > 3:
                                filtered_datasets = datasets[3:]
                            else:
                                filtered_datasets = datasets
            
                            # check remaining slices for scout, localizer, b0 and filter out
                            disallowed_terms = ['scout', 'localizer', 'b0']
                            filtered_datasets = [ds for ds in filtered_datasets 
                                if not any(x.lower() in disallowed_terms for x in ds[1].ImageType)
                                and ('SeriesDescription' not in ds[1] or not any(term in ds[1].SeriesDescription.lower() for term in disallowed_terms))
                                and ('ProtocolName' not in ds[1] or not any(term in ds[1].ProtocolName.lower() for term in disallowed_terms))
                                and ('SequenceName' not in ds[1] or not any(term in ds[1].SequenceName.lower() for term in disallowed_terms))]

                            # generate quality scores
                            if not edit_scan.scan_quality or args['reset'] == True:
                                edit_scan.scan_quality = self.get_quality_score(edit_scan, xnat_scan, filtered_datasets, log, args)
                                xtools.flush_database()

                            # get acquisition variables
                            if not edit_scan.scan_acquisition or args['reset'] == True:
                                edit_scan.scan_acquisition = self.get_acquisition_tags(edit_scan, xnat_scan, filtered_datasets, log)
                                xtools.flush_database()
                
        except Exception as e:            
            log.error(f'Project Scan Error - project: {scan.project_name} | subject: {scan.subject_label} | experiment: {scan.experiment_label} | scan: {scan.scan_id} | error: {str(e)}')
            return None

        return None



    # ----------------------------
    # get acquisition variables
    # ----------------------------

    def get_acquisition_tags(self, edit_scan, xnat_scan, datasets, log):

        # all
        all_list = [
            #'PatientID',                    # (0010,0020) - Patient ID
            'StudyInstanceUID',             # (0020,000D) - Study Instance UID
            #'StudyDescription',             # (0008,1030) - Study Description
            'SeriesInstanceUID',            # (0020,000E) - Series Instance UID
            #'SeriesDescription',            # (0008,103E) - Series Description
            'Manufacturer',                 # (0008,0070) - Manufacturer
            #'ManufacturerModelName',        # (0008,1090) - Manufacturer Model Name
            'Modality',                     # (0008,0060) - Modality
            
            'ImageType',                    # (0008,0008) - Image Type
            'SliceThickness',               # (0018,0050) - Slice Thickness
            'SpacingBetweenSlices',         # (0018,0088) - Spacing Between Slices
            'ImagePositionPatient',         # (0020,0032) - Image Position (Patient)
            'ImageOrientationPatient',      # (0020,0037) - Image Orientation (Patient)
            'PixelSpacing',                 # (0028,0030) - Pixel Spacing
            #'BitsAllocated',                # (0028,0100) - Bits Allocated
            #'BitsStored',                   # (0028,0101) - Bits Stored
            #'HighBit',                      # (0028,0102) - High Bit
            #'PixelRepresentation',          # (0028,0103) - Pixel Representation
            #'WindowCenter',                 # (0028,1050) - Window Center
            #'WindowWidth',                  # (0028,1051) - Window Width
            ]
        
        # mr
        mr_list = [
            'ContrastBolusAgent',           # (0018,0010) - Contrast/Bolus Agent
            'ScanningSequence',             # (0018,0020) - Scanning Sequence
            'SequenceVariant',              # (0018,0021) - Sequence Variant
            'ScanOptions',                  # (0018,0022) - Scan Options
            'MRAcquisitionType',            # (0018,0023) - MR Acquisition Type
            'SequenceName',                 # (0018,0024) - Sequence Name
            'RepetitionTime',               # (0018,0080) - Repetition Time - TR (Time to Repetition)
            'EchoTime',                     # (0018,0081) - Echo Time - TE (Time to Echo)
            'MagneticFieldStrength',        # (0018,0087) - Magnetic Field Strength
            'EchoTrainLength',              # (0018,0091) - Echo Train Length - ETL (Echo Train Length)
            'FlipAngle',                    # (0018,1314) - Flip Angle
            'ContrastBolusUsageSequence',   # (0018,9341) - Contrast/Bolus Usage Sequence (for enhanced)
            'ContrastBolusAgentPhase',      # (0018,9344) - Contrast/Bolus Agent Administered (for enhanced)
            ] 

        # ct & mg
        ct_mg_list = [
            'KVP',                          # (0018,0060) - KVP
            'FocalSpots',                   # (0018,1190) - Focal Spots
            'DistanceSourceToDetector',     # (0018,1110) - Distance Source to Detector
            'DistanceSourceToPatient',      # (0018,1111) - Distance Source to Patient
            'ExposureTime',                 # (0018,1150) - Exposure Time
            'XRayTubeCurrentInmA',          # (0018,1151) - X-Ray Tube Current
            'Exposure',                     # (0018,1152) - Exposure
            #'ExposureInuAs',                # (0018,1153) - Exposure in uAs
            'FilterType',                   # (0018,1160) - Filter Type 
            ]

        # ct
        ct_list = [
            'GantryDetectorTilt',           # (0018,1120) - Gantry/Detector Tilt
            'TableHeight',                  # (0018,1130) - Table Height
            #'GeneratorPower',               # (0018,1170) - Generator Power
            'ConvolutionKernel',            # (0018,1210) - Convolution Kernel
            'SpiralPitchFactor',            # (0018,9311) - Spiral Pitch Factor
            ]

        # mg
        mg_list = [
            'BodyPartThickness',            # (0018,11A0) - Body Part Thickness
            'CompressionForce',             # (0018,11A2) - Compression Force
            'ViewPosition',                 # (0018,5101) - View Position
            'ImageLaterality',              # (0020,0062) - Image Laterality
            ]


        def handle_multivalue(obj):
            if isinstance(obj, MultiValue):
                # Convert MultiValue to list
                return [v for v in obj]
            raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

        try:
            # Option 1
            # Read first DICOM file in scan (NOT always first)
            #dicom_dataset = xnat_scan.read_dicom()

            # Option 2
            # Read first DICOM file in sorted dataset list
            #dicom_dataset = datasets[0][1]

            # Option 3
            # Read random DICOM file in scan
            dicom_dataset = random.choice(datasets)[1]
    
            extract_dict = {}

            if dicom_dataset.Modality == 'CT':
                combined_list = [*all_list, *ct_mg_list, *ct_list]
                for tag in combined_list:
                    extract_dict[tag] = dicom_dataset.get(tag, None)
            elif dicom_dataset.Modality == 'MG':
                combined_list = [*all_list, *ct_mg_list, *mg_list]
                for tag in combined_list:
                    extract_dict[tag] = dicom_dataset.get(tag, None)
            elif dicom_dataset.Modality == 'MR':
                combined_list = [*all_list, *mr_list]
                for tag in combined_list:
                    extract_dict[tag] = dicom_dataset.get(tag, None)

            if len(extract_dict) != 0:
                return json.dumps(extract_dict, default=handle_multivalue)

            return None

        except Exception as e:     
            log.error(f'Acquisition Retrieval Error - project: {edit_scan.project_name} | subject: {edit_scan.subject_label} | experiment: {edit_scan.experiment_label} | scan: {edit_scan.scan_id} | error: {str(e)}')
            return None

    # ----------------------------
    # get quality score
    # ----------------------------

    def get_quality_score(self, edit_scan, xnat_scan, datasets, log, args):

        results_dict = {}
        results_dict['instances'] = {}

        try:
            # Randomly select 10%, no less than 10 or length of list.
            list_length = len(datasets)
            sample_size = max(10, int(list_length*0.1))
            sample_size = min(sample_size, list_length)  # Ensure sample size does not exceed list length
            selected_datasets = random.sample(datasets, sample_size)

            # ----------------------------
            # Multi-threaded
            # Warning - Maxes out CPU
            # ----------------------------

            if args['multi_thread'] == True:

                # retrieve the header information from the DICOM files
                with futures.ThreadPoolExecutor(max_workers=args['multi_thread_workers']) as executor:

                    futures_list = []

                    for dataset in selected_datasets:
                        futures_list.append(executor.submit(self.get_piqe, dataset))

                    for future in futures.as_completed(futures_list):
                        dataset, score, artifact_mask, noise_mask, activity_mask = future.result()
                        results_dict['instances'][dataset[1].SOPInstanceUID] = {}
                        results_dict['instances'][dataset[1].SOPInstanceUID]['piqe_score'] = score

            # ----------------------------
            # Single-threaded
            # ----------------------------

            else:
                # retrieve the pixel information from the DICOM files
                for dataset in selected_datasets:
                    dataset, score, artifact_mask, noise_mask, activity_mask = self.get_piqe(dataset)
                    results_dict['instances'][dataset[1].SOPInstanceUID] = {}
                    results_dict['instances'][dataset[1].SOPInstanceUID]['piqe_score'] = score
                    #results_dict['instances'][dicom_file[1].SOPInstanceUID]['artifact_mask'] = artifact_mask
                    #results_dict['instances'][dicom_file[1].SOPInstanceUID]['noise_mask'] = noise_mask
                    #results_dict['instances'][dicom_file[1].SOPInstanceUID]['activity_mask'] = activity_mask

            # Calculate and log the average score
            scores = [instance['piqe_score'] for instance in results_dict['instances'].values()]
            average_score = sum(scores) / len(scores)
            #print(f"Average PIQE Score: {average_score:.2f}")
            results_dict['average_piqe_score'] = average_score

            return json.dumps(results_dict)

        except Exception as e:     
            log.error(f'Quality Score Error - project: {edit_scan.project_name} | subject: {edit_scan.subject_label} | experiment: {edit_scan.experiment_label} | scan: {edit_scan.scan_id} | error: {str(e)}')
            return None
    
    def get_piqe(self, dataset):

        # Get dicom header with pixels
        dicom_file = self.read_dicom(dataset[0], exclude_pixels=False)[1]

        # Get pixel data as numpy array
        check_array = dicom_file.pixel_array

        # Normalize pixel array if necessary
        check_image = cv2.normalize(check_array, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Convert image from grayscale to RGB because PIQE needs a 3-channel image
        check_image = cv2.cvtColor(check_image, cv2.COLOR_GRAY2RGB)

        # Open the image using OpenCV
        #cv2.imshow('DICOM image', pixel_array)

        # Wait for a key press and then close the image window
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

        score, artifact_mask, noise_mask, activity_mask = piqe(check_image)
        #print(f"Score: {Score:.2f}")

        return dataset, score, artifact_mask, noise_mask, activity_mask


