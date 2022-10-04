import pydicom as dcm
import os
import csv
import openpyxl
import SimpleITK as sitk

# Function that reads a list of dicom tag names from a txt file and returns the tags in a list
def read_tags(txt_file):
    file = open(txt_file,'r')
    tags = file.read().splitlines()
    return tags

# Function to get the number of slices for a dicom image
def get_number_of_slices(dcm_folder):
    files = os.listdir(dcm_folder)
    slices = 0
    UID = []
    for i in range(len(files)):
        tags = dcm.dcmread(os.path.join(dcm_folder,files[i]),stop_before_pixels=True)
        UID.append(tags['SeriesInstanceUID'].value)
        if i==0:
            slices = 1
        elif i!=0:
            if UID[i]==UID[i-1]:
                slices = slices+1
    return slices

# Function that takes a DICOM folder as an input, reads dicom tags from the first slice and returns specified tags as a dict,
# and if specified also adds dimension and spacing of post-processed image
def extract_tags(dcm_folder,tag_list,pre_processed=None):
    files = os.listdir(dcm_folder)
    tags = dcm.dcmread(os.path.join(dcm_folder,files[0]),stop_before_pixels=True)
    tags_dict = {}
    for tag in tag_list:
        try:
            tags_dict[tag]=str(tags[tag].value)
        except:
            print('Tag: ' + str(tag) + ' not available!')
            tags_dict[tag]='empty'
    tags_dict['Slices']=str(get_number_of_slices(dcm_folder))
    if pre_processed!=None:
        size_pre,spacing_pre = extract_tags_post(pre_processed)
        tags_dict['Dim_pre']=str(size_pre)
        tags_dict['Spacing_pre']=str(spacing_pre)
    return tags_dict

def extract_tags_post(image):
    im = sitk.ReadImage(image)
    imsize = im.GetSize()
    imspacing = im.GetSpacing()
    return [imsize,imspacing]

# Function that creates a csv file based on the dicts with extracted tags
def write_dict_to_csv(input_dict,output_csv,tag_list):
    
    # first check if dict is nested (required for file writing)
    try:
        input_dict[0]
        input_dict_nested = input_dict
    except:
        input_dict_nested = {}
        input_dict_nested['1']=input_dict
    
    tag_list.append('Slices')
    if 'Dim_pre' in input_dict:
        tag_list.append('Dim_pre')
        tag_list.append('Spacing_pre')
    
    with open(output_csv,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile,fieldnames=tag_list)
        writer.writeheader()
        for k in input_dict_nested:
            writer.writerow({field: input_dict_nested[k].get(field) or k for field in tag_list})
        print('csv '+ output_csv +' written!')

#Function that converts the csv file into an excel file
def convert_csv_to_xlsx(input_csv, output_xlsx):
    csv_data = []
    with open(input_csv) as file_obj:
        reader = csv.reader(file_obj)
        for row in reader:
            csv_data.append(row)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in csv_data:
        sheet.append(row)
    workbook.save(output_xlsx)
