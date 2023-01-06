#!/bin/bash

# Measure Elapsed time of the script:
START_TIME=$SECONDS

Task='2'
Center='A'
AnatomicalSite='P'
Site='pelvis'
initial='/nfs/arch11/researchData/PROJECT/CBCTreplan/SynthRAD/2023/Pelvis/'
dirOut='/nfs/arch11/researchData/PROJECT/SynthRAD/2023/dataset_UMCU/Task'${Task}'/'${Site}'/'

Flag_preproc=123 	# set the flag to 1234 to activate the download
Flag_overview=1234
Flag_extract=1234
Flag_remove=123   # this is for full debug

if [ $Flag_extract == '1234' ]; then
  rm ${dirOut}overview/CBCT_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_CBCT_UMCU_${Site}.xlsx
fi
## these paths contain all the fixed provided tools
## not to be modified by the user
preproc='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/pre_process_tools.py'
extract='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/extract_tags_tools_umc.py'

tags_CBCT='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/param_files/tags_CBCT.txt'
tags_CT='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/param_files/tags_CT.txt'
param_reg='/home/mmaspero/Projects/GrandChallenge_sCT/SynthRAD2023/code/preprocessing/param_files/parameters_CBCT_'${Site}'.txt'

Now=`date`
script_name=$(basename $0)
echo -e $script_name $Now
echo -e $script_name $Now  >> ${dirOut}Logfile.txt
printf 'pts \t date_ct \t date_cbct \t phase \n' >> ${dirOut}Logfile.txt

declare -a patients
readarray patients < ./pat_list_${Site}_cbct2ct.txt
readarray -t patients < ./pat_list_${Site}_cbct2ct.txt

for patIndex in $(eval echo {0..$((${#patients[@]}-1))})
do
	patient=`echo ${patients[patIndex]} | awk '{print $1}'`
#  patientid=`echo ${patients[patIndex]} | awk '{print $2}'`
  dateCT=`echo ${patients[patIndex]} | awk '{print $4}'`
  dateCBCT=`echo ${patients[patIndex]} | awk '{print $3}'`
  phase=`echo ${patients[patIndex]} | awk '{print $5}'`

  patientnr=${patient:1:3}
  dirCT=${initial}${patient}/CBCTreg/CBCT${dateCBCT}_CT${dateCT}/
  dirCBCT=${initial}${patient}/CBCTreg/CBCT${dateCBCT}_CT${dateCT}/

  pts=${Task}${AnatomicalSite}${Center}${patientnr}
  echo -e $patient $patientnr $dateCT $dateCBCT $phase $pts
  printf '%s \t %s \t %s \t %s \n' $pts $dateCT $dateCBCT $phase   >> ${dirOut}Logfile.txt

  TMP=${dirOut}${phase}/${pts}/
  mkdir -p $TMP

  Dcm_CT=$(find ${initial}${patient}/CT/ -maxdepth 2 -type d -name "*Dcm*" -print | head -1)
  Dcm_CBCT=$(find ${initial}${patient}/CBCT/ -maxdepth 2 -type d -name "*Dcm*" -print | head -1)

  find ${initial}${patient}/CT/ -maxdepth 2 -type d -name "*Dcm*"

  Gipl_CT=$(find ${dirCT} -type f -name CT.gipl | head -1)
  Hdf_CT=${dirCT}CT.hdf
  echo -e "Gipl CT: " $Gipl_CT

  Gipl_CBCT=$(find ${dirCBCT} -type f -name CBCT.gipl | head -1)
  Hdf_CBCT=${dirCT}CBCT.hdf

  echo -e "Gipl CBCT: " $Gipl_CBCT

  echo -e "Dcm CBCT: " $Dcm_CBCT
  echo -e "Dcm CT: " $Dcm_CT

  if [ $Flag_preproc == '1234' ]; then
<<'Ciao'
Ciao

  gipl2hdf.jar --infile $Gipl_CT --outfile $Hdf_CT
  cp $Gipl_CT ${TMP}ct_or.gipl
  ConvertSitk --infile $Gipl_CT --outfile ${TMP}ct_or.nii.gz
  gipl2hdf.jar --infile $Gipl_CBCT --outfile $Hdf_CBCT
  cp $Gipl_CBCT ${TMP}cbct_or.gipl
  ConvertSitk --infile $Gipl_CBCT --outfile ${TMP}cbct_or.nii.gz

# From here Adrian steps
# Resample CT to 1x1x1
  python ${preproc} resample --i ${TMP}ct_or.nii.gz --o ${TMP}ct_resampled.nii.gz --s 1 1 2.5
#Register CBCTI to CT according to the parameter file specified
  python ${preproc} register --f ${TMP}ct_resampled.nii.gz --m ${TMP}cbct_or.nii.gz --o ${TMP}cbct_registered.nii.gz --p ${param_reg}

#Mask CBCT
  echo -e "Masking CBCT"
  python ${preproc} mask_cbct --i ${TMP}ct_resampled.nii.gz --mask_in ${TMP}cbct_or.nii.gz --p ${TMP}cbct_registered_parameters.txt --o ${TMP}mask_CBCT.nii.gz
#        generate_mask_cbct_pelvis(args.i, args.mask_in, args.p, args.o)
#        def generate_mask_cbct_pelvis(ct, cbct, trans_file, output_fn=None, return_sitk=False):
#  python ${preproc} segment --i ${TMP}cbct_registered.nii.gz --o ${TMP}mask_CBCT.nii.gz --r 12

  echo -e "Correcting FOV"
  python ${preproc} correct --i ${TMP}cbct_or.nii.gz --ii ${TMP}ct_resampled.nii.gz \
  --f ${TMP}cbct_registered_parameters.txt --mask_crop ${TMP}mask_CBCT.nii.gz --o ${TMP}mask_CBCT_corrected.nii.gz

#Mask CBCTI and resampled to cropped CT and CBCTI to mask_CBCT
  python ${preproc} crop --i ${TMP}ct_resampled.nii.gz --mask_crop ${TMP}mask_CBCT_corrected.nii.gz --o ${TMP}ct_crop.nii.gz #--mask_value -1000

  python ${preproc} crop --i ${TMP}cbct_registered.nii.gz --mask_crop ${TMP}mask_CBCT_corrected.nii.gz --o ${TMP}cbct_crop.nii.gz #--mask_value 0
  python ${preproc} crop --i ${TMP}mask_CBCT.nii.gz --mask_crop ${TMP}mask_CBCT_corrected.nii.gz --o ${TMP}mask_crop.nii.gz #--mask_value 0

#Mask CT, not used
  python ${preproc} segment --i ${TMP}ct_crop.nii.gz --o ${TMP}mask_CT.nii.gz

#Crop to dilated mask_CBCT
  #python ${preproc} crop --i ${TMP}ct_resampled.nii.gz --mask_crop ${TMP}mask_CBCT.nii.gz --o ${TMP}ct_cropped.nii.gz
  #python ${preproc} crop --i ${TMP}cbct_registered.nii.gz --mask_crop ${TMP}mask_CBCT.nii.gz --o ${TMP}cbct_cropped.nii.gz
<<'Ciao'
Ciao
  fi

  if [ $Flag_overview == '1234' ]; then
#Generate overview
  python ${preproc} overview --i ${TMP}cbct_crop.nii.gz --ii ${TMP}ct_crop.nii.gz --mask_in  ${TMP}mask_crop.nii.gz \
   --o ${dirOut}overview/${pts}_cbct_ct_mask_${phase}.png
  fi

  if [ $Flag_remove == '1234' ]; then
    echo "Removing "
      rm ${TMP}ct_o* ${TMP}ct_r* ${TMP}cbct_r* ${TMP}cbct_o* ${TMP}mask_C*
  fi

  if [ $Flag_extract == '1234' ]; then
# Extract from dicom to csv/excel
#Extracting dicomtags to csv
  echo -e $Dcm_CBCT

   python ${extract} extract --path ${Dcm_CBCT} --tags ${tags_CBCT} --pre ${TMP}cbct_crop.nii.gz \
   --csv ${dirOut}overview/CBCT_UMCU_${Site}.csv --pt $pts --phase $phase

   python ${extract} extract --path ${Dcm_CT} --tags ${tags_CT} --pre ${TMP}ct_crop.nii.gz \
   --csv ${dirOut}overview/CT_UMCU_${Site}.csv --pt $pts --phase $phase
  fi
done

if [ $Flag_extract == '1234' ]; then

  python ${extract} toxlsx --csv ${dirOut}overview/CBCT_UMCU_${Site}.csv \
  --xlsx ${dirOut}overview/CT_CBCT_UMCU_${Site}.xlsx --tags "CBCT"

  python ${extract} toxlsx --csv ${dirOut}overview/CT_UMCU_${Site}.csv \
  --xlsx ${dirOut}overview/CT_CBCT_UMCU_${Site}.xlsx --tags "CT"

fi
#today=`date +%Y%m%d`
#mkdir -p ${dirOut}overview/${today}
#cp ${dirOut}overview/*.csv ${dirOut}overview/${today}/
#cp ${dirOut}overview/CT_CBCT_UMCU_${Site}.xlsx ${dirOut}overview/${today}/

ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo 'Time elapsed to prepare the data: ' $(($ELAPSED_TIME/60)) ' min' $(($ELAPSED_TIME%60)) ' s'
echo 'Time elapsed to prepare the data: ' $(($ELAPSED_TIME/60)) ' min' $(($ELAPSED_TIME%60)) ' s' >> ${dirOut}Logfile.txt
