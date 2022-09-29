%% ----------- -- Get_ImageProtocol_visualize -----------------------------
%
% Goal: to retrieve the image protocol from the dicom, and visualize the
% post-processed images
%
% Written by M. Maspero 2022-08. Radiotherapy Dep., UMC Utrecht 2022.
%
% -------------------------------------------------------------------------

%% Clean-up

clc; clear all;
close all;

Size_ftn=20; Name_ftn='Times New Roman';
set(0,'DefaultAxesFontSize',Size_ftn,'DefaultAxesFontName',Name_ftn,'DefaultTextFontname','Times New Roman');

%% Create flags to pick the seq type

Flag.flag_T1=1234;          % set to 1234 to pick that sequence type
Flag.contours_mask=123;     %set 1234 to plot the contours. N.B. a bug is currently present
Flag.save_fig=1234;         %set 1235 to save the plot

% Chosen sequence
Seq='T1';
Date_Anal='20220804';       % Date of the image evaluation

%% Settings parameters

% Write here as on which patients you want to run the analysis
Dataset='Brain';

% Locations: TO BE SET BY THE USER
Dir.homeData='location of your data';
Dir.homeSave='location of the processed data (nifti)';
Dir.homeSave_fig=['/nfs/arch11/researchData/PROJECT/SynthRAD/2023/data_mri2ct_fin/brain/figure/']; %where to store the figures
disp(['------------------------',Dataset])

%% Load the list of selected patients

ptlist_=importfile('../examples/pat_list_brain_mri2ct.txt');
PtName=ptlist_.PtName;
Phase=ptlist_.phase;

%% Counters
pp=0; % initialise
cnt_MR=0;
cnt_CT=0;


%% Loop over the patient

