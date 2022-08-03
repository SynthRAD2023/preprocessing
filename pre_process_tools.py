import argparse
import SimpleITK as sitk
import numpy as np

def convert_dicom_to_nifti(input,output):
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(input)
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    sitk.WriteImage(image,output)

def resample(input,output,spacing):
    image = sitk.ReadImage(input)
    space = image.GetSpacing()
    size = image.GetSize()
    direction = image.GetDirection()
    origin = image.GetOrigin()
    new_space = spacing
    new_size = tuple([int(round(osz*ospc/nspc)) for osz,ospc,nspc in zip(size, space, new_space)])
    image_resampled = sitk.Resample(image, new_size, sitk.Transform() , sitk.sitkLinear, origin,  new_space, direction, -1000.0, sitk.sitkInt16)
    sitk.WriteImage(image_resampled,output)

def read_parameter_map(parameter_fn):
    return sitk.ReadParameterFile(parameter_fn)

def register(fixed,moving,parameter,output):
    #Load images
    fixed_image = sitk.ReadImage(fixed)
    moving_image = sitk.ReadImage(moving)

    #Perform registration based on parameter file
    elastixImageFilter = sitk.ElastixImageFilter()
    elastixImageFilter.SetParameterMap(parameter)
    elastixImageFilter.PrintParameterMap()
    elastixImageFilter.SetFixedImage(moving_image) #due to FOV differences CT first registered to MR an inverted in the end
    elastixImageFilter.SetMovingImage(fixed_image)
    elastixImageFilter.LogToConsoleOn()
    elastixImageFilter.LogToFileOff()
    elastixImageFilter.Execute()
    
    #convert to itk transform format
    transform = elastixImageFilter.GetTransformParameterMap(0)
    x = transform.values()
    center = np.array((x[0])).astype(np.float64)
    rigid = np.array((x[22])).astype(np.float64)
    transform_itk = sitk.Euler3DTransform()
    transform_itk.SetParameters(rigid)
    transform_itk.SetCenter(center)
    transform_itk.SetComputeZYX(False)

    ##invert transform to get MR registered to CT
    inverse = transform_itk.GetInverse()

    ##transform MR image
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(fixed_image)
    resample.SetTransform(inverse)
    resample.SetInterpolator(sitk.sitkLinear)
    output_image = resample.Execute(moving_image)
    
    #write output image
    sitk.WriteImage(output_image ,output)

def segment(input_image, output_mask, radius=(12,12,12)):
    image = sitk.ReadImage(input_image)
    mask = sitk.OtsuThreshold(sitk.InvertIntensity(image))
    component_image = sitk.ConnectedComponent(mask)
    sorted_component_image = sitk.RelabelComponent(component_image, sortByObjectSize=True)
    largest_component_binary_image = sorted_component_image == 1
    mask_closed = sitk.BinaryMorphologicalClosing(largest_component_binary_image,(12,12,12))
    mask_closed1 = sitk.BinaryMorphologicalClosing(mask_closed,(7,7,7))
    #sitk.WriteImage(mask_closed1,output_mask)
    dilated_mask = sitk.BinaryDilate(mask_closed,(10,10,0))
    sitk.WriteImage(dilated_mask,output_mask)

def mask(input_image,input_mask,mask_value,output_image):
    image = sitk.ReadImage(input_image)
    mask = sitk.ReadImage(input_mask)
    masked_image = sitk.Mask(image,mask,mask_value,0)
    sitk.WriteImage(masked_image,output_image)

def crop(input_image,mask_for_crop,output_image):
    image = sitk.ReadImage(input_image)
    mask = sitk.ReadImage(mask_for_crop)
    mask_np = sitk.GetArrayFromImage(mask)
    idx_nz = np.nonzero(mask_np)
    IP = [np.min(idx_nz[0])-5,np.max(idx_nz[0])+5]
    AP = [np.min(idx_nz[1])-5,np.max(idx_nz[1])+5]
    LR = [np.min(idx_nz[2])-5,np.max(idx_nz[2])+5]
    cropped_image = image[LR[0]:LR[1],AP[0]:AP[1],IP[0]:IP[1]]
    sitk.WriteImage(cropped_image,output_image)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Define fixed, moving and output filenames')
    parser.add_argument('operation', help='select operation to perform (register, convert, segment, mask, resample)')
    parser.add_argument('--f', help='fixed file path')
    parser.add_argument('--m', help='moving file path')
    parser.add_argument('--i', help='input file path (folder containing dicom series) for registration or resampling')
    parser.add_argument('--o',help='output file path')
    parser.add_argument('--p',help='parameter file path (if not specified generate default)')
    parser.add_argument('--s',help='spacing used for resampling (size of the image will be adjusted accordingly)',nargs='+',type=int)
    parser.add_argument('--r',help='radius for closing operation during masking')
    parser.add_argument('--mask_in',help='input mask to mask CT, CBCT or MR image')
    parser.add_argument('--mask_value',help = 'intensity value used outside mask')
    parser.add_argument('--mask_crop',help='mask to calculate bounding box for crop')
    args = parser.parse_args()

    if args.operation == 'register':
        if args.p is not None:
            register(args.f, args.m, read_parameter_map(args.p), args.o)
        # do something
        else:
        # do something else
            print('Please load a valid elastix parameter file!')
            #register(args.f, args.m, create_parameter_map(), args.o)
    elif args.operation == 'convert':
        convert_dicom_to_nifti(args.i,args.o)
    elif args.operation == 'resample':
        print(tuple(args.s))
        resample(args.i,args.o,tuple(args.s))
    elif args.operation == 'segment':
        segment(args.i,args.o,args.r)
    elif args.operation == 'mask':
        mask(args.i,args.mask_in,args.mask_value,args.o)
    elif args.operation == 'crop':
        crop(args.i,args.mask_crop,args.o)
    else:
        print('check help for usage instructions')


