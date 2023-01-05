import argparse
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import os
from operator import mul


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

def limit_pixel_values(input_fn, output_fn,low_val=-1024):
    input_im = sitk.ReadImage(input_fn)
    input_np = sitk.GetArrayFromImage(input_im)
    input_np[input_np<low_val]=low_val
    output_im = sitk.GetImageFromArray(input_np)
    output_im.CopyInformation(input_im)
    sitk.WriteImage(output_im,output_fn)

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

def segment(input_image, output_mask=None, radius=(12, 12, 12),return_sitk=False):
    image = sitk.InvertIntensity(sitk.Cast(sitk.ReadImage(input_image),sitk.sitkFloat32))
    mask = sitk.OtsuThreshold(image)
    dil_mask = sitk.BinaryDilate(mask, (10, 10, 1))
    component_image = sitk.ConnectedComponent(dil_mask)
    sorted_component_image = sitk.RelabelComponent(component_image, sortByObjectSize=True)
    largest_component_binary_image = sorted_component_image == 1
    mask_closed = sitk.BinaryMorphologicalClosing(largest_component_binary_image, (12, 12, 12))
    dilated_mask = sitk.BinaryDilate(mask_closed, (10, 10, 0))
    filled_mask = sitk.BinaryFillhole(dilated_mask)
    if return_sitk:
        return filled_mask
    else:
        sitk.WriteImage(filled_mask, output_mask)

def segment_small(input_image, output_mask=None, radius=(12, 12, 12),return_sitk=False):
    image = sitk.InvertIntensity(sitk.Cast(sitk.ReadImage(input_image),sitk.sitkFloat32))
    mask = sitk.OtsuThreshold(image)
    dil_mask = sitk.BinaryDilate(mask, (10, 10, 1))
    component_image = sitk.ConnectedComponent(dil_mask)
    sorted_component_image = sitk.RelabelComponent(component_image, sortByObjectSize=True)
    largest_component_binary_image = sorted_component_image == 1
    mask_closed = sitk.BinaryMorphologicalClosing(largest_component_binary_image, (5, 5, 5))
    dilated_mask = sitk.BinaryDilate(mask_closed, (10, 10, 0))
    filled_mask = sitk.BinaryFillhole(dilated_mask)
    if return_sitk:
        return filled_mask
    else:
        sitk.WriteImage(filled_mask, output_mask)

def create_FOV_cbct(cbct,output_mask=None,return_sitk=False):
    
    def create_circular_mask(h, w, center, radius):
        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
        mask = dist_from_center <= radius
        return mask

    im = sitk.ReadImage(cbct)
    im_np = sitk.GetArrayFromImage(im)
    dim = np.shape(im_np)

    #define center and radius of FOV
    centerX = dim[1]/2
    centerY = dim[2]/2
    radius = dim[1]/2-1

    #create a mask of this FOV for each slice
    cbct_mask=np.zeros((dim[0],dim[1],dim[2]),int)
    for i in range(dim[0]-26):
        cbct_mask[i+13,:,:]=create_circular_mask(dim[1],dim[2],(centerX,centerY),radius)
    cbct_mask=cbct_mask.astype(int)

    # limit first and last slices to smaller radii
    #for j in range(1,14):
    #    cbct_mask[j]=create_circular_mask(dim[1],dim[2],(centerX,centerY),18+(j-1)*15)
    #    cbct_mask[-j]=create_circular_mask(dim[1],dim[2],(centerX,centerY),18+(j-1)*15)

    mask_itk = sitk.GetImageFromArray(cbct_mask)
    mask_itk.CopyInformation(im)
    castFilter = sitk.CastImageFilter()
    castFilter.SetOutputPixelType(sitk.sitkInt16)
    imgFiltered = castFilter.Execute(mask_itk)
    if return_sitk:
        return imgFiltered
    sitk.WriteImage(imgFiltered,output_mask)

def fix_fov_cbct_umcg(cbct_or,ct_ref,mask_cbct,trans,output_mask):
    fov = create_FOV_cbct(cbct_or,return_sitk=True)
    ct = sitk.ReadImage(ct_ref)
    cbct_mask = sitk.ReadImage(mask_cbct)
    fov_mask = transform_mask(fov,ct,trans)

    cbct_mask_corrected = sitk.GetArrayFromImage(fov_mask)*sitk.GetArrayFromImage(cbct_mask)
    cbct_mask_corrected = sitk.GetImageFromArray(cbct_mask_corrected)
    cbct_mask_corrected.CopyInformation(cbct_mask)

    sitk.WriteImage(cbct_mask_corrected,output_mask)

