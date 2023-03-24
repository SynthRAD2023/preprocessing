#!/bin/bash

# Measure Elapsed time of the script:
START_TIME=$SECONDS

Task='2'
Center='A'
AnatomicalSite='P'
Site='pelvis'
initial='InitialData'
dirOut='whereTheDataWillGo/Task'${Task}'/'${Site}'/'

Flag_preproc=123 	# set the flag to 1234 to activate the download
Flag_rtstruc=1234
Flag_overview=1234
Flag_extract=123
Flag_remove=123   # this is for full debug

if [ $Flag_extract == '1234' ]; then
  rm ${dirOut}overview/CBCT_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_UMCU_${Site}.csv
  rm ${dirOut}overview/CT_CBCT_UMCU_${Site}.xlsx
fi
## these paths contain all the fixed provided tools
## not to be modified by the user
preproc='/code/preprocessing/pre_process_tools.py'
extract='/code/preprocessing/extract_tags_tools_umc.py'
convert_rtss='/code/preprocessing/convert_structures.py'

tags_CBCT='/code/preprocessing/param_files/tags_CBCT.txt'
tags_CT='/code/preprocessing/param_files/tags_CT.txt'
param_reg='/code/preprocessing/param_files/parameters_CBCT_'${Site}'.txt'

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
  patientid=`echo ${patients[patIndex]} | awk '{print $2}'`
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
  Dcm_RTset=$(find ${initial}${patient}/RTset/ -maxdepth 2 -type d -name "*Dcm*" -print | head -1)

  find ${initial}${patient}/CT/ -maxdepth 2 -type d -name "*Dcm*"

  Gipl_CT=$(find ${dirCT} -type f -name CT.gipl | head -1)
  Hdf_CT=${dirCT}CT.hdf
  echo -e "Gipl CT: " $Gipl_CT

  Gipl_CBCT=$(find ${dirCBCT} -type f -name CBCT.gipl | head -1)
  Hdf_CBCT=${dirCT}CBCT.hdf

  echo -e "Gipl CBCT: " $Gipl_CBCT

  echo -e "Dcm CBCT: " $Dcm_CBCT
  echo -e "Dcm CT: " $Dcm_CT
  echo -e "Dcm RTset: " $Dcm_RTset

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
#  python ${preproc} mask_cbct --i ${TMP}ct_resampled.nii.gz --mask_in ${TMP}cbct_or.nii.gz --p ${TMP}cbct_registered_parameters.txt --o ${TMP}mask_CBCT.nii.gz
  python ${preproc} segment --i ${TMP}cbct_registered.nii.gz --o ${TMP}mask_CBCT.nii.gz --r 12
  python ${preproc} mask_cbct --i ${TMP}ct_resampled.nii.gz --mask_in ${TMP}cbct_or.nii.gz --p ${TMP}cbct_registered_parameters.txt --o ${TMP}mask_CBCT.nii.gz
  python ${preproc} correct --i ${TMP}cbct_or.nii.gz --ii ${TMP}ct_resampled.nii.gz \
  --f ${TMP}cbct_registered_parameters.txt --mask_crop ${TMP}mask_CBCT.nii.gz --o ${TMP}mask_CBCT_corrected.nii.gz
#def fix_fov_cbct_umcg(cbct_or,ct_ref,mask_cbct,trans,output_mask):
#fix_fov_cbct_umcg(args.i, args.ii, args.mask_in, args.p, args.o)

#        generate_mask_cbct_pelvis(args.i, args.mask_in, args.p, args.o)
#        def generate_mask_cbct_pelvis(ct, cbct, trans_file, output_fn=None, return_sitk=False):
#  python ${preproc} segment --i ${TMP}cbct_registered.nii.gz --o ${TMP}mask_CBCT.nii.gz --r 12

#  echo -e "Correcting FOV"
#  python ${preproc} fix_umcu --i ${TMP}cbct_or.nii.gz --ii ${TMP}ct_resampled.nii.gz \
#  --mask_in ${TMP}mask_CBCT.nii.gz --p ${TMP}cbct_registered_parameters.txt --o ${TMP}mask_CBCT_corrected.nii.gz
#  python ${preproc} correct --i ${TMP}cbct_or.nii.gz --ii ${TMP}ct_resampled.nii.gz \
#  --f ${TMP}cbct_registered_parameters.txt --mask_crop ${TMP}mask_CBCT.nii.gz --o ${TMP}mask_CBCT_corrected.nii.gz

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

 if [ $Flag_rtstruc == '1234' ]; then
    echo -e "Preparing RTStruct"
    Dcm_RTstruct=$(find ${Dcm_RTset} -type f -name rts*dcm | head -1)
    echo $Dcm_RTstruct
    if [ -z "$Dcm_RTstruct" ]; then
      dicomgetcli.jar -autoanonymize -patientid $patientid -database dicom_rtstruct -dirs ${dirCT}Dcm/ -tags "Modality" -tagvalues "RTST" -tagvaluecomparators containsIgnoreCase  > /dev/null
    fi
    Dcm_RTstruct=$(find ${Dcm_RTset} -type f -name rts*dcm | head -1)
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

  if [ $Flag_overview == '1234' ]; then
#Generate overview
  python ${preproc} overview --i ${TMP}cbct_crop.nii.gz --ii ${TMP}ct_crop.nii.gz --mask_in  ${TMP}mask_crop.nii.gz \
   --o ${dirOut}overview/${pts}_cbct_ct_mask_${phase}.png
  fi

  if [ $Flag_remove == '1234' ]; then
    echo "Removing "
      rm ${TMP}ct_or.gipl ${TMP}ct_r* ${TMP}cbct_r*gz ${TMP}cbct_or.gipl ${TMP}mask_C*
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
