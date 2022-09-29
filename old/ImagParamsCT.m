function [Dim,Vox,FOV,kVP,Expo,Curr,Time,Other]=ImagParamsCT( pat,ext )
%ImagParams print on screen some image parameters for CT
% The input is the path to the folder containing the dicom files
% Developed by m.maspero@umcutrecht.nl, 2105
% In case of comments/improvements just let me know
if nargin<2
    ext='/ct*.dcm*';
else
end

dicomsCT=dir(fullfile(pat,ext));
if isempty(dicomsCT)
    Dim=[0 0 0];
    Vox=[0 0 0];
    FOV=Vox;
    kVP=0;
    Expo=0;
    Curr=0;
    Time=0;
    Other=struct;
    warning(['No file with extension ',ext])
    return
end
dcmCT=dicominfo([pat,'/',dicomsCT(5).name]);
dcmCT2=dicominfo([pat,'/',dicomsCT(6).name]);

if ~strcmp(dcmCT.Modality,'CT')
    error('The selected dicoms are not CT images')
end

if ~isfield(dcmCT,'ExposureTime')
    dcmCT.ExposureTime=0;
end

if ~isfield(dcmCT,'Exposure')
    dcmCT.Exposure=0;
end

if ~isfield(dcmCT,'ScanOptions')
    dcmCT.ScanOptions='none';
end

if ~isfield(dcmCT,'XrayTubeCurrent')
    dcmCT.XrayTubeCurrent=0;
end

if ~isfield(dcmCT,'CTDIvol')
    dcmCT.CTDIvol=0;
end

if ~isfield(dcmCT,'KVP')
    dcmCT.KVP=0;
end

%AcqMat=dcmCT.AcquisitionMatrix(dcmCT.AcquisitionMatrix~=0);
Nr_Slices=numel(dicomsCT)-2;
Dim=[dcmCT.Rows dcmCT.Columns Nr_Slices];
Vox=[dcmCT.PixelSpacing(1) dcmCT.PixelSpacing(2) dcmCT.SliceThickness];
FOV=[dcmCT.Rows*dcmCT.PixelSpacing(1) dcmCT.Columns*dcmCT.PixelSpacing(2) dcmCT.SliceThickness*Nr_Slices]/10;
kVP=dcmCT.KVP;

if isempty(kVP)
    kVP=0;
end
Expo=dcmCT.ExposureTime;
Curr= dcmCT.XrayTubeCurrent;

if ~isfield(dcmCT,'AcquisitionDate')
    dcmCT.AcquisitionDate=dcmCT.StudyDate;
    dcmCT.AcquisitionTime=dcmCT.StudyTime;
    %     warning('No Acq date, return!')
    %     Dim=[0 0 0];
    %     Vox=[0 0 0];
    %     FOV=Vox;
    %     kVP=0;
    %     Expo=0;
    %     Curr=0;
    %     return
end

Time=str2num(dcmCT.AcquisitionTime);

if ~isfield(dcmCT,'StudyDescription')
    dcmCT.StudyDescription='none';
end


Other.PatientSex=dcmCT.PatientSex;
if isfield(dcmCT,'ProtocolName')
Other.ProtocolName=dcmCT.ProtocolName;
else
Other.ProtocolName='none';
end
Other.PatientBday=dcmCT.PatientBirthDate;
if isfield(dcmCT,'PatientWeight')
Other.PatientWeight=dcmCT.PatientWeight;
else
    Other.PatientWeight=0;
end
if isfield(dcmCT,'PatientAge')
Other.PatientAge=dcmCT.PatientAge;
else
    Other.PatientAge=0;
end
if isfield(dcmCT,'PatientLenght')
Other.PatientLenght=dcmCT.PatientLenght;
else
    Other.PatientLenght=0;
end
if isfield(dcmCT,'InstitutionName')
Other.InstitutionName=dcmCT.InstitutionName;
else
Other.InstitutionName='none';
end

Other.StudyName=dcmCT.StudyDescription;
if isfield(dcmCT,'SeriesDescription')
Other.SeriesName=dcmCT.SeriesDescription;
else
Other.SeriesName='none';
end

Other.Date= dcmCT.AcquisitionDate;
Other.Time=dcmCT.AcquisitionTime;
Other.ID=dcmCT.PatientID;
Other.ManufacturerModel=dcmCT.ManufacturerModelName;
Other.Manufacturer=dcmCT.Manufacturer;
Other.SoftwareVersion=dcmCT.SoftwareVersion;
Other.ScanOptions=dcmCT.ScanOptions;
Other.CTDIvol=dcmCT.CTDIvol;


if isempty(Other)
    Other=0;
end
if isempty(Time)
Time=0;
end
assignin('base','dcmCT',dcmCT)
assignin('base','dcmCT2',dcmCT2)

fprintf(['Acq date: %s @ %s ; PatiendID: %s (%s)\n',...
    '"%s" Imaging parameters on %s %s, %s %s  \n',...
    'Acq Matrix %ix%ix%i; Pixel=%.2fx%.2fx%.2f mm3,  FOV = %.1fx%.1fx%.1f cm3 \n'...,
    'KVP = %0.1f, Exposure Time %i ms, Current %i mA, Exposure %i mAs \n',...
    'CTDIvol = %0.3f \n ------------------\n'],...
    dcmCT.AcquisitionDate,dcmCT.AcquisitionTime,dcmCT.PatientID,dcmCT.PatientSex,...
    dcmCT.StudyDescription,dcmCT.Manufacturer,dcmCT.ManufacturerModelName,...
    dcmCT.Modality,dcmCT.ScanOptions,...
    dcmCT.Rows,dcmCT.Columns,Nr_Slices,...
    dcmCT.PixelSpacing(1),dcmCT.PixelSpacing(2),dcmCT.SliceThickness,...
    dcmCT.Rows*dcmCT.PixelSpacing(1)/10,dcmCT.Columns*dcmCT.PixelSpacing(2)/10,dcmCT.SliceThickness*Nr_Slices/10,...
    kVP,dcmCT.ExposureTime, dcmCT.XrayTubeCurrent, dcmCT.Exposure,...
    dcmCT.CTDIvol);

%     dcmCT.AcquisitionDuration);

end