for ssssl=1:numel(Ptname)
    close all;
    pp=pp+1;
    
    Pt(pp)=pp;
    disp(['--------------------------------- ',Ptname{pp}])
    dirMR=dir([Dir.homeData,Ptname{pp},'/MRI/...path to MRI']);
    dirCT=dir([Dir.homeData,Ptname{pp},'/MRI/...path to CT']);
    
    %Names of the nifti files to open, this correspond to the names used in
    %the bash -> /preprocessing/examples/pre_process_batch_MR.sh
    filename_MR=['mr_cropped'];
    filename_CTmask=['ct_cropped'];
    filename_Mask=['mask_cropped'];
    
    % read dicom file of original MR and CT
    Dcm_dirMR=dir([Dir.homeData,Ptname{pp},'/MRI/',dateMR,'/',strrep(SeqMR{ll},'_sendto_','*sendto*'),'/Dc*']);
    Dcm_dirCT=dir([Dir.homeData,Ptname{pp},'/RTset/',dateCT,'/Dc*']);
    
    % update counters for MR and CT
    cnt_MR=cnt_MR+1;
    cnt_CT=cnt_CT+1;
    
    % extract MR dicom info
    tmp=dir([Dcm_dirMR.folder,'/',Dcm_dirMR.name,'/*']);
    
    %% Open Nifti MR, CT and mask
    MR_file=dir([Dir.homeSave,Phase{index},'/',Ptname{pp},'/',filename_MR,'.nii.gz']);
    disp('Opening MRI...')
    MR_info = niftiinfo([MR_file.folder,'/',MR_file.name]);
    MR=permute(niftiread(MR_info),[2 1 3]);
    
    CT_file=dir([Dir.homeSave,Phase{index},'/',Ptname{pp},'/',filename_CTmask ,'.nii.gz']);
    disp('Opening CT...')
    CT_info = niftiinfo([CT_file.folder,'/',CT_file.name]);
    CT=permute(niftiread(CT_info),[2 1 3]);
    
    Mask_file=dir([Dir.homeSave,Phase{index},'/',Ptname{pp},'/',filename_Mask ,'.nii.gz']);
    disp('Opening Mask...')
    Mask_info = niftiinfo([Mask_file.folder,'/',Mask_file.name]);
    Mask=permute(niftiread(Mask_info),[2 1 3]);
    
    %% Visualize MR and CT to control the quality of the registration
    [X,Y,Z]=size(MR);
    X=linspace(0,X,X);
    Y=linspace(0,Y,Y);
    Z=linspace(0,Z,Z);
    
    im_size=round(size(MR)/2);
    
    disp('Visualizing...')
    
    prc99=prctile(MR(:),99.5);
    
    figure
    subplot(231), imagesc(X,Y,MR(:,:,im_size(3)), [0  prc99] ), axis square off
    pos=get(gca,'Position'); pos(2)=0.52;pos(3:4)=pos(3:4)*1.05;  set(gca,'Position',pos);
    if Flag.contours_mask==1234
        hold on;  contour(Y,X,squeeze(Mask(:,:,im_size(3))),'LineColor','b','LineWidth',0.5);
    end
    subplot(232), imagesc(Y,Z, imrotate(squeeze(MR(im_size(1),:,:)),90),[0  prc99]), axis square off
    if Flag.contours_mask==1234
        hold on; contour(imrotate(squeeze(Mask(im_size(1),:,:)),90),'LineColor','b','LineWidth',0.5);
    end
    pos=get(gca,'Position');      pos(1)=0.365; pos(2)=0.52;pos(3:4)=pos(3:4)*1.05;      set(gca,'Position',pos);
    title('MR','FontName',Name_ftn)
    subplot(233), imagesc(X,Z, imrotate(squeeze(MR(:,im_size(2),:)),90),[0  prc99] ), axis square off, colormap(gray)
    pos=get(gca,'Position'); pos(1)=0.6; pos(2)=0.52;pos(3:4)=pos(3:4)*1.05;   set(gca,'Position',pos);
    if Flag.contours_mask==1234
        hold on; contour(imrotate(squeeze(Mask(:,im_size(2),:)),90),'LineColor','b','LineWidth',0.5);
    end
    originalSize1 = get(gca, 'Position'); colorbar; set(gca, 'Position', originalSize1);
    
    set(gcf,'Position',[500         2        1400         800])
    subplot(234), imagesc(X,Y,CT(:,:,im_size(3)),[-500 500]  ), axis square off
    if Flag.contours_mask==1234
        hold on;  contour(Y,X,squeeze(Mask(:,:,im_size(3))),'LineColor','b','LineWidth',0.5);
    end
    pos=get(gca,'Position'); pos(2)=0.02;pos(3:4)=pos(3:4)*1.05;  set(gca,'Position',pos);
    subplot(235), imagesc(Y,Z, imrotate(squeeze(CT(im_size(1),:,:)),90),[-500 500]), axis square off
    if Flag.contours_mask==1234
        hold on; contour(Y,Z,imrotate(squeeze(Mask(im_size(1),:,:)),90),'LineColor','b','LineWidth',0.5);
    end
    pos=get(gca,'Position');      pos(1)=0.365; pos(2)=0.02;pos(3:4)=pos(3:4)*1.05;      set(gca,'Position',pos);
    title('CT','FontName',Name_ftn)
    subplot(236), imagesc(X,Z, imrotate(squeeze(CT(:,im_size(2),:)),90),[-500 500]  ), axis square off
    pos=get(gca,'Position'); pos(1)=0.6; pos(2)=0.02;pos(3:4)=pos(3:4)*1.05;   set(gca,'Position',pos);
    originalSize1 = get(gca, 'Position'); colorbar; set(gca, 'Position', originalSize1);
    if Flag.contours_mask==1234
        hold on; contour(X,Z,imrotate(squeeze(Mask(:,im_size(2),:)),90),'LineColor','b','LineWidth',0.5);
    end
    if Flag.save_fig==1234
        saveas(gcf,[Dir.homeSave_fig,Ptname{ssssl},'_MR_CT_',Phase{index}],'png')
    end
    
    %% Retrieve info from dicom
    % read the MR dicom
    if isempty(tmp)
        
        tmp=dir([Dcm_dirMR.folder,'/',Dcm_dirMR.name,'/*dcm']);
        try
            [data]=ImagParamsold(tmp(1).folder,'/*dcm') ;
        catch Er
        end
    end
    
    % extract info from MR dicom
    if exist('data')
        MRstruct(cnt_MR).Num=cnt_MR;
        MRstruct(cnt_MR).PtLabel=Ptname{pp};
        %                            MRstruct(cnt_MR).Time=data.AcquisitionTime;
        MRstruct(cnt_MR).Dim=data.Size;
        MRstruct(cnt_MR).Dim(3)=numel(tmp);
        MRstruct(cnt_MR).MagneticField=data.FieldStrength;
        MRstruct(cnt_MR).Vox=data.VoxelSize;
        MRstruct(cnt_MR).FOV=data.VoxelSize.*single(data.Size);
        %                            MRstruct(cnt_MR).InstitutionName=data.InstitutionName;
        %                            MRstruct(cnt_MR).SeriesName=data.SeriesName;
        MRstruct(cnt_MR).AcqTyp=data.MRAcquisitionType;
        MRstruct(cnt_MR).Dim_postpro=size(MR); %from nifti
        MRstruct(cnt_MR).Vox_postpro=MR_info.PixelDimensions; %from nifti
        MRstruct(cnt_MR).Seq=data.ScanningSequence;
        MRstruct(cnt_MR).SeqVariant=data.SequenceVar;
        MRstruct(cnt_MR).TR=data.TR;
        MRstruct(cnt_MR).TE=data.TE;
        MRstruct(cnt_MR).FlipAngle=data.FlipAngle;
        MRstruct(cnt_MR).SeqVariant=data.NSA;
        MRstruct(cnt_MR).EchoTrain=data.EchoTrain;
        MRstruct(cnt_MR).Duration=data.AcquisitionDuration;
        MRstruct(cnt_MR).PixelBandWidth=data.BandWidth;
        MRstruct(cnt_MR).SizeAcq=data.AcqMat;
        MRstruct(cnt_MR).Averages=data.Averages;
        MRstruct(cnt_MR).Type=cell2mat(data.Type');
        %        MRstruct(cnt_MR).PatientSex=data.PatientSex;
        MRstruct(cnt_MR).Date=data.AcquisitionDate;
        MRstruct(cnt_MR).ProtocolName=data.ProtocolName;
        MRstruct(cnt_MR).StudyName=data.StudyName;
        MRstruct(cnt_MR).Manufacturer=data.Manufacturer;
        MRstruct(cnt_MR).ManufacturerModel=data.ManufacturerModel;
        MRstruct(cnt_MR).SoftwareVersion=data.SoftwareVersion;
        %                        MRstruct(cnt_MR).DataLocation=[tmp(1).folder];
    end
    
    % extract CT dicom info
    tmp=dir([Dcm_dirCT.folder,'/',Dcm_dirCT.name,'/ct*']);
    if ~isempty(tmp)
        CTstruct(cnt_CT).Num=cnt_CT;
        CTstruct(cnt_CT).PtLabel=Contdir(ssssl).name;
        [CTstruct(cnt_CT).Dim,CTstruct(cnt_CT).Vox,CTstruct(cnt_CT).FOV,CTstruct(cnt_CT).kVP,CTstruct(cnt_CT).Expo,CTstruct(cnt_CT).Curr,CTstruct(cnt_CT).Time,Other]...
            =ImagParamsCT(tmp(1).folder) ;
        CTstruct(cnt_CT).ID=Other.ID;
        CTstruct(cnt_CT).Date=Other.Date;
        CTstruct(cnt_CT).Time=Other.Time;
        CTstruct(cnt_CT).ProtocolName=Other.ProtocolName;
        CTstruct(cnt_CT).StudyName=Other.StudyName;
        CTstruct(cnt_CT).SeriesName=Other.SeriesName;
        CTstruct(cnt_CT).Set=Phase{index};
        %                        CTstruct(cnt_CT).DataLocation=tmp(1).folder;
    end
end


%% Save CT & MR as .mat files and save excel sheets
save([Dir.homeSave,'/ImageInfo_',Dataset,'_',Date_Anal,'_',SequenceChoice],'MRstruct','CTstruct','Pt','cnt*')
writetable(struct2table(CTstruct),[Dir.homeSave,'/Overview_',Dataset,'_',Date_Anal,'_',SequenceChoice,'.xls'],'Sheet','CT','WriteVariableNames',true);
writetable(struct2table(MRstruct),[Dir.homeSave,'/Overview_',Dataset,'_',Date_Anal,'_',SequenceChoice,'.xls'],'Sheet','MR','WriteVariableNames',true);
