import numpy as np
import SimpleITK as sitk
from scipy.signal import find_peaks

def detect_face(external_struct,eye_struct,output_path):
    # function that tries to estimate the face region an generates a simplified mask of it
    # this mask also contains all the air in front of the face
    
    # read inputs
    ext_sitk = sitk.ReadImage(external_struct)
    eye_sitk = sitk.ReadImage(eye_struct)
    ext = sitk.GetArrayFromImage(ext_sitk)
    eye = sitk.GetArrayFromImage(eye_sitk)

    print('Create eye bounding box...')
    # create bounding box for eye
    rows = np.any(eye, axis=1)
    cols = np.any(eye, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    
    # find center of boudning box
    y_eye = rmax - np.round((rmax-rmin)/2)
    x_eye = cmax - np.round((cmax-cmin)/2)

    print('Detect neck surface')
    # detect neck
    dim_ext = np.shape(ext)
    slice_external = ext[:,:,int(dim_ext[2]/2)]
    surface = []
    for x1 in range(dim_ext[0]):
        f = np.where(slice_external[x1,:]==1)[0]
        if f.size == 0:
            surface.append(np.nan)
        else:
            surface.append(np.min(f))
    y_neck = np.min(find_peaks(surface, distance = 20)[0])
    x_neck = surface[y_neck]

    # line between eye and neck (definig border between face and rest of the head)
    k = (y_eye - y_neck)/(x_eye - x_neck)
    d = y_neck - k * x_neck

    print('Create mask...')
    # create mask for face
    face = np.zeros_like(ext)
    for l in range(dim_ext[2]):
        for i in range(dim_ext[1]):
            for j in range(dim_ext[0]):
                if j < k*i + d:
                    face[j,i,l] = 1
    face[0:y_neck,:,:] = 0
    face[int(y_eye)+10:,:,:]=0

    print('Save mask...')
    face_mask = sitk.GetImageFromArray(face)
    face_mask.CopyInformation(ext_sitk)
    sitk.WriteImage(face_mask,output_path,True)

def anonymize_mask(face_mask,mask,output):
    # function that applies the face mask to the masks generated during pre-processing
    # can also be applied to cropped images/masks since it performs resampling

    # read inputs
    face = sitk.ReadImage(face_mask)
    mask = sitk.ReadImage(mask)

    # resample face to mask
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(mask)
    resample.SetInterpolator(sitk.sitkNearestNeighbor)
    resample.SetDefaultPixelValue(0)
    face_resampled = resample.Execute(face)

    # remove face from mask
    mask_np = sitk.GetArrayFromImage(mask)
    face_np = sitk.GetArrayFromImage(face_resampled)
    mask_np[face_np==1]=0
    mask_anon = sitk.GetImageFromArray(mask_np)
    mask_anon.CopyInformation(face_resampled)
    sitk.WriteImage(mask_anon,output,True)