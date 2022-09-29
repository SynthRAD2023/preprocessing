function data=ImagParamsold( pat,ext )
%ImagParams print on screen some image parameters for MR
% The input is the path to the folder containing the dicom files
% Developed by m.maspero@umcutrecht.nl, 2015
% In case of comments/improvements just let me know
if nargin<2
    ext='/mr*.dcm*';
else
end
disp(pat)
dicomsMR=dir(fullfile(pat,ext));

if numel(dicomsMR)==0
    error('No Dicom file with .dcm extension')
end
%%
if numel(dicomsMR)>6
    dcmMR=dicominfo([pat,'/',dicomsMR(5).name]);
    dcmMR2=dicominfo([pat,'/',dicomsMR(6).name]);
else
    dcmMR=dicominfo([pat,'/',dicomsMR(1).name]);
    dcmMR2=0;
end
assignin('base','dcmMR',dcmMR)
assignin('base','dcmMR2',dcmMR2)
if ~strcmp(dcmMR.Modality,'MR')
    warning('The selected dicoms are not MR images')
end
%% Image Type string
j=0;t=0;
Eco=zeros(1,2);
Typ=cell(1);
for ii=2:5:numel(dicomsMR)-1;
    
    j=j+1;
    dcm=dicominfo([pat,'/',dicomsMR(ii).name]);
    if isfield(dcm,'ImageType')
        Typ{j}=dcm.ImageType;
        if isempty(strfind(Typ{j},'ORIGINAL'))
        else
            t=t+1;
              if isfield(dcmMR,'EchoTime')
                 Eco(t)=dcmMR.EchoTime;
              else
                  Eco(t)=0;
              end
        end
    else
        Typ{j}='none';
        %t=t+1;
        %Eco(t)=0;
    end
end

Ecco=sort(unique(Eco));
if numel(Typ)==1
    T=Typ{1};
else
    T=unique(Typ);
end
if numel(dicomsMR)>6
    A=horzcat(T{:});
else
    A=T;
end
if isnumeric(A)
    A=num2str(A);
