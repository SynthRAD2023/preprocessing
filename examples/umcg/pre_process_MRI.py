import os
import fnmatch
import pre_process_tools as pre
import anonymize as anon

path = r'\\path\to\Data'
patient_list = os.listdir(path)
patient_list = fnmatch.filter(patient_list,'p_0*')

extra_anon_patient_list = ['p_0017','p_0060','p_0061','p_0071','p_0076','p_0083','p_0084','p_0101','p_0104','p_0176','p_0199']
script_dir = r'\\path\to\scripts'

pre_process_fn = 'MRI_preprocess_anon'
error=[]

for patient in patient_list:
    try:
        ## create MR_preprocess directory
        print(patient)

        if os.path.isdir(os.path.join(path,patient,pre_process_fn)):
            print('--MRI_preprocess dir already exists!')
        else:
            print('--create MRI_preprocess dir')
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

        ## MRI
        folders_MRI = os.listdir(os.path.join(path,patient,'MRI'))
        MRI_fn = fnmatch.filter(folders_MRI,'**t1*gd**')[0]

        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'MRI.nii.gz')):
            print('--MRI already converted')
        else:
            print('--convert MRI')
            pre.convert_dicom_to_nifti(os.path.join(path,patient,'MRI',MRI_fn),
                                        os.path.join(path,patient,pre_process_fn,'MRI.nii.gz'))

        ## Register MRI to CT 
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'MRI_registered.nii.gz')):
            print('--MRI already registered!')
        else:
            print('--register MRI')
            pre.register(os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz'),
                        os.path.join(path,patient,pre_process_fn,'MRI.nii.gz'),
                        pre.read_parameter_map(script_dir+'\param_files\parameters_MRI_brain.txt'),
                        os.path.join(path,patient,pre_process_fn,'MRI_registered.nii.gz'))

        ## remove face from CBCT and CT
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'MRI_registered_anon.nii.gz')):
            print('--CBCT and CT already anonymized!')
        else:
            face = os.path.join(path,patient,'CBCT_preprocess_anon','face_mask.nrrd')
            cbct = os.path.join(path,patient,pre_process_fn,'MRI_registered.nii.gz')
            ct = os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz')
            cbct_anon = os.path.join(path,patient,pre_process_fn,'MRI_registered_anon.nii.gz')
            ct_anon = os.path.join(path,patient,pre_process_fn,'pCT_resampled_anon.nii.gz')
            anon.remove_face(face,cbct,cbct_anon,background=0)
            anon.remove_face(face,ct,ct_anon,background=-1000)

        ## Find mask MR and CT
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'mask_MRI.nii.gz')):
            print('--MRI already segmented!')
        else:
            print('--segment MRI')
            pre.segment(os.path.join(path,patient,pre_process_fn,'MRI_registered_anon.nii.gz'),
                        os.path.join(path,patient,pre_process_fn,'mask_MRI.nii.gz'))
        
        ## Correct mask to fit MR FOV
        if os.path.isfile(os.path.join(path,patient,pre_process_fn,'mask_MRI_corrected.nii.gz')):
            print('--mask already corrected!')
        else:
            print('--correct mask')
            pre.correct_mask_mr(os.path.join(path,patient,pre_process_fn,'MRI.nii.gz'),
                                os.path.join(path,patient,pre_process_fn,'pCT_resampled.nii.gz'),
                                os.path.join(path,patient,pre_process_fn,'MRI_registered_parameters.txt'),
                                os.path.join(path,patient,pre_process_fn,'mask_MRI.nii.gz'),
                                os.path.join(path,patient,pre_process_fn,'mask_MRI_corrected.nii.gz'))

        ## crop MR and CT without applying any mask
        if os.path.isfile(os.path.join(path, patient, pre_process_fn, 'MRI_cropped.nii.gz')):
            print('--MR already cropped!')
        else:
            print('--crop MR')
            pre.crop(os.path.join(path, patient, pre_process_fn, 'MRI_registered_anon.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_MRI_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'MRI_cropped.nii.gz'))

        if os.path.isfile(os.path.join(path, patient, pre_process_fn, 'CT_cropped.nii.gz')):
            print('--CT already cropped!')
        else:
            print('--crop CT')
            pre.crop(os.path.join(path, patient, pre_process_fn, 'pCT_resampled_anon.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_MRI_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'CT_cropped.nii.gz'))

        if os.path.isfile(os.path.join(path, patient, pre_process_fn, 'mask_cropped.nii.gz')):
            print('--mask already cropped!')
        else:
            print('--crop mask')
            pre.crop(os.path.join(path, patient, pre_process_fn, 'mask_MRI_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_MRI_corrected.nii.gz'),
                        os.path.join(path, patient, pre_process_fn, 'mask_cropped.nii.gz'))

        ## generate overview image
        if os.path.isfile(os.path.join(path, patient, 'overview_MR.png')):
            print('--overview already generated!')
        else:
            print('--generating overview')
            pre.generate_overview(os.path.join(path, patient, pre_process_fn, 'MRI_cropped.nii.gz'),
                                    os.path.join(path, patient, pre_process_fn, 'CT_cropped.nii.gz'),
                                    os.path.join(path, patient, pre_process_fn, 'mask_cropped.nii.gz'),
                                    os.path.join(path, patient, 'overview_MR.png'),title=patient)
    except:
        error.append(patient)
        with open(os.path.join(path,'log.txt'),'a') as f:
            f.write(patient)