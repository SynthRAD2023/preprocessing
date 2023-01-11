import extract_tags_tools as ext
import os
import fnmatch

dataset_path = r'\\path\to\dataset'

tags_MR = ext.read_tags(r'Z:\path\to\code\preprocessing\param_files\tags_MR.txt')
tags_CT = ext.read_tags(r'Z:\path\to\code\preprocessing\param_files\tags_CT.txt')

print(tags_MR)

cases = os.listdir(dataset_path)
cases = fnmatch.filter(cases,'p0*')

MR_dataset = {}
CT_dataset = {}

for i in range(len(cases)):
    print(i)
    try:
        MR_dirs = fnmatch.filter(os.listdir(os.path.join(dataset_path,cases[i],'MRI')),'t1_mprage_sag_p2_*_MPR_*')
        MR_preprocessed = fnmatch.filter(os.listdir(os.path.join(dataset_path,cases[i],'temp')),'MR_cropped.nii.gz')
        mr_tags_case = ext.extract_tags(os.path.join(dataset_path,cases[i],'MRI',MR_dirs[0]),tags_MR,MR_preprocessed)
        key = str(cases[i])
        MR_dataset[key]=mr_tags_case
    except:
        print(cases[i]+' MR error!')

    try:
        CT_dirs = fnmatch.filter(os.listdir(os.path.join(dataset_path,cases[i],'CT')),'*pCT*')
        CT_preprocessed = fnmatch.filter(os.listdir(os.path.join(dataset_path,cases[i],'temp')),'CT_cropped.nii.gz')
        ct_tags_case = ext.extract_tags(os.path.join(dataset_path,cases[i],'CT',CT_dirs[0]),tags_CT,CT_preprocessed)
        key = str(cases[i])
        CT_dataset[key]=ct_tags_case
    except:
        print(cases[i]+' CT error!')
    

ext.write_dict_to_csv(CT_dataset,os.path.join(dataset_path,'CT_MR_UMCG_brain.csv'),tags_CT)
ext.convert_csv_to_xlsx(os.path.join(dataset_path,'CT_MR_UMCG_brain.csv'),os.path.join(dataset_path,'CT_MR_UMCG_brain.xlsx'))

ext.write_dict_to_csv(MR_dataset,os.path.join(dataset_path,'MR_UMCG_brain.csv'),tags_MR)
ext.convert_csv_to_xlsx(os.path.join(dataset_path,'MR_UMCG_brain.csv'),os.path.join(dataset_path,'MR_UMCG_brain.xlsx'))