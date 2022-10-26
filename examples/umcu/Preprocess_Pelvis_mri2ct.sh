#!/bin/bash

# Measure Elapsed time of the script:
START_TIME=$SECONDS

Task='1'
Center='A'
AnatomicalSite='P'
Site='pelvis'
initial='/nfs/arch11/researchData/PROJECT/MRonlyTP/Gen_sCT/data/'
dirOut='/nfs/arch11/researchData/PROJECT/SynthRAD/2023/dataset_UMCU/Task1/'${Site}'/'

Flag_preproc=123 	# set the flag to 1234 to activate the download
Flag_extract=1234
Flag_overview=1234
Flag_remove=123   # this is for full debug

if [ $Flag_extract == '1234' ]; then
  rm ${dirOut}overview/MR_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_MR_UMCU_${Site}.xlsx
fi
## these paths contain all the fixed provided tools
## not to be modified by the user
preproc='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/pre_process_tools_umc.py'
extract='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/extract_tags_tools_umc.py'

tags_MR='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/param_files/tags_MR.txt'
tags_CT='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/param_files/tags_CT.txt'
param_reg='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/param_files/parameters_MR.txt'

Now=`date`
script_name=$(basename $0)
echo -e $script_name $Now
echo -e $script_name $Now  >> ${dirOut}Logfile.txt
printf 'pts \t date_ct \t date_mr \t phase \n' >> ${dirOut}Logfile.txt

declare -a patients
readarray patients < ./pat_list_${Site}_mri2ct.txt
readarray -t patients < ./pat_list_${Site}_mri2ct.txt

