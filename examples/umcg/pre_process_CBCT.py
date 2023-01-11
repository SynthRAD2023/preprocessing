import os
import fnmatch
import pre_process_tools as pre
import anonymize as anon

path = r'\\path\to\Data'
patient_list = os.listdir(path)
patient_list = fnmatch.filter(patient_list,'p_0*')

extra_anon_patient_list = ['p_0017','p_0060','p_0061','p_0071','p_0076','p_0083','p_0084','p_0101','p_0104','p_0176','p_0199']
script_dir = r'\\path\to\scripts'

pre_process_fn = 'CBCT_preprocess_anon'

error = []

for patient in patient_list:
    try:
        ## create CBCT_preprocessorary directory
        print(patient)

        if os.path.isdir(os.path.join(path,patient,pre_process_fn)):
            print('--CBCT_preprocess_anon dir already exists!')
        else:
            print('--create CBCT_preprocess_anon dir')
            os.mkdir(os.path.join(path,patient,pre_process_fn))

        
        ## pCT
        folders_CT = os.listdir(os.path.join(path,patient,'CT'))
        pCT_fn = fnmatch.filter(folders_CT,'*pCT*')[0]
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'pCT.nii.gz')):
            print('--pCT already converted')
        else:
            print('--convert pCT')
            pre.convert_dicom_to_nifti(os.path.join(path,patient,'CT',pCT_fn),
                                        os.path.join(path,patient,pre_process_fn,'pCT.nii.gz'))
        
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz')):
            print('--pCT already resampled!')
        else:
            print('--resample pCT')
            pre.resample(os.path.join(path,patient,pre_process_fn,'pCT.nii.gz'),
                        os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz'),(1,1,1))

        ## CBCT
        folders_CBCT = os.listdir(os.path.join(path,patient,'CBCT'))
        CBCT_fn = fnmatch.filter(folders_CBCT,'*CBCT*')[0]

        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'CBCT.nii.gz')):
            print('--CBCT already converted')
        else:
            print('--convert CBCT')
            pre.convert_dicom_to_nifti(os.path.join(path,patient,'CBCT',CBCT_fn),
                                        os.path.join(path,patient,pre_process_fn,'CBCT.nii.gz'))

        ## Register CBCT to CT 
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'CBCT_registered.nii.gz')):
            print('--CBCT already registered!')
        else:
            print('--register CBCT')
            pre.register(os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz'),
                        os.path.join(path,patient,pre_process_fn,'CBCT.nii.gz'),
                        pre.read_parameter_map(script_dir+'\param_files\parameters_CBCT_brain.txt'),
                        os.path.join(path,patient,pre_process_fn,'CBCT_registered.nii.gz'))

        ## detect face based on structures
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'face_mask.nrrd')):
            print('--face already detected!')
        else:
            print('--detect face')
            eye_struct = os.path.join(path,patient,'planning','structs','Eye_Post_L.nrrd')
            external_struct = os.path.join(path,patient,'planning','structs','External.nrrd')
            face = os.path.join(path,patient,pre_process_fn,'face_mask.nrrd')
            exist_count = extra_anon_patient_list.count(patient)
            if exist_count > 0:
                print('using umcu defacing')
                anon.detect_face_umcu(eye_struct,face)
            else:
                anon.detect_face(external_struct,eye_struct,face)
           

        ## remove face from CBCT and CT
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'CBCT_registered_anon.nii.gz')):
            print('--CBCT and CT already anonymized!')
        else:
            face = os.path.join(path,patient,pre_process_fn,'face_mask.nrrd')
            cbct = os.path.join(path,patient,pre_process_fn,'CBCT_registered.nii.gz')
            ct = os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz')
            cbct_anon = os.path.join(path,patient,pre_process_fn,'CBCT_registered_anon.nii.gz')
            ct_anon = os.path.join(path,patient,pre_process_fn,'pCT_resampled_anon.nii.gz')
            anon.remove_face(face,cbct,cbct_anon,background=-1000)
            anon.remove_face(face,ct,ct_anon,background=-1000)
        
        ## Find mask MR and CT
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'mask_CBCT.nii.gz')):
            print('--CBCT already segmented!')
        else:
            print('--segment CBCT')
            pre.segment(os.path.join(path,patient,pre_process_fn,'CBCT_registered_anon.nii.gz'),
                        os.path.join(path,patient,pre_process_fn,'mask_CBCT.nii.gz'))
        
        ## Correct mask to fit MR FOV
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'mask_CBCT_corrected.nii.gz')):
            print('--mask already corrected!')
        else:
            print('--correct mask')
            pre.correct_mask_mr(os.path.join(path,patient,pre_process_fn,'CBCT.nii.gz'),
                                os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz'),
                                os.path.join(path,patient,pre_process_fn,'CBCT_registered_parameters.txt'),
                                os.path.join(path,patient,pre_process_fn,'mask_CBCT.nii.gz'),
                                os.path.join(path,patient,pre_process_fn,'mask_CBCT_corrected.nii.gz'))

        ## crop MR and CT without applying any mask
        if os.path.isfile(os.path.join(path, patient, pre_process_fn, 'CBCT_cropped.nii.gz')):
            print('--MR already cropped!')
        else:
            print('--crop MR')
            pre.crop(os.path.join(path, patient, pre_process_fn, 'CBCT_registered_anon.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_CBCT_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'CBCT_cropped.nii.gz'))

        if os.path.isfile(os.path.join(path, patient, pre_process_fn, 'CT_cropped.nii.gz')):
            print('--CT already cropped!')
        else:
            print('--crop CT')
            pre.crop(os.path.join(path, patient, pre_process_fn, 'pCT_resampled_anon.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_CBCT_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'CT_cropped.nii.gz'))

        if os.path.isfile(os.path.join(path, patient, pre_process_fn, 'mask_cropped.nii.gz')):
            print('--mask already cropped!')
        else:
            print('--crop mask')
            pre.crop(os.path.join(path, patient, pre_process_fn, 'mask_CBCT_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_CBCT_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_cropped.nii.gz'))

        ## generate overview image
        if os.path.isfile(os.path.join(path, patient, 'overview_CBCT.png')):
            print('--overview already generated!')
        else:
            print('--generating overview')
            pre.generate_overview(os.path.join(path, patient, pre_process_fn, 'CBCT_cropped.nii.gz'),
                                    os.path.join(path, patient, pre_process_fn, 'CT_cropped.nii.gz'),
                                    os.path.join(path, patient, pre_process_fn, 'mask_cropped.nii.gz'),
                                    os.path.join(path, patient, 'overview_CBCT.png'),title=patient)
    except:
        error.append(patient)
        with open(os.path.join(path,'log.txt'),'a') as f:
            f.write(patient)