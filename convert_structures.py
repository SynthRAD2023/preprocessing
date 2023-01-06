import SimpleITK as sitk
import subprocess as sub
import os
import csv

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

def crop_structure(struct_fn,mask_fn,output_fn):
    #crop structure so it alligns withs the cropped images generated during pre-processing
    #using the cropped mask (mask_fn) as reference for cropping
    struct = sitk.ReadImage(struct_fn)
    mask = sitk.ReadImage(mask_fn)

    crop_struct = sitk.ResampleImageFilter()
    crop_struct.SetReferenceImage(mask)
    crop_struct.SetInterpolator(sitk.sitkNearestNeighbor)

    struct_cropped = crop_struct.Execute(struct)
    write_struct = sitk.ImageFileWriter()
    write_struct.UseCompressionOn()
    write_struct.SetFileName(output_fn)
    write_struct.Execute(struct_cropped)

def list_structures(path_structures):
    #return a sorted list of all strucutes in a directory, also removing the file ending.nrrd
    structures = os.listdir(path_structures)
    structures = [structure[:-5] for structure in structures]
    structures.sort()
    return structures

def create_header(dataset_dict):
    header = []
    structures = []
    for patient in dataset_dict:
        structures.extend(dataset_dict[patient])
    [header.append(x) for x in structures if header.count(x)==0]
    return header

def check_availability(header,dataset_dict):
    results_dict = {}
    for patient in dataset_dict:
        print(patient)
        patient_dict = {i:0 for i in header}
        for i in header:
            if dataset_dict[patient].count(i) == 1:
                patient_dict[i]=1
        results_dict[patient]=patient_dict
    return results_dict

def mergedict(a,b):
    a.update(b)
    return a

def write_dict_to_csv(result_dict,header,output_file):
    header.insert(0,'patient')
    with open(output_file, "w",newline='') as f:
        w = csv.DictWriter(f, header)
        w.writeheader()
        for k,d in sorted(result_dict.items()):
            w.writerow(mergedict({'patient': k},d))

def count_occurence(header,results):
    counts = {}
    patients = list(results.keys())
    for struct in header:
        count = 0
        for patient in patients:
            if results[patient][struct]==1:
                count = count + 1
        counts[struct]=count
    return counts

def delete_keys(results,header,counts,threshold):
    patients = list(results.keys())
    structs = list(results[patients[0]].keys())
    for struct in structs:
        if counts[struct]<threshold:
            for patient in patients:
                del results[patient][struct]
            header.remove(struct)
    return header, results