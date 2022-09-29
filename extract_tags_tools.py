import pydicom as dcm
import os
import csv
import openpyxl

# Function that reads a list of dicom tag names from a txt file and returns the tags in a list
def read_tags(txt_file):
    file = open(txt_file,'r')
    tags = file.read().splitlines()
    return tags

# Function that takes a DICOM folder as an input, reads the first slice and returns specified tags as a dict
def extract_tags(dcm_folder,tag_list):
    files = os.listdir(dcm_folder)
    tags = dcm.dcmread(os.path.join(dcm_folder,files[0]),stop_before_pixels=True)
    tags_dict = {}
    for tag in tag_list:
        try:
            tags_dict[tag]=str(tags[tag].value)
        except:
            print('Tag: ' + str(tag) + ' not available!')
            tags_dict[tag]='empty'
    return tags_dict

# Function that creates a csv file based on the dicts with extracted tags
def write_dict_to_csv(input_dict,output_csv,tag_list):
    with open(output_csv,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile,fieldnames=tag_list)
        writer.writeheader()
        for k in input_dict:
            writer.writerow({field: input_dict[k].get(field) or k for field in tag_list})
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
