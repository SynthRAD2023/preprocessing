import argparse
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import os


def convert_dicom_to_nifti(input, output):
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(input)
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    sitk.WriteImage(image, output)


def resample(input, output, spacing):
    image = sitk.ReadImage(input)
    space = image.GetSpacing()
    size = image.GetSize()
    direction = image.GetDirection()
    origin = image.GetOrigin()
    new_space = spacing
    new_size = tuple([int(round(osz * ospc / nspc)) for osz, ospc, nspc in zip(size, space, new_space)])
    image_resampled = sitk.Resample(image, new_size, sitk.Transform(), sitk.sitkLinear, origin, new_space, direction,
                                    -1000.0, sitk.sitkInt16)
    sitk.WriteImage(image_resampled, output)


def read_parameter_map(parameter_fn):
    return sitk.ReadParameterFile(parameter_fn)


def register(fixed, moving, parameter, output):
    # Load images
    fixed_image = sitk.ReadImage(fixed)
    moving_image = sitk.ReadImage(moving)

    # Perform registration based on parameter file
    elastixImageFilter = sitk.ElastixImageFilter()
    elastixImageFilter.SetParameterMap(parameter)
    elastixImageFilter.PrintParameterMap()
    elastixImageFilter.SetFixedImage(moving_image)  # due to FOV differences CT first registered to MR an inverted in the end
    elastixImageFilter.SetMovingImage(fixed_image)
    elastixImageFilter.LogToConsoleOn()
    elastixImageFilter.LogToFileOff()
    elastixImageFilter.Execute()

    # convert to itk transform format
    transform = elastixImageFilter.GetTransformParameterMap(0)
    x = transform.values()
    center = np.array((x[0])).astype(np.float64)
    rigid = np.array((x[22])).astype(np.float64)
    transform_itk = sitk.Euler3DTransform()
    transform_itk.SetParameters(rigid)
    transform_itk.SetCenter(center)
    transform_itk.SetComputeZYX(False)

    # save itk transform to correct MR mask later
    output = str(output)
    transform_itk.WriteTransform(str(output.split('.')[:-2][0]) + '_parameters.txt')
    #transform_itk.WriteTransform(str('registration_parameters.txt'))

    ##invert transform to get MR registered to CT
    inverse = transform_itk.GetInverse()

    ## check if moving image is an mr or cbct
    min_moving = np.amin(sitk.GetArrayFromImage(moving_image))
    if min_moving <-500:
        background = -1000
    else:
        background = 0

    ##transform MR image
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(fixed_image)
    resample.SetTransform(inverse)
    resample.SetInterpolator(sitk.sitkLinear)
    resample.SetDefaultPixelValue(background)
    output_image = resample.Execute(moving_image)

    # write output image
    sitk.WriteImage(output_image, output)

def clean_border(input_image, output_image):
    im = (sitk.ReadImage(input_image))
    im_np = sitk.GetArrayFromImage(im)
    im_np[im_np >= 3500] = 0
    im2 = sitk.GetImageFromArray(im_np)
    im2.CopyInformation(im)
    sitk.WriteImage(im2, output_image)

def segment(input_image, output_mask, radius=(12, 12, 12)):
    image = sitk.InvertIntensity(sitk.Cast(sitk.ReadImage(input_image),sitk.sitkFloat32))
    mask = sitk.OtsuThreshold(image)
    component_image = sitk.ConnectedComponent(mask)
    sorted_component_image = sitk.RelabelComponent(component_image, sortByObjectSize=True)
    largest_component_binary_image = sorted_component_image == 1
    mask_closed = sitk.BinaryMorphologicalClosing(largest_component_binary_image, (12, 12, 12))
    dilated_mask = sitk.BinaryDilate(mask_closed, (10, 10, 0))
#    filled_mask = sitk.BinaryFillhole(dilated_mask)
    sitk.WriteImage(dilated_mask, output_mask)

def correct_mask_mr(mr,ct,transform,mask,mask_corrected):
    # load inputs
    mr_im = sitk.ReadImage(mr)
    ct_im = sitk.ReadImage(ct)
    tf = sitk.ReadTransform(transform)
    mask_im = sitk.ReadImage(mask)
    
    # create mask of original MR FOV
    mr_im_np = sitk.GetArrayFromImage(mr_im)
    mr_im_np[mr_im_np>=-2000]=1
    fov=sitk.GetImageFromArray(mr_im_np)
    fov.CopyInformation(mr_im)

    # transform mask to registered mr
    tf = tf.GetInverse()
    default_value=0
    interpolator=sitk.sitkNearestNeighbor
    fov_reg = sitk.Resample(fov,ct_im,tf,interpolator,default_value)
    
    # correct MR mask with fov_reg box
    fov_np = sitk.GetArrayFromImage(fov_reg)
    mask_np = sitk.GetArrayFromImage(mask_im)
    mask_corrected_np=mask_np*fov_np

    #save corrected mask
    mask_corrected_im = sitk.GetImageFromArray(mask_corrected_np)
    mask_corrected_im.CopyInformation(mask_im)
    sitk.WriteImage(mask_corrected_im, mask_corrected)


def mask_ct(input_image, input_mask, output_image):
    image = sitk.ReadImage(input_image)
    mask = sitk.ReadImage(input_mask)
    masked_image = sitk.Mask(image, mask, -1000, 0)
    sitk.WriteImage(masked_image, output_image)

def mask_mr(input_image, input_mask, output_image):
    image = sitk.ReadImage(input_image)
    mask = sitk.ReadImage(input_mask)
    masked_image = sitk.Mask(image, mask, 0, 0)
    sitk.WriteImage(masked_image, output_image)

