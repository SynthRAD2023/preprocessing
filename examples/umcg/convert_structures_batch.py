import SimpleITK as sitk
import numpy as np 
import subprocess as sub
import os
import fnmatch
import shutil
import convert_structures as conv

data_dir = r'\\path\\to\\data\\directory'

cases = os.listdir(data_dir)
cases = fnmatch.filter(cases,'p_0*')
cases = ['p_0013','p_0019','p_0035','p_0037','p_0053','p_0060','p_0084','p_0104','p_0176','p_0199','p_0004','p_0010','p_0025','p_0032','p_0046','p_0055','p_0056','p_0058','p_0061','p_0065','p_0067','p_0070','p_0088','p_0101','p_0103','p_0110','p_0144','p_0183','p_0191','p_0196']


for case in cases:

    planning_path = os.path.join(data_dir,case,'planning')

    if os.path.isdir(planning_path):
        print(f'{planning_path} already exists')
    else:
        os.mkdir(planning_path)

    print(case)

    # try:
    #     unapproved = os.listdir(os.path.join(data_dir,case,'CT','RS Unapproved Structure Set'))
    #     for rtss in unapproved:
    #         shutil.copyfile(os.path.join(data_dir,case,'CT','RS Unapproved Structure Set',rtss),
    #                         os.path.join(planning_path,rtss[:-4]+'_unapproved.dcm'))
    #         conv.struct_to_nrrd(os.path.join(planning_path,rtss[:-4]+'_unapproved.dcm'),os.path.join(planning_path,'structs'))
    # except:
    #     print('no unapproved structure sets')
    
    # try:
    #     approved = os.listdir(os.path.join(data_dir,case,'CT','RS Approved Structure Set'))
    #     for rtss in approved:
    #         shutil.copyfile(os.path.join(data_dir,case,'CT','RS Approved Structure Set',rtss),
    #                         os.path.join(planning_path,rtss[:-4]+'_approved.dcm'))
    #         conv.struct_to_nrrd(os.path.join(planning_path,rtss[:-4]+'_approved.dcm'),os.path.join(planning_path,'structs'))
    # except:
    #     print('no approved structure sets')

    # try:
    #     conv.nii_to_nrrd(os.path.join(data_dir,case,'CBCT_preprocess','pCT_resampled.nii.gz'),os.path.join(planning_path,'pCT.nrrd'))
    
    #     structures = fnmatch.filter(os.listdir(os.path.join(planning_path,'structs')),'*.nrrd')
    #     ref_CT = sitk.ReadImage(os.path.join(planning_path,'pCT.nrrd'))
        
    #     for structure in structures:
    #         structure_path = os.path.join(planning_path,'structs',structure)
    #         conv.resample_structure(structure_path,ref_CT,structure_path,ref_CT_is_sitk=True)
    # except:
    #     print('print error with conversion or resampling')

    # try:
    #     structures = fnmatch.filter(os.listdir(os.path.join(planning_path,'structs')),'*.nrrd')
    #     for structure in structures:
    #         structure_path = os.path.join(planning_path,'structs',structure)
    #         ref_mask_path = os.path.join(data_dir,case,'CBCT_preprocess_anon','mask_cropped.nii.gz')
    #         output_path = os.path.join(planning_path,'structs',structure[:-5]+'_cropped.nrrd')
    #         if os.path.isfile(output_path):
    #             print(f'{structure} already cropped!')
    #         else:
    #             print(f'cropping {structure}...')
    #             conv.crop_structure(structure_path,ref_mask_path,output_path)
    # except:
    #     print(f'error with cropping {case}')
    

    try:
        structures = fnmatch.filter(os.listdir(os.path.join(planning_path,'structs')),'*.nrrd')
        structures_not_cropped = [ x for x in structures if "_cropped" not in x ]
        for structure in structures_not_cropped:
            structure_path = os.path.join(planning_path,'structs',structure)
            ref_mask_path = os.path.join(data_dir,case,'MRI_preprocess_anon','mask_cropped.nii.gz')
            output_path = os.path.join(planning_path,'structs',structure[:-5]+'_cropped_mri.nrrd')
            if os.path.isfile(output_path):
                print(f'{structure} already cropped!')
            else:
                print(f'cropping {structure}...')
                conv.crop_structure(structure_path,ref_mask_path,output_path)
    except:
        print(f'error with cropping {case}')