def fix_fov_cbct_umcu(cbct_or,ct_ref,mask_cbct,trans,output_mask):
    fov = create_FOV_cbct_umcu(cbct_or,return_sitk=True)
    ct = sitk.ReadImage(ct_ref)
    cbct_mask = sitk.ReadImage(mask_cbct)
    fov_mask = transform_mask(fov,ct,trans)

    cbct_mask_corrected = sitk.GetArrayFromImage(fov_mask)*sitk.GetArrayFromImage(cbct_mask)
    cbct_mask_corrected = sitk.GetImageFromArray(cbct_mask_corrected)
    cbct_mask_corrected.CopyInformation(cbct_mask)

    sitk.WriteImage(cbct_mask_corrected,output_mask)

def fix_fov_mri_umcu(ct_ref,mask_cbct,output_mask):
    mask_ct = segment_small(ct_ref,return_sitk=True)
    cbct_mask = sitk.ReadImage(mask_cbct)

    cbct_mask_corrected = sitk.GetArrayFromImage(mask_ct)*sitk.GetArrayFromImage(cbct_mask)
    cbct_mask_corrected = sitk.GetImageFromArray(cbct_mask_corrected)
    cbct_mask_corrected.CopyInformation(cbct_mask)

    sitk.WriteImage(cbct_mask_corrected,output_mask)

def create_FOV_cbct_umcu(cbct,output_mask=None,return_sitk=False):
    #load image
    im = sitk.ReadImage(cbct)
    cbct_np = sitk.GetArrayFromImage(im)
    
    #select cbct fov 
    dim = np.shape(cbct_np)
    cbct_mask=np.zeros((dim[0],dim[1],dim[2]),int)
    cbct_mask[cbct_np>0]=1
    cbct_mask=cbct_mask.astype(int)

    #convert to sitk and fill holes
    mask_itk = sitk.GetImageFromArray(cbct_mask)
    mask_itk.CopyInformation(im)
    castFilter = sitk.CastImageFilter()
    castFilter.SetOutputPixelType(sitk.sitkInt16)
    imgFiltered = castFilter.Execute(mask_itk)
    filled_mask = sitk.BinaryMorphologicalClosing(imgFiltered, (20, 20, 20))

    try:
        dilated_mask = sitk.BinaryDilate(filled_mask, (-1, -1, 0))
    except:
        dilated_mask = filled_mask

    if return_sitk:
        return dilated_mask
    else:
        sitk.WriteImage(dilated_mask,output_mask)


def create_FOV_cbct_umcu_pelvis(cbct, output_mask=None, return_sitk=False):
    # load image
    im = sitk.ReadImage(cbct)
    cbct_np = sitk.GetArrayFromImage(im)

    # select cbct fov
    dim = np.shape(cbct_np)
    cbct_mask = np.zeros((dim[0], dim[1], dim[2]), int)
    cbct_mask[cbct_np > 0] = 1
    cbct_mask = cbct_mask.astype(int)

    # convert to sitk and fill holes
    mask_itk = sitk.GetImageFromArray(cbct_mask)
    mask_itk.CopyInformation(im)
    castFilter = sitk.CastImageFilter()
    castFilter.SetOutputPixelType(sitk.sitkInt16)
    imgFiltered = castFilter.Execute(mask_itk)
    filled_mask = sitk.BinaryMorphologicalClosing(imgFiltered, (20, 20, 20))

    try:
        dilated_mask = sitk.BinaryDilate(filled_mask, (15, 15, 0))
    except:
        dilated_mask = filled_mask

    if return_sitk:
        return dilated_mask
    else:
        sitk.WriteImage(dilated_mask, output_mask)

def transform_mask(input_mask,ref_img,trans_file): 
    # function to transform a mask using the previously calculated (rigid) registration parameters
    # this function uses images as inputs not filepaths, so reading the files has to be performed outside 
    tf = sitk.ReadTransform(trans_file) 
    tf = tf.GetInverse()
    default_value=0
    interpolator=sitk.sitkNearestNeighbor
    mask_reg = sitk.Resample(input_mask,ref_img,tf,interpolator,default_value)
    return mask_reg

def generate_mask_cbct(ct,cbct,trans_file,output_fn=None,return_sitk=False):
    limit_pixel_values(ct,ct)
    ct_im = sitk.ReadImage(ct)
    cbct_im = sitk.ReadImage(cbct)
    mask_ct = segment(ct,return_sitk=True)
    cbct_fov = create_FOV_cbct_umcu(cbct,return_sitk=True)
    fov_reg = transform_mask(cbct_fov,ct_im,trans_file)
    mask_ct_np = sitk.GetArrayFromImage(mask_ct)
    cbct_fov_np = sitk.GetArrayFromImage(fov_reg)
    mask_cbct_np = mask_ct_np*cbct_fov_np
    mask_cbct = sitk.GetImageFromArray(mask_cbct_np)
    component_image = sitk.ConnectedComponent(mask_cbct)
    sorted_component_image = sitk.RelabelComponent(component_image, sortByObjectSize=True)
    largest_component = sorted_component_image == 1
    largest_component.CopyInformation(mask_ct)
    if return_sitk:
        return largest_component
    else:
        sitk.WriteImage(largest_component,output_fn)

def generate_mask_cbct_pelvis(ct,cbct,trans_file,output_fn=None,return_sitk=False):
    limit_pixel_values(ct,ct)
    ct_im = sitk.ReadImage(ct)
    cbct_im = sitk.ReadImage(cbct)
    mask_ct = segment(ct,return_sitk=True)
    cbct_fov = create_FOV_cbct_umcu(cbct,return_sitk=True)
    fov_reg = transform_mask(cbct_fov,ct_im,trans_file)
    mask_ct_np = sitk.GetArrayFromImage(mask_ct)
    cbct_fov_np = sitk.GetArrayFromImage(fov_reg)
    mask_cbct_np = mask_ct_np*cbct_fov_np
    mask_cbct = sitk.GetImageFromArray(mask_cbct_np)
    component_image = sitk.ConnectedComponent(mask_cbct)
    sorted_component_image = sitk.RelabelComponent(component_image, sortByObjectSize=True)
    largest_component = sorted_component_image == 1
    largest_component.CopyInformation(mask_ct)
    if return_sitk:
        return largest_component
    else:
        sitk.WriteImage(largest_component,output_fn)

def correct_mask_mr(mr,ct,transform,mask,mask_corrected):
    # load inputs
    mr_im = sitk.ReadImage(mr)
    ct_im = sitk.ReadImage(ct)
    tf = sitk.ReadTransform(transform)
    mask_im = sitk.ReadImage(mask)
    mask_ct = segment(ct, return_sitk=True)

    # create mask of original MR FOV
    mr_im_np = sitk.GetArrayFromImage(mr_im)
    mr_im_np[mr_im_np>=-2000]=1
    fov=sitk.GetImageFromArray(mr_im_np)
    fov.CopyInformation(mr_im)

    # transform mask to registered mr
    fov_reg = transform_mask(fov,ct_im,transform)
    
    # correct MR mask with fov_reg box
    fov_np = sitk.GetArrayFromImage(fov_reg)
    mask_np = sitk.GetArrayFromImage(mask_im)
    mask_ct_np = sitk.GetArrayFromImage(mask_im)
    mask_corrected_np=mask_np*fov_np*mask_ct_np

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
    border=10
    if  np.min(idx_nz[1])<border:
        AP = [np.min(idx_nz[1]) - np.min(idx_nz[1]), np.max(idx_nz[1]) + 10]
    else:
        AP = [np.min(idx_nz[1]) - border, np.max(idx_nz[1]) + border]
    if np.min(idx_nz[2]) < border:
        LR = [np.min(idx_nz[2]) - np.min(idx_nz[2]), np.max(idx_nz[2]) + 10]
    else:
        LR = [np.min(idx_nz[2]) - border, np.max(idx_nz[2]) + border]
    cropped_image = image[LR[0]:LR[1], AP[0]:AP[1], IP[0]:IP[1]]
    sitk.WriteImage(cropped_image, output_image)

def generate_overview(input_path,ref_path,mask_path,output_path,title=''):
    #load images as np arrrays
    im=sitk.ReadImage(ref_path)
    ref_img = sitk.GetArrayFromImage(im)
    input_img = sitk.GetArrayFromImage(sitk.ReadImage(input_path))
    mask_img = sitk.GetArrayFromImage(sitk.ReadImage(mask_path))
    
    # attempt of 'normalizing' images for difference calculations
    if np.max(ref_img)>3000:
        max_ref = 3000
    else:
        max_ref = np.max(ref_img)
    
    if np.max(input_img)>2000:
        max_in = 2000
    else:
        max_in = np.max(input_img)

    input_norm = (input_img+np.abs(np.min(input_img)))/(max_in+np.abs(np.min(input_img)))
    ref_norm = (ref_img+np.abs(np.min(ref_img)))/(max_ref+np.abs(np.min(ref_img)))
    diff = input_norm - ref_norm

    # select central slices
    im_shape = np.shape(ref_img)

    #aspect ratio for plots
    spacing=list(im.GetSpacing())
    spacing.reverse() #SimpleITK to numpy conversion
    asp_ax = spacing[1]*spacing[2]
    asp_sag = spacing[0]*spacing[1]
    asp_cor = spacing[0]*spacing[2]

    #window/level for CBCT/MR (called input)
    if np.min(input_img)<-500: #CBCT
        if spacing[0]==1:   #brain
            w_i = 2500
            l_i = 250
        else:               #pelvis
            w_i = 1200
            l_i = -400
    else: #MR
        if spacing[0]==1:   #brain
            w_i = 600
            l_i = 280
        else:               #pelvis
            w_i = 600
            l_i = 280
    
    #window/level for CT (called ref)
    w_r = 2500
    l_r = 200

    # titles for subplots
    titles = [  os.path.basename(os.path.normpath(input_path)),
                os.path.basename(os.path.normpath(ref_path)),
                os.path.basename(os.path.normpath(mask_path)),
                'Difference'
                ]

    # make subplots axial, sagittal and coronal view
    fig, ax = plt.subplots(3,4,figsize=(14,10))

    fig.suptitle(title, fontsize=18,y=1.01)

    ax[0][0].imshow(input_img[int(im_shape[0]/2),:,::-1],cmap='gray',aspect=asp_ax)#,vmin=l_i-w_i/2,vmax=l_i+w_i/2)
    ax[0][1].imshow(ref_img[int(im_shape[0]/2),:,::-1],cmap='gray',aspect=asp_ax,vmin=l_r-w_r/2,vmax=l_r+w_r/2)
    ax[0][2].imshow(mask_img[int(im_shape[0]/2),:,::-1],cmap='gray',aspect=asp_ax)
    ax[0][3].imshow(diff[int(im_shape[0]/2),:,::-1],cmap='RdBu',aspect=asp_ax,vmin=-0.3,vmax=0.3)

    for j in range(4):
        ax[1][j].set_xticklabels([])
        ax[1][j].set_yticklabels([])

    ax[1][0].imshow(input_img[::-1,:,int(im_shape[2]/2)],cmap='gray',aspect=asp_sag)#,vmin=l_i-w_i/2,vmax=l_i+w_i/2)
    ax[1][1].imshow(ref_img[::-1,:,int(im_shape[2]/2)],cmap='gray',aspect=asp_sag,vmin=l_r-w_r/2,vmax=l_r+w_r/2)
    ax[1][2].imshow(mask_img[::-1,:,int(im_shape[2]/2)],cmap='gray',aspect=asp_sag)
    ax[1][3].imshow(diff[::-1,:,int(im_shape[2]/2)],cmap='RdBu',aspect=asp_sag,vmin=-0.3,vmax=0.3)

    for i in range(4):
        ax[0][i].set_xticklabels([])
        ax[0][i].set_yticklabels([])
        ax[0][i].set_title(titles[i].split('.')[0])

    ax[2][0].imshow(input_img[::-1,int(im_shape[1]/2),::-1],cmap='gray',aspect=asp_cor)#,vmin=l_i-w_i/2,vmax=l_i+w_i/2)
    ax[2][1].imshow(ref_img[::-1,int(im_shape[1]/2),::-1],cmap='gray',aspect=asp_cor,vmin=l_r-w_r/2,vmax=l_r+w_r/2)
    ax[2][2].imshow(mask_img[::-1,int(im_shape[1]/2),::-1],cmap='gray',aspect=asp_cor)
    ax[2][3].imshow(diff[::-1,int(im_shape[1]/2),::-1],cmap='RdBu',aspect=asp_cor,vmin=-0.3,vmax=0.3)

    for j in range(4):
        ax[2][j].set_xticklabels([])
        ax[2][j].set_yticklabels([])

    plt.tight_layout()
    plt.savefig(output_path,transparent=False,facecolor='white',bbox_inches='tight')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Define fixed, moving and output filenames')
    parser.add_argument('operation', help='select operation to perform (register, convert, segment, mask_mr, mask_ct,'+\
    ' resample, correct,overview, clean, fix, mask_umcg)')
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
    elif args.operation == 'mask_umcg':
        create_FOV_cbct(args.i, args.o, True)
    elif args.operation == 'mask_cbct':
        generate_mask_cbct(args.i, args.mask_in, args.p, args.o)
    elif args.operation == 'mask_cbct_pelvis':
        generate_mask_cbct_pelvis(args.i, args.mask_in, args.p, args.o)
    elif args.operation == 'fix_umcg':
        fix_fov_cbct_umcg(args.i, args.ii, args.mask_in, args.p, args.o)
    elif args.operation == 'fix_umcu':
        fix_fov_cbct_umcu(args.i, args.ii, args.mask_in, args.p, args.o)
    elif args.operation == 'fix_umcu_mri':
        fix_fov_mri_umcu(args.i, args.mask_in, args.o)
    elif args.operation == 'overview':
        generate_overview(args.i, args.ii, args.mask_in, args.o)
    elif args.operation == 'crop':
        crop(args.i, args.mask_crop, args.o)
    elif args.operation == 'clean':
        clean_border(args.i, args.o)
    else:
        print('check help for usage instructions')