#!/bin/bash

# Modify according to the location of your data
initial='/path/to/data/directory'
dirOut='/path/to/output/directory'

declare -a patients
readarray patients < ./pat_list_brain_mri2ct.txt
readarray -t patients < ./pat_list_brain_mri2ct.txt

for patIndex in $(eval echo {0..$((${#patients[@]}-1))})
do
	patient=`echo ${patients[patIndex]} | awk '{print $1}'`
  dateCT=`echo ${patients[patIndex]} | awk '{print $2}'`
  dateMR=`echo ${patients[patIndex]} | awk '{print $3}'`
  phase=`echo ${patients[patIndex]} | awk '{print $4}'`

  dirCT=${initial}${patient}/RTset/${dateCT}/
  dirMR=${initial}${patient}/MRI/${dateMR}/

  echo -e $patient $dateCT $dateMR $phase

  TMP=${dirOut}${phase}/${patient}/
  mkdir -p $TMP

  echo "Converting dcm to nifti"
  python ../pre_process_tools.py convert_dicom_to_nifti --i ${dirCT}Dcm/ --o ${TMP}ct_or.nii.gz
  python ../pre_process_tools.py convert_dicom_to_nifti --i ${dirMR}Dcm/ --o ${TMP}mr_or.nii.gz

# Resample CT to 1x1x1
  echo "Resampling CT"
  python ../pre_process_tools.py resample --i ${TMP}ct_or.nii.gz --o ${TMP}ct_resampled.nii.gz --s 1 1 1

# Register MRI to CT according to the parameter file specified
  echo "Registering..."
  python ../pre_process_tools.py register --f ${TMP}ct_resampled.nii.gz --m ${TMP}mr_or.nii.gz --o ${TMP}mr_T1_registered.nii.gz --p parameters_MR.txt

# Mask MR & CT
  echo "Masking"
  python ../pre_process_tools.py segment --i ${TMP}mr_T1_registered.nii.gz --o ${TMP}mask_MR.nii.gz

# These three are the final images that are provided for each patient
# Crop to dilated mask_MR
  python ../pre_process_tools.py crop --i ${TMP}ct_resampled.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}ct_cropped.nii.gz
  python ../pre_process_tools.py crop --i ${TMP}mr_T1_registered.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mr_cropped.nii.gz
# Crop the mask
  python ../pre_process_tools.py crop --i ${TMP}mask_MR.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mask_cropped.nii.gz

<<'Comm'

# Optional, if desired to apply mask to image and crop aacordingly

# Mask CT, not used
  #python ../pre_process_tools.py segment --i ${TMP}ct_resampled.nii.gz --o ${TMP}mask_CT.nii.gz

#Mask CT and MRI to mask_MR
  echo "Apply mask"
  python ../pre_process_tools.py mask_ct --i ${TMP}ct_resampled.nii.gz --mask_in ${TMP}mask_MR.nii.gz --o ${TMP}ct_resampled_masked.nii.gz
  python ../pre_process_tools.py mask_mr --i ${TMP}mr_T1_registered.nii.gz --mask_in ${TMP}mask_MR.nii.gz --o ${TMP}mr_T1_registered_masked.nii.gz.nii.gz

# Crop to dilated mask after having applied the masking
  python ../pre_process_tools.py crop --i ${TMP}ct_resampled_masked.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}ct_cropped_masked.nii.gz
  python ../pre_process_tools.py crop --i ${TMP}mr_T1_registered_masked.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mr_cropped_masked.nii.gz
done