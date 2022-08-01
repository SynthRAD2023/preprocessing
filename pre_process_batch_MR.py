import os 
import fnmatch
import pre_process_tools as pre

path = r'\\zkh\Appdata\RTDicom\GalaponAV\Dataset_Brain'
patient_list = os.listdir(path)
patient_list = fnmatch.filter(patient_list,'p0*')

for patient in patient_list:
    ## create temporary directory
    print(patient)

    if os.path.isdir(os.path.join(path,patient,'temp')):
        print('--temp dir already exists!')
    else:
        print('--create temp dir')
        os.mkdir(os.path.join(path,patient,'temp'))

    
    ## pCT
    folders_CT = os.listdir(os.path.join(path,patient,'CT'))
    pCT_fn = fnmatch.filter(folders_CT,'*pCT*')[0]
    if os.path.isfile(os.path.join(path,patient,'temp','pCT.nii.gz')):
        print('--pCT already converted')
    else:
        print('--convert pCT')
        pre.convert_dicom_to_nifti(os.path.join(path,patient,'CT',pCT_fn),os.path.join(path,patient,'temp','pCT.nii.gz'))
    
    if os.path.isfile(os.path.join(path,patient,'temp','pCT_resampled.nii.gz')):
        print('--pCT already resampled!')
    else:
        print('--resample pCT')
        pre.resample(os.path.join(path,patient,'temp','pCT.nii.gz'),os.path.join(path,patient,'temp','pCT_resampled.nii.gz'),(1,1,1))

    ## MR
    folders_MR = os.listdir(os.path.join(path,patient,'MRI'))
    MR_fn = fnmatch.filter(folders_MR,'*t1*gd*')[0]

    if os.path.isfile(os.path.join(path,patient,'temp','MR_T1_gd.nii.gz')):
        print('--MR already converted')
    else:
        print('--convert MR')
        pre.convert_dicom_to_nifti(os.path.join(path,patient,'MRI',MR_fn),os.path.join(path,patient,'temp','MR_T1_gd.nii.gz'))

    ## Register MR to CT 
    if os.path.isfile(os.path.join(path,patient,'temp','MR_T1_gd_registered.nii.gz')):
        print('--MR already registered!')
    else:
        print('--register MR')
        pre.register(os.path.join(path,patient,'temp','pCT_resampled.nii.gz'),os.path.join(path,patient,'temp','MR_T1_gd.nii.gz'),pre.create_parameter_map(),os.path.join(path,patient,'temp','MR_T1_gd_registered.nii.gz'))

    ## mask MR and CT
    if os.path.isfile(os.path.join(path,patient,'temp','mask_MR.nii.gz')):
        print('--MR already segmented!')
    else:
        print('--segment MR')
        pre.segment(os.path.join(path,patient,'temp','MR_T1_gd_registered.nii.gz'),os.path.join(path,patient,'temp','mask_MR.nii.gz'))
    
    if os.path.isfile(os.path.join(path,patient,'temp','MR_T1_gd_registered_masked.nii.gz')):
        print('--MR already masked!')
    else:
        print('--mask MR')
        pre.mask(os.path.join(path,patient,'temp','MR_T1_gd_registered.nii.gz'),os.path.join(path,patient,'temp','mask_MR.nii.gz'),0,os.path.join(path,patient,'temp','MR_T1_gd_registered_masked.nii.gz'))
    
    if os.path.isfile(os.path.join(path,patient,'temp','pCT_resampled_masked.nii.gz')):
        print('--pCT already masked')
    else:
        print('--mask pCT')
        pre.mask(os.path.join(path,patient,'temp','pCT_resampled.nii.gz'),os.path.join(path,patient,'temp','mask_MR.nii.gz'),-1000,os.path.join(path,patient,'temp','pCT_resampled_masked.nii.gz'))

    ## crop MR and CT and mask
    if os.path.isfile(os.path.join(path,patient,'temp','MR_cropped.nii.gz')):
        print('--MR already cropped!')
    else:
        print('--crop MR')
        pre.crop(os.path.join(path,patient,'temp','MR_T1_gd_registered_masked.nii.gz'),os.path.join(path,patient,'temp','mask_MR.nii.gz'),os.path.join(path,patient,'temp','MR_cropped.nii.gz'))
    
    if os.path.isfile(os.path.join(path,patient,'temp','CT_cropped.nii.gz')):
        print('--CT already cropped!')
    else:
        print('--crop CT')
        pre.crop(os.path.join(path,patient,'temp','pCT_resampled_masked.nii.gz'),os.path.join(path,patient,'temp','mask_MR.nii.gz'),os.path.join(path,patient,'temp','CT_cropped.nii.gz'))
    
    if os.path.isfile(os.path.join(path,patient,'temp','mask_cropped.nii.gz')):
        print('--mask already cropped!')
    else:
        print('--crop mask')
        pre.crop(os.path.join(path,patient,'temp','mask_MR.nii.gz'),os.path.join(path,patient,'temp','mask_MR.nii.gz'),os.path.join(path,patient,'temp','mask_cropped.nii.gz'))