for patIndex in $(eval echo {0..$((${#patients[@]}-1))})
do
	patient=`echo ${patients[patIndex]} | awk '{print $1}'`
  dateCT=`echo ${patients[patIndex]} | awk '{print $3}'`
  dateMR=`echo ${patients[patIndex]} | awk '{print $4}'`
  phase=`echo ${patients[patIndex]} | awk '{print $5}'`

  patientnr=${patient:1:3}
  dirCT=${initial}${patient}/RTset/${dateCT}/
  dirMR=${initial}${patient}/MRI/${dateMR}/

  pts=${Task}${AnatomicalSite}${Center}${patientnr}
  echo -e $patient $patientnr $dateCT $dateMR $phase $pts
  printf '%s \t %s \t %s \t %s \n' $pts $dateCT $dateMR $phase   >> ${dirOut}Logfile.txt

  TMP=${dirOut}${phase}/${pts}/
  mkdir -p $TMP

#  Dcm_CT=$(find ${initial}${patientAnon}/ct/dicom/ -type f -name ct*dcm | head -1)
#  Dcm_MR=$(find ${initial}${patientAnon}/conebeam_ct/dicom/ -type f -name *dcm | head -1)

  Hdf_CT=$(find ${dirCT}Hdf/ -type f -name MOD=CT*hdf | head -1)
  echo -e "Hdf CT: " $Hdf_CT

#(contains(SeqMR{ll},"IP3DTFE") | contains(SeqMR{ll},"IPW")) && ~contains(SeqMR{ll},"MRCAT") && ~contains(SeqMR{ll},"gd")
  find ${dirMR} -maxdepth 1 -type d \( -ipath "*ip*" -o -ipath "*mrcat*" \) -print
  dir_MR=$(find ${dirMR} -maxdepth 1 -type d \( -ipath "*ip*" -o -ipath "*mrcat*" \) -print | head -1)
  Hdf_MR=$(find ${dir_MR}/Hdf -type f -name MOD=MR*YPE=IP*hdf | head -1)
  echo -e "Hdf MR: " $Hdf_MR


  if [ $Flag_preproc == '1234' ]; then
<<'Ciao'
Ciao
  hdf2gipl.jar --infile $Hdf_CT --outfile ${TMP}ct_or.gipl
  ConvertSitk --infile ${TMP}ct_or.gipl --outfile ${TMP}ct_or.nii.gz
  hdf2gipl.jar --infile $Hdf_MR --outfile ${TMP}mr_or.gipl
  ConvertSitk --infile ${TMP}mr_or.gipl --outfile ${TMP}mr_or.nii.gz

# From here Adrian steps

# Resample CT to 1x1x2.5
  echo "Resampling... "
  python ${preproc} resample --i ${TMP}ct_or.nii.gz --o ${TMP}ct_resampled.nii.gz --s 1 1 2.5

  echo "Clean border MRI... "
  python ${preproc} clean --i ${TMP}mr_or.nii.gz --o ${TMP}mr_clean.nii.gz

#Register MRI to CT according to the parameter file specified
  echo "Registering... "
  python ${preproc} register --f ${TMP}ct_resampled.nii.gz --m ${TMP}mr_clean.nii.gz --o ${TMP}mr_IP_registered.nii.gz --p ${param_reg}
#Mask MR
  echo "Segmenting MR... "
  python ${preproc} segment --i ${TMP}mr_IP_registered.nii.gz --o ${TMP}mask_MR.nii.gz --r 12
  echo "Correcting FOV... "
  python ${preproc} correct --i ${TMP}mr_or.nii.gz --ii ${TMP}ct_resampled.nii.gz \
  --f ${TMP}mr_IP_registered_parameters.txt --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mask_MR_corrected.nii.gz


#Mask MRI and resampled to cropped CT and MRI to mask_MR
  echo "Cropping... "
  python ${preproc} crop --i ${TMP}ct_resampled.nii.gz --mask_crop ${TMP}mask_MR_corrected.nii.gz --o ${TMP}ct_crop.nii.gz #--mask_value -1000
  python ${preproc} crop --i ${TMP}mr_IP_registered.nii.gz --mask_crop ${TMP}mask_MR_corrected.nii.gz --o ${TMP}mr_crop.nii.gz #--mask_value 0
  python ${preproc} crop --i ${TMP}mask_MR.nii.gz --mask_crop ${TMP}mask_MR_corrected.nii.gz --o ${TMP}mask_crop.nii.gz #--mask_value 0

#Mask CT, not used
  echo "Segmenting CT... "
  python ${preproc} segment --i ${TMP}ct_crop.nii.gz --o ${TMP}mask_CT.nii.gz

#Crop to dilated mask_MR
  #python ${preproc} crop --i ${TMP}ct_resampled.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}ct_cropped.nii.gz
  #python ${preproc} crop --i ${TMP}mr_IP_registered.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mr_cropped.nii.gz

  if [ $Flag_remove == '1234' ]; then
  echo "Removing "
  rm ${TMP}ct_o* ${TMP}ct_r* ${TMP}mr_I* ${TMP}mr_cl* ${TMP}mr_o* ${TMP}mask_MR* ${TMP}mask_CT*
  fi
  fi

<<'Comm'
Comm

  if [ $Flag_overview == '1234' ]; then
#Generate overview
   echo "Overview png... "
   python ${preproc} overview --i ${TMP}mr_crop.nii.gz --ii ${TMP}ct_crop.nii.gz --mask_in  ${TMP}mask_crop.nii.gz \
   --o ${dirOut}overview/${pts}_mr_ct_mask_${phase}.png
  fi

  if [ $Flag_extract == '1234' ]; then

# Extract from dicom to csv/excel
#Extracting dicomtags to csv
  echo "CSV... "
  python ${extract} extract --path ${dir_MR}/Dcm/ --tags ${tags_MR} --pre ${TMP}mr_crop.nii.gz \
  --csv ${dirOut}overview/MR_UMCU_${Site}.csv --pt $pts --phase $phase

  python ${extract} extract --path ${dirCT}/Dcm/ --tags ${tags_CT} --pre ${TMP}ct_crop.nii.gz \
  --csv ${dirOut}overview/CT_UMCU_${Site}.csv --pt $pts --phase $phase

  fi

done

if [ $Flag_extract == '1234' ]; then
echo "Excel... "
python ${extract} toxlsx --csv ${dirOut}overview/MR_UMCU_${Site}.csv \
--xlsx ${dirOut}overview/CT_MR_UMCU_${Site}.xlsx --tags "MR"

python ${extract} toxlsx --csv ${dirOut}overview/CT_UMCU_${Site}.csv \
--xlsx ${dirOut}overview/CT_MR_UMCU_${Site}.xlsx --tags "CT"
fi
#today=`date +%Y%m%d`
#mkdir -p ${dirOut}overview/${today}
#cp ${dirOut}overview/*.csv ${dirOut}overview/${today}/
#cp ${dirOut}overview/CT_MR_UMCU_brain.xlsx ${dirOut}overview/${today}/

ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo 'Time elapsed to prepare the data: ' $(($ELAPSED_TIME/60)) ' min' $(($ELAPSED_TIME%60)) ' s'
echo 'Time elapsed to prepare the data: ' $(($ELAPSED_TIME/60)) ' min' $(($ELAPSED_TIME%60)) ' s' >> ${dirOut}Logfile.txt