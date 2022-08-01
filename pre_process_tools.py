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
    image_resampled = sitk.Resample(image, new_size, sitk.Transform() , sitk.sitkLinear, origin,  new_space, direction, 0.0, sitk.sitkInt16)
    sitk.WriteImage(image_resampled,output)

def create_parameter_map():
    p = sitk.ParameterMap()
    p['FixedInternalImagePixelType'] = ['float']
    p['MovingInternalImagePixelType'] = ['float']
    p['FixedImageDimension'] = ['3']
    p['MovingImageDimension'] = ['3']
    p['UseDirectionCosines'] = ['true']
    p['Registration'] = ['MultiResolutionRegistration']
    p['Interpolator'] = ['LinearInterpolator']
    p['Resampler'] = ['DefaultResampler']
    p['ResampleInterpolator'] = ['FinalBSplineInterpolator']
    p['FixedImagePyramid'] = ['FixedRecursiveImagePyramid']
    p['MovingImagePyramid'] = ['MovingRecursiveImagePyramid']
    p['Transform'] = ['EulerTransform']
    p['Sampler'] = ['RandomCoordinate']
    p['Optimizer'] = ['AdaptiveStochasticGradientDescent']
    p['Metric'] = ['AdvancedMattesMutualInformation']
    p['AutomaticScalesEstimation'] = ['true']
    p['AutomaticTransformInitialization'] = ["true"]
    p['AutomaticTransformInitializationMethod']=['GeometricalCenter']
    p['HowToCombineTransforms'] = ['Compose']
    p['NumberOfHistogramBins'] = ['16' ,'32', '32', '64']
    p['NumberOfResolutions'] = ['4']
    p['ImagePyramidSchedule'] = ['8','8','8','4','4','4','2','2','2','1','1','1']
    p['MaximumNumberOfIterations'] = ['1000', '1000', '1500', '1500']
    p['NumberOfSpatialSamples'] = ['2048']
    p['NewSamplesEveryIteration'] = ['true']
    p['ImageSampler'] = ['RandomCoordinate']
    p['FixedImageBSplineInterpolationOrder'] = ['1']
    p['UseRandomSampleRegion'] = ['true']
    p['BSplineInterpolationOrder'] = ['1']
    p['FinalBSplineInterpolationOrder'] = ['3']
    p['DefaultPixelValue'] = ['0']
    p['WriteResultImage '] = ['true']
    p['WriteTransformParametersEachIteration'] = ['false']
    p['WriteTransformParametersEachResolution'] = ['true']
    p['ResultImageFormat'] = ['nrrd']
    return(p)

def register(fixed,moving,parameter,output):
    #Load images
    fixed_image = sitk.ReadImage(fixed,sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving,sitk.sitkFloat32)
    #Initialize registration
    initial_transform = sitk.CenteredTransformInitializer(fixed_image, 
                                                        moving_image, 
                                                        sitk.Euler3DTransform(), 
                                                        sitk.CenteredTransformInitializerFilter.GEOMETRY)

    moving_initialized = sitk.Resample(moving_image,fixed_image,initial_transform)

    #Perform registration
    elastixImageFilter = sitk.ElastixImageFilter()
    elastixImageFilter.SetParameterMap(parameter)
    elastixImageFilter.PrintParameterMap()
    elastixImageFilter.SetFixedImage(fixed_image)
    elastixImageFilter.SetMovingImage(moving_initialized)
    elastixImageFilter.LogToConsoleOn()
    elastixImageFilter.Execute()
    output_image = elastixImageFilter.GetResultImage()
    output_image = sitk.Cast(output_image,sitk.sitkInt16)
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
    parser.add_argument('operation', help='select operation to perform (register, convert,mask or resample)')
    parser.add_argument('--f', help='fixed file path')
    parser.add_argument('--m', help='moving file path')
    parser.add_argument('--i', help='input file path (folder containing dicom series) for registration or resampling')
    parser.add_argument('--o',help='output file path')
    parser.add_argument('--s',help='spacing used for resampling (size of the image will be adjusted accordingly)',nargs='+',type=int)
    parser.add_argument('--r',help='radius for closing operation during masking')
    parser.add_argument('--mask',help='input mask to mask CT, CBCT or MR image')
    parser.add_argument('--mask_value',help = 'intensity value used outside mask')
    parser.add_argument('--mask_crop',help='mask to calculate bounding box for crop')
    args = parser.parse_args()

    if args.operation == 'register':
        register(args.f,args.m,create_parameter_map(),args.o)
    elif args.operation == 'convert':
        convert_dicom_to_nifti(args.i,args.o)
    elif args.operation == 'resample':
        print(tuple(args.s))
        resample(args.i,args.o,tuple(args.s))
    elif args.operation == 'segment':
        segment(args.i,args.o,args.r)
    elif args.operation == 'mask':
        mask(args.i,args.mask,args.mask_value,args.o)
    elif args.operation == 'crop':
        crop(args.i,args.mask_crop,args.o)
    else:
        print('check help for usage instructions')


