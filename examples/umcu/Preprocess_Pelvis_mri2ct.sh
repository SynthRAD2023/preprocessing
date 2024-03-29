#!/bin/bash

# Measure Elapsed time of the script:
START_TIME=$SECONDS

Task='1'
Center='A'
AnatomicalSite='P'
Site='pelvis'
initial='initialDataLocation'
dirOut='whereTheDAtaWillGo/Task1/'${Site}'/'

Flag_preproc=123 	# set the flag to 1234 to activate the download
Flag_rtstruc=1234
Flag_extract=123
Flag_overview=1234
Flag_remove=123   # this is for full debug

if [ $Flag_extract == '1234' ]; then
  rm ${dirOut}overview/MR_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_MR_UMCU_${Site}.xlsx
fi
## these paths contain all the fixed provided tools
## not to be modified by the user
preproc='/code/preprocessing/pre_process_tools.py'
extract='/code/preprocessing/extract_tags_tools_umc.py'
convert_rtss='/code/preprocessing/convert_structures.py'

tags_MR='/code/preprocessing/param_files/tags_MR.txt'
tags_CT='/code/preprocessing/param_files/tags_CT.txt'
param_reg='/code/preprocessing/param_files/parameters_MR.txt'

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
	patientid=`echo ${patients[patIndex]} | awk '{print $2}'`
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

  Hdf_CT=$(find ${dirCT}Hdf/ -type f \( -iname "mod=ct*bek*" -o -iname "mod=ct*pros*" -o -iname "mod=ct*pelv*" -o -iname "mod=ct*bdo*" -o -iname "mod=ct*mar*" \) | head -1)
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

  python ${preproc} fix_umcu_mri --i ${TMP}ct_crop.nii.gz --mask_in ${TMP}mask_crop.nii.gz --o ${TMP}mask_crop.nii.gz


#  python ${preproc} correct --i ${TMP}mr_crop.nii.gz --ii ${TMP}ct_crop.nii.gz \
#  --mask_crop ${TMP}mr_crop.nii.gz --o ${TMP}mask_crop2.nii.gz

#Mask CT, not used
  echo "Segmenting CT... "
#  python ${preproc} segment --i ${TMP}ct_crop.nii.gz --o ${TMP}mask_CT.nii.gz

#Crop to dilated mask_MR
  #python ${preproc} crop --i ${TMP}ct_resampled.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}ct_cropped.nii.gz
  #python ${preproc} crop --i ${TMP}mr_IP_registered.nii.gz --mask_crop ${TMP}mask_MR.nii.gz --o ${TMP}mr_cropped.nii.gz
  fi

if [ $Flag_rtstruc == '1234' ]; then
    echo -e "Preparing RTStruct"
    Dcm_RTstruct=$(find ${dirCT}Dcm/ -type f -name rts*dcm | head -1)
    echo $Dcm_RTstruct
    if [ -z "$Dcm_RTstruct" ]; then
      dicomgetcli.jar -autoanonymize -patientid $patientid -database dicom_rtstruct -dirs ${dirCT}Dcm/ -tags "Modality" -tagvalues "RTST" -tagvaluecomparators containsIgnoreCase  > /dev/null
    fi
    Dcm_RTstruct=$(find ${dirCT}Dcm/ -type f -name rts*dcm | head -1)
    echo -e "Dcm RTSTRUCT: " $Dcm_RTstruct
    mkdir -p ${TMP}rtss
    mkdir -p ${TMP}rtss/or
    alias plastimatch='/usr/bin/plastimatch'

##   python ${convert_rtss} str2nrrd --i ${Dcm_RTstruct} --o ${TMP}rtss/or
    /usr/bin/plastimatch convert --input ${Dcm_RTstruct} --output-prefix ${TMP}rtss/or --prefix-format nrrd --output-ss-list ${TMP}rtss/or/List.txt
    python ${convert_rtss} nii2nrrd --i ${TMP}ct_crop.nii.gz --o ${TMP}rtss/ct_crop.nrrd
    rm ${TMP}rtss/or/*_sq.nrrd
    cp ${TMP}rtss/or/List.txt ${TMP}rtss/StructuresList.txt
    find ${TMP}rtss/or/ -name "* *" -type f | while read file; do mv "$file" ${file// /}; done
    for file in ${TMP}rtss/or/*.nrrd;do
    #for file in ${TMP}rtss/*.nrrd;do
      file2=$(echo ${file} | awk -F'/' '{print $NF}')
      if [ $file2 != 'ct_crop.nrrd' ]; then
        python ${convert_rtss} resample --i ${TMP}rtss/or/$file2 --ref ${TMP}rtss/ct_crop.nrrd --o ${TMP}rtss/$file2
      fi
    done
  fi

<<'Comm'
  if [ $Flag_rtstruc == '1234' ]; then
    echo -e "Preparing RTStruct"
    Dcm_RTstruct=$(find ${dirCT}Dcm/ -type f -name rts*dcm | head -1)
    if [ -z "$Dcm_RTstruct" ]; then
      dicomgetcli.jar -autoanonymize -patientid $patientid -database dicom_rtstruct -dirs ${dirCT}Dcm/ -tags "Modality" -tagvalues "RTST" -tagvaluecomparators containsIgnoreCase  > /dev/null
    fi
    Dcm_RTstruct=$(find ${dirCT}Dcm/ -type f -name rts*dcm | head -1)
    echo -e "Dcm RTSTRUCT: " $Dcm_RTstruct
    mkdir -p ${TMP}rtss
    mkdir -p ${TMP}rtss/or
    alias plastimatch='/usr/bin/plastimatch'

##   python ${convert_rtss} str2nrrd --i ${Dcm_RTstruct} --o ${TMP}rtss/or
 #   /usr/bin/plastimatch convert --input ${Dcm_RTstruct} --output-prefix ${TMP}rtss/or --prefix-format nrrd --output-ss-list ${TMP}rtss/or/List.txt
    python ${convert_rtss} nii2nrrd --i ${TMP}ct_crop.nii.gz --o ${TMP}rtss/ct_crop.nrrd
    rm ${TMP}rtss/or/*_sq.nrrd
    cp ${TMP}rtss/or/List.txt ${TMP}rtss/StructuresList.txt
    find ${TMP}rtss/or/ -name "* *" -type f | while read file; do mv "$file" ${file// /}; done
    for file in ${TMP}rtss/or/*.nrrd;do
      file2=$(echo ${file} | awk -F'/' '{print $NF}')
      python ${convert_rtss} resample --i ${TMP}rtss/or/$file2 --ref ${TMP}rtss/ct_crop.nrrd --o ${TMP}rtss/$file2
    done
  fi
Comm

  if [ $Flag_remove == '1234' ]; then
  echo "Removing "
  rm ${TMP}ct_o* ${TMP}ct_r* ${TMP}mr_I*gz ${TMP}mr_cl* ${TMP}mr_o* ${TMP}mask_MR* ${TMP}mask_CT*
  fi

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
