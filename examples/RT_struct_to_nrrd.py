import SimpleITK as sitk
import os
import fnmatch
import shutil
import convert_structures as conv

data_dir = r'\\path\\to\\data\\directory'

cases = os.listdir(data_dir)
cases = fnmatch.filter(cases,'p_0*')

for case in cases:

    planning_path = os.path.join(data_dir,case,'planning')

    if os.path.isdir(planning_path):
        print(f'{planning_path} already exists')
    else:
        os.mkdir(planning_path)

    print(case)

    try:
        unapproved = os.listdir(os.path.join(data_dir,case,'CT','RS Unapproved Structure Set'))
        for rtss in unapproved:
            shutil.copyfile(os.path.join(data_dir,case,'CT','RS Unapproved Structure Set',rtss),
                            os.path.join(planning_path,rtss[:-4]+'_unapproved.dcm'))
            conv.struct_to_nrrd(os.path.join(planning_path,rtss[:-4]+'_unapproved.dcm'),os.path.join(planning_path,'structs'))
    except:
        print('no unapproved structure sets')
    
    try:
        approved = os.listdir(os.path.join(data_dir,case,'CT','RS Approved Structure Set'))
        for rtss in approved:
            shutil.copyfile(os.path.join(data_dir,case,'CT','RS Approved Structure Set',rtss),
                            os.path.join(planning_path,rtss[:-4]+'_approved.dcm'))
            conv.struct_to_nrrd(os.path.join(planning_path,rtss[:-4]+'_approved.dcm'),os.path.join(planning_path,'structs'))
    except:
        print('no approved structure sets')

    try:
        conv.nii_to_nrrd(os.path.join(data_dir,case,'CBCT_preprocess','pCT_resampled.nii.gz'),os.path.join(planning_path,'pCT.nrrd'))
    
        structures = fnmatch.filter(os.listdir(os.path.join(planning_path,'structs')),'*.nrrd')
        ref_CT = sitk.ReadImage(os.path.join(planning_path,'pCT.nrrd'))
        
        for structure in structures:
            structure_path = os.path.join(planning_path,'structs',structure)
            conv.resample_structure(structure_path,ref_CT,structure_path,ref_CT_is_sitk=True)
    except:
        print('print error with conversion or resampling')