def crop(input_image, mask_for_crop, output_image):
    image = sitk.ReadImage(input_image)
    mask = sitk.ReadImage(mask_for_crop)
    mask_np = sitk.GetArrayFromImage(mask)
    idx_nz = np.nonzero(mask_np)
    IP = [np.min(idx_nz[0]) , np.max(idx_nz[0]) ]
    AP = [np.min(idx_nz[1]) - 10, np.max(idx_nz[1]) + 10]
    LR = [np.min(idx_nz[2]) - 10, np.max(idx_nz[2]) + 10]
    cropped_image = image[LR[0]:LR[1], AP[0]:AP[1], IP[0]:IP[1]]
    sitk.WriteImage(cropped_image, output_image)

def generate_overview(input_path,ref_path,mask_path,output_path,title=''):
    #load images as np arrrays
    ref_img = sitk.GetArrayFromImage(sitk.ReadImage(ref_path))
    input_img = sitk.GetArrayFromImage(sitk.ReadImage(input_path))
    mask_img = sitk.GetArrayFromImage(sitk.ReadImage(mask_path))

    diff = input_img/(np.max(input_img))-ref_img/(np.max(ref_img))

    # select central slices
    im_shape = np.shape(ref_img)

    # titles for subplots
    titles = [  os.path.basename(os.path.normpath(input_path)),
                os.path.basename(os.path.normpath(ref_path)),
                os.path.basename(os.path.normpath(mask_path)),
                'Difference'
                ]

    # make subplots axial, sagittal and coronal view
    fig, ax = plt.subplots(3,4,figsize=(14,10))

    fig.suptitle(title, fontsize=18,y=1.01)

    ax[0][0].imshow(input_img[int(im_shape[0]/2),:,::-1],cmap='gray')
    ax[0][1].imshow(ref_img[int(im_shape[0]/2),:,::-1],cmap='gray')
    ax[0][2].imshow(mask_img[int(im_shape[0]/2),:,::-1],cmap='gray')
    ax[0][3].imshow(diff[int(im_shape[0]/2),:,::-1],cmap='RdBu',vmin=-0.7,vmax=0.7)

    for j in range(4):
        ax[1][j].set_xticklabels([])
        ax[1][j].set_yticklabels([])

    ax[1][0].imshow(input_img[::-1,:,int(im_shape[2]/2)],cmap='gray')
    ax[1][1].imshow(ref_img[::-1,:,int(im_shape[2]/2)],cmap='gray')
    ax[1][2].imshow(mask_img[::-1,:,int(im_shape[2]/2)],cmap='gray')
    ax[1][3].imshow(diff[::-1,:,int(im_shape[2]/2)],cmap='RdBu',vmin=-0.7,vmax=0.7)

    for i in range(4):
        ax[0][i].set_xticklabels([])
        ax[0][i].set_yticklabels([])
        ax[0][i].set_title(titles[i].split('.')[0])

    ax[2][0].imshow(input_img[::-1,int(im_shape[1]/2),:],cmap='gray')
    ax[2][1].imshow(ref_img[::-1,int(im_shape[1]/2),:],cmap='gray')
    ax[2][2].imshow(mask_img[::-1,int(im_shape[1]/2),:],cmap='gray')
    ax[2][3].imshow(diff[::-1,int(im_shape[1]/2),:],cmap='RdBu',vmin=-0.7,vmax=0.7)

    for j in range(4):
        ax[2][j].set_xticklabels([])
        ax[2][j].set_yticklabels([])

    plt.tight_layout()
    plt.savefig(output_path,transparent=False,facecolor='white',bbox_inches='tight')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Define fixed, moving and output filenames')
    parser.add_argument('operation', help='select operation to perform (register, convert, segment, mask_mr, mask_ct,resample, correct,overview, clean)')
    parser.add_argument('--f', help='fixed file path')
    parser.add_argument('--m', help='moving file path')
    parser.add_argument('--i', help='input file path (folder containing dicom series) for registration or resampling')
    parser.add_argument('--ii', help='2nd input file path')
    parser.add_argument('--o', help='output file path')
    parser.add_argument('--p', help='parameter file path (if not specified generate default)')
    parser.add_argument('--s', help='spacing used for resampling (size of the image will be adjusted accordingly)',
                        nargs='+', type=float)
    parser.add_argument('--r', help='radius for closing operation during masking')
    parser.add_argument('--mask_in', help='input mask to mask CT, CBCT or MR image')
    #    parser.add_argument('--mask_value',help = 'intensity value used outside mask')
    parser.add_argument('--mask_crop', help='mask to calculate bounding box for crop')
    args = parser.parse_args()

    if args.operation == 'register':
        if args.p is not None:
            register(args.f, args.m, read_parameter_map(args.p), args.o)
        # do something
        else:
            # do something else
            print('Please load a valid elastix parameter file!')
            # register(args.f, args.m, create_parameter_map(), args.o)
    elif args.operation == 'convert':
        convert_dicom_to_nifti(args.i, args.o)
    elif args.operation == 'resample':
        print(tuple(args.s))
        resample(args.i, args.o, tuple(args.s))
    elif args.operation == 'segment':
        segment(args.i, args.o, args.r)
    elif args.operation == 'correct':
        correct_mask_mr(args.i, args.ii, args.f, args.mask_crop, args.o)
        # mr, ct, params, mask, output mask
    elif args.operation == 'mask_mr':
        #        print('arg mask_value= '+ args.mask_value)
        mask_mr(args.i, args.mask_in, args.o)
    elif args.operation == 'mask_ct':
        #        print('arg mask_value= '+ args.mask_value)
        mask_ct(args.i, args.mask_in, args.o)
    elif args.operation == 'overview':
        generate_overview(args.i, args.ii, args.mask_in, args.o)
    elif args.operatio