import SimpleITK as sitk
import numpy as np
import subprocess as sub
import os
import fnmatch
import shutil
from sys import platform

def struct_to_nrrd(struct_path, output_path):
    #convert dicom RTstruct into individual .nrrd files for each structure
    #requires Plastimatch (www.plastimatch.org)
    sub.run(['plastimatch','convert','--input',struct_path,'--output-prefix',output_path,'--prefix-format','nrrd'],shell=True)

def nii_to_nrrd(input_path,output_path):
    #convert pCT from .nii.gz to .nrrd and remove all meta data so it can be used with matRad
    im = sitk.ReadImage(input_path)
    for k in im.GetMetaDataKeys():
        im.EraseMetaData(k)
    sitk.WriteImage(im,output_path,True)


def resample_structure(structure_path,ref_CT,output_path,ref_CT_is_sitk=False):
    #resample a structure (.nrrd) onto same grid as the pCT, 
    #ref_CT can be path to an image (e.g. nrrd) or already loaded as a sitk image (ref_CT_is_sitk=True)
    #(this helps to speed up the resampling if a batch of structures is resampled)
    print(f'Reading structure {os.path.basename(structure_path)}')
    structure_im = sitk.ReadImage(structure_path)
    if ref_CT_is_sitk == False:
        print(f'Reading reference {os.path.basename(ref_CT)}')
        ref_CT = sitk.ReadImage(ref_CT)
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(ref_CT)
    resample.SetInterpolator(sitk.sitkNearestNeighbor)
    print(f'Resampling...')
    structure_resampled = resample.Execute(structure_im)
    print(f'Writing...')
    sitk.WriteImage(structure_resampled,output_path,True)
    print(f'Finished!')