end
Type=([regexp(A,['\\M\'],'match');regexp(A,['\\IP\'],'match');regexp(A,['\\OP\'],'match');...
    regexp(A,['\\R\'],'match');regexp(A,['\\I\'],'match');regexp(A,['\\P\'],'match');...
    regexp(A,['\\W\'],'match');regexp(A,['\\F\'],'match')]);
% A=cell2struct(horzcat(Type),'Type',1);

if ~isfield(dcmMR,'SeriesDescription')
    dcmMR.SeriesDescription='none';
end

if ~isempty(regexp(dcmMR.SeriesDescription,['\w*B1 calibration\w*']))
    fprintf(['Acq date: %s @ %s ; PatiendID: %s \n "%s" \n'],...
        dcmMR.StudyDate,dcmMR.StudyTime,dcmMR.PatientID,...
        dcmMR.SeriesDescription)
else
    if isfield(dcmMR,'MagneticFieldStrength')
        data.FieldStrength = dcmMR.MagneticFieldStrength;
    else
        data.FieldStrength = 0;
    end
    data.PrecessionIsClockwise = 1;
    if isfield(dcmMR,'AcquisitionMatrix')
        AcqMat=dcmMR.AcquisitionMatrix(dcmMR.AcquisitionMatrix~=0);
    else
        AcqMat=[0 0 0 ];
    end
    if isfield(dcmMR,'Private_2001_1018')
        Nr_Slices=dcmMR.Private_2001_1018(1);
    elseif isfield(dcmMR,'MRSeriesNrOfSlices')
        Nr_Slices=dcmMR.MRSeriesNrOfSlices;
    else
        Nr_Slices=numel(dicomsMR)-2;
    end
    %%
    if isfield(dcmMR,'RepetitionTime')
        data.TR = dcmMR.RepetitionTime;
    else
        data.TR = 0;
    end
    
    if Ecco(1)==0
        data.TE(1:numel(Ecco)-1) = Ecco(2:end);
        nrEcho=numel(Ecco)-1;
    else
        data.TE(1:numel(Ecco)) =Ecco;
        nrEcho=numel(Ecco);
    end
    if numel(Ecco)==1
        nrEcho=1;
        if Ecco==0
            if isfield(dcmMR,'EchoTime')
                data.TE=dcmMR.EchoTime;    else
                data.TE=0;
            end
            %    data.TR=0.;
        end
    end
    data.Type=Type;
    
    if ~isfield(dcmMR,'SpacingBetweenSlices')
        dcmMR.SpacingBetweenSlices=0;
    end
    if ~isfield(dcmMR,'PixelSpacing')
        dcmMR.PixelSpacing=[0 0];
    end
    if ~isfield(dcmMR,'Rows')
        dcmMR.Rows=0;
    end
    if ~isfield(dcmMR,'Columns')
        dcmMR.Columns=0;
    end
    
    data.VoxelSize=[dcmMR.PixelSpacing(1),dcmMR.PixelSpacing(2),dcmMR.SpacingBetweenSlices];
    data.Size=[dcmMR.Rows,dcmMR.Columns,Nr_Slices];
    %if isfield(dcmMR,'Private_2005_140f.Item_1.Spoiling')
    if isfield(dcmMR,'Private_2005_140f.Item_1.Spoiling')
        Spoil=dcmMR.Private_2005_140f.Item_1.Spoiling;
    else
        Spoil='Nkn';
    end
    
    %elseif isfield(dcmMR,'PrivatePerFrameSq.Item_1.Spoiling')
    %Spoil=dcmMR.PrivatePerFrameSq.Item_1.Spoiling;
    %else
    %Spoil='Spoiled?';
    %end
    
    
    if isfield(dcmMR,'Private_2001_1020')
        Sequence=dcmMR.Private_2001_1020;
    elseif  isfield(dcmMR,'MRImageScanningSequencePrivate')
        Sequence=dcmMR.MRImageScanningSequencePrivate;
    else
        Sequence='Not KN';
    end
    
    if ~isfield(dcmMR,'AcquisitionDuration')
        dcmMR.AcquisitionDuration='0';
    end
    if ~isfield(dcmMR,'AcquisitionDate')
        data.AcquisitionDate=dcmMR.StudyDate;
        data.AcquisitionTime=dcmMR.StudyTime;
    else
        data.AcquisitionDate=dcmMR.AcquisitionDate;
        data.AcquisitionTime=dcmMR.AcquisitionTime;
    end
    data.PatientSex=dcmMR.PatientSex;
    data.ProtocolName=dcmMR.ProtocolName;
    data.PatientBday=dcmMR.PatientBirthDate;
    data.PatientWeight=dcmMR.PatientWeight;
    if isfield(dcmMR,'PatientAge')
        data.PatientAge=dcmMR.PatientAge;
    else
        data.PatientAge=0;
    end
    if isfield(dcmMR,'PatientLenght')
        data.PatientLenght=dcmMR.PatientLength;
    else
        data.PatientLenght=0;
        if isfield(dcmMR,'PatientSize')
            data.PatientLenght=dcmMR.PatientSize;
        else
            data.PatientLenght=0;
        end
    end
    data.ProtocolName=dcmMR.ProtocolName;
       if isfield(dcmMR,'InstitutionName')
        data.InstitutionName=dcmMR.InstitutionName;
    else
        data.InstitutionName='none';
    end
    
    if isfield(dcmMR,'StudyDescription')
        data.StudyName=dcmMR.StudyDescription;
    else
        data.StudyName='none';
    end
    if isfield(dcmMR,'SeriesyDescription')
        data.SeriesName=dcmMR.SeriesDescription;
    else
        data.SeriesName='none';
    end
    
    if isfield(dcmMR,'MRAcquisitionType')
        data.MRAcquisitionType=dcmMR.MRAcquisitionType;
    else
        data.MRAcquisitionType='none';
    end
    if isfield(dcmMR,'ScanningSequence')
        data.ScanningSequence=dcmMR.ScanningSequence;
    else
        data.ScanningSequence='none';
    end
    
    if ~isfield(dcmMR,'SequenceVariant')
        dcmMR.SequenceVariant='none';
        
    end
    data.SequenceVar=dcmMR.SequenceVariant;
    if ~isfield(dcmMR,'FlipAngle')
        dcmMR.FlipAngle=0;
    end
    
    if ~isfield(dcmMR,'PixelBandwidth')
        dcmMR.PixelBandwidth=0;
    end
    
    if ~isfield(dcmMR,'NumberOfPhaseEncodingSteps')
        dcmMR.NumberOfPhaseEncodingSteps=0;
    end
    
    if ~isfield(dcmMR,'NumberOfAverages')
        dcmMR.NumberOfAverages=0;
    end
    
    data.NSA=dcmMR.NumberOfAverages;
    data.FlipAngle=dcmMR.FlipAngle;
    data.BandWidth=dcmMR.PixelBandwidth;
    data.AcquisitionDuration=dcmMR.AcquisitionDuration;
    data.ID=dcmMR.PatientID;
    data.Sex=dcmMR.PatientSex;
    data.AcqMat=[AcqMat(1) AcqMat(2) Nr_Slices];
    data.Averages=dcmMR.NumberOfAverages;
    
    if ~isfield(dcmMR,'EchoTrainLength')
        dcmMR.EchoTrainLength=0;
    end
    data.EchoTrain= dcmMR.EchoTrainLength;
    data.ManufacturerModel=dcmMR.ManufacturerModelName;
    data.Manufacturer=dcmMR.Manufacturer;
    data.SoftwareVersion=dcmMR.SoftwareVersion;
    
    %%
    
    fprintf(['Acq date: %s @ %s ; PatiendID: %s (%s)\n',...
        '"%s" Imaging parameters @  %.2f T, %s %s (%s): %s cartesian %s %s %s, %i-echo (%s) \n',...
        'TE1/TE2/TE... = %s ms; TR = %.2f ms; FA= %i deg; BW = %.1f Hz; \n',...
        'Acq Matrix %ix%ix%i, PhaseEnc(%i); Recon Matrix %ix%ix%i; Recon Res = %.1fx%.1fx%.1f mm \n ',...
        'FOV = %.1fx%.1fx%.1f mm \n'...,
        'NSA = %i ; Acq Duration = %.2f s\n',...
        'Image Type:\n %s \n --------------------- \n'],...
        data.AcquisitionDate,data.AcquisitionTime,dcmMR.PatientID,dcmMR.PatientSex,...
        dcmMR.ProtocolName,data.FieldStrength,data.Manufacturer,data.ManufacturerModel,data.SoftwareVersion,...
        data.MRAcquisitionType,...
        Spoil,...
        Sequence,...
        data.ScanningSequence,nrEcho,dcmMR.SequenceVariant,...
        num2str(horzcat(data.TE)),data.TR,dcmMR.FlipAngle,dcmMR.PixelBandwidth,...dcmMR.MRSeriesWaterFatShift,...
        AcqMat(1),AcqMat(2),Nr_Slices,dcmMR.NumberOfPhaseEncodingSteps,dcmMR.Rows,dcmMR.Columns,Nr_Slices,...
        data.VoxelSize,...
        dcmMR.Rows*dcmMR.PixelSpacing(1),dcmMR.Columns*dcmMR.PixelSpacing(2),dcmMR.SpacingBetweenSlices*Nr_Slices,...
        dcmMR.NumberOfAverages,dcmMR.AcquisitionDuration,horzcat(Type{:}));
end
end
