#!/bin/bash
# Run this in a OS with unix-based syntax

# Measure Elapsed time of the script:
START_TIME=$SECONDS

# Modify according to the location of your data
initial='/path/to/data/directory'
dirOut='/path/to/output/directory'
Task='1' # 1 = MRI-to-CT, 2 = CBCT-to-CT
Center='A'
AnatomicalSite='B'  # B = brain, P = pelvis

rm ${dirOut}overview/MR_${Center}_brain.csv
rm ${dirOut}overview/CT_${Center}_brain.csv
rm ${dirOut}overview/CT_${Center}_brain.xlsx

tags_MR='./param_files/tags_MR.txt'
tags_CT='./param_files/tags_CT.txt'

#Prepare calculation of elapsed time for the script and logging
Now=`date`
script_name=$(basename $0)
echo -e $script_name $Now
echo -e $script_name $Now  >> ${dirOut}Logfile.txt
printf 'pts \t date_ct \t date_mr \t phase \n' >> ${dirOut}Logfile.txt

declare -a patients
readarray patients < ./pat_list_brain_mri2ct.txt
readarray -t patients < ./pat_list_brain_mri2ct.txt

for patIndex in $(eval echo {0..$((${#patients[@]}-1))})
do
	patient=`echo ${patients[patIndex]} | awk '{print $1}'`
  dateCT=`echo ${patients[patIndex]} | awk '{print $2}'`
  dateMR=`echo ${patients[patIndex]} | awk '{print $3}'`
  phase=`echo ${patients[patIndex]} | awk '{print $4}'`

  patientnr=${patient:1:3}
  dirCT=${initial}${patient}/RTset/${dateCT}/
  dirMR=${initial}${patient}/MRI/${dateMR}/

  pts=${Task}${AnatomicalSite}${Center}${patientnr}
  echo -e $patient $patientnr $dateCT $dateMR $phase $pts
  printf '%s \t %s \t %s \t %s \n' $pts $dateCT $dateMR $phase   >> ${dirOut}Logfile.txt

  TMP=${dirOut}${phase}/${patient}/
  mkdir -p $TMP

  echo "Converting dcm to nifti"
  python ../pre_process_tools.py convert_dicom_to_nifti --i ${dirCT}Dcm/ --o ${TMP}ct_or.nii.gz
  python ../pre_process_tools.py convert_dicom_to_nifti --i ${dirMR}Dcm/ --o ${TMP}mr_or.nii.gz

# Resample CT to 1x1x1
  echo "Resampling CT"
  python ../pre_process_tools.py resample --i ${TMP}ct_or.nii.gz --o ${TMP}ct_resampled.nii.gz --s 1 1 1

#Register MRI to CT according to the parameter file specified
  echo "Registering..."
  python ../pre_process_tools.py register --f ${TMP}ct_resampled.nii.gz --m ${TMP}mr_or.nii.gz --o ${TMP}mr_T1_registered.nii.gz --p ./param_files/parameters_MR.txt
#Mask MR
  echo "Masking"
  python ../pre_process_tools.py segment --i ${TMP}mr_T1_registered.nii.gz --o ${TMP}mask_MR.nii.gz --r 12
#Mask CT, not used
#  python ../pre_process_tools.py segment --i ${TMP}CT_cropped.nii.gz --o ${TMP}mask_CT.nii.gz

#Correct FOV
  python ../pre_process_tools.py correct --i ${TMP}mr_or.nii.gz --ii ${TMP}ct_resampled.nii.gz \
  --f ${TMP}mr_T1_registered_parameters.txt --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mask_MR_corrected.nii.gz

# These three are the final images that are provided for each patient
#Mask MRI and resampled to cropped FOV
  python ../pre_process_tools.py crop --i ${TMP}ct_resampled.nii.gz --mask_crop ${TMP}mask_MR_corrected.nii.gz --o ${TMP}ct_crop.nii.gz #--mask_value -1000
  python ../pre_process_tools.py crop --i ${TMP}mr_T1_registered.nii.gz --mask_crop ${TMP}mask_MR_corrected.nii.gz --o ${TMP}mr_crop.nii.gz #--mask_value 0
  python ../pre_process_tools.py crop --i ${TMP}mask_MR.nii.gz --mask_crop ${TMP}mask_MR_corrected.nii.gz --o ${TMP}mask_crop.nii.gz #--mask_value 0

# Removing the images that are not shared
  echo "Removing "
  rm ${TMP}ct* ${TMP}mr* ${TMP}mask_MR* ${TMP}mask_CT*

#Generate overview
   python ../pre_process_tools.py overview --i ${TMP}mr_crop.nii.gz --ii ${TMP}ct_crop.nii.gz --mask_in  ${TMP}mask_crop.nii.gz \
   --o ${dirOut}overview/${pts}_mr_ct_mask_${phase}.png

# Extract from dicom to csv/excel

   python ../extract_tags_tools.py extract --path ${dirMR}Dcm/ --tags ${tags_MR} --pre ${TMP}mr_crop.nii.gz \
   --csv ${dirOut}overview/MR_UMCU_brain.csv

   python ../extract_tags_tools.py extract --path ${dirCT}Dcm/ --tags ${tags_CT} --pre ${TMP}ct_crop.nii.gz \
   --csv ${dirOut}overview/CT_UMCU_brain.csv

<<'Comm'

# Optional, if desired to apply mask to image and crop accordingly

# Mask CT, not used
  #python ../pre_process_tools.py segment --i ${TMP}ct_resampled.nii.gz --o ${TMP}mask_CT.nii.gz

#Mask CT and MRI to mask_MR
  echo "Apply mask"
  python ../pre_process_tools.py mask_ct --i ${TMP}ct_resampled.nii.gz --mask_in ${TMP}mask_MR.nii.gz --o ${TMP}ct_resampled_masked.nii.gz
  python ../pre_process_tools.py mask_mr --i ${TMP}mr_T1_registered.nii.gz --mask_in ${TMP}mask_MR.nii.gz --o ${TMP}mr_T1_registered_masked.nii.gz.nii.gz

# Crop to dilated mask after having applied the masking
  python ../pre_process_tools.py crop --i ${TMP}ct_resampled_masked.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}ct_cropped_masked.nii.gz
  python ../pre_process_tools.py crop --i ${TMP}mr_T1_registered_masked.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mr_cropped_masked.nii.gz
Comm
done

python ../extract_tags_tools.py toxlsx --csv ${dirOut}overview/MR_UMCU_brain.csv \
--xlsx ${dirOut}overview/CT_MR_UMCU_brain.xlsx --tags "MR"

python ../extract_tags_tools.py toxlsx --csv ${dirOut}overview/CT_UMCU_brain.csv \
--xlsx ${dirOut}overview/CT_MR_UMCU_brain.xlsx --tags "CT"

ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo 'Time elapsed to prepare the data: ' $(($ELAPSED_TIME/60)) ' min' $(($ELAPSED_TIME%60)) ' s'
echo 'Time elapsed to prepare the data: ' $(($ELAPSED_TIME/60)) ' min' $(($ELAPSED_TIME%60)) ' s' >> ${dirOut}Logfile.txt
