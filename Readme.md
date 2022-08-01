<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![GNU General Public License v3.0][license-shield]][https://github.com/SynthRAD2023/preprocessing/blob/db07f7007063243f2f3fdb2084db7ce288d0a070/LICENSE]


<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://synthrad2023.grand-challenge.org/">
    <img src="./SynthRAD_banner.png" alt="Logo" width="770" height="160">
  </a>


  <p align="center">
    Preprocessing script: from dicom to aligned nifty
    <br />
    <a href="https://github.com/SynthRAD2023/preprocessing"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/SynthRAD2023/preprocessing">View Demo</a>
    ·
    <a href="https://github.com/SynthRAD2023/preprocessing/issues">Report Bug</a>
    ·
    <a href="https://github.com/SynthRAD2023/preprocessing/issues">Request Feature</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

Here's a blank template to get started:
**To avoid retyping too much info. Do a search and replace with your text editor for the following:**
`github_username`, `repo_name`, `twitter_handle`, `email`


### Built With

* []()
* []()
* []()



<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
```sh
npm install npm@latest -g
```

### Installation

1. Clone the repo
```sh
git clone https://github.com/github_username/repo_name.git
```
2. Install NPM packages
```sh
npm install
```



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_



<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/github_username/repo_name/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Your Name - [@twitter_handle](https://twitter.com/twitter_handle) - email

Project Link: [https://github.com/github_username/repo_name](https://github.com/github_username/repo_name)



<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements

* []()
* []()
* []()





<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo.svg?style=flat-square
[contributors-url]: https://github.com/github_username/repo/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo.svg?style=flat-square
[forks-url]: https://github.com/github_username/repo/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo.svg?style=flat-square
[stars-url]: https://github.com/github_username/repo/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo.svg?style=flat-square
[issues-url]: https://github.com/github_username/repo/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo.svg?style=flat-square
[license-url]: https://github.com/github_username/repo/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/github_username
[product-screenshot]: images/screenshot.png


# Pre-processing data for synthRAD2023 Grand Challenge

## Goal

Considering the ``.dcm`` of the MRI (or CBCT), CT of each patient, register to the CT reference grid
after resampling and cropping to reduce the amount of data to be considered for the challenge.

## Requirements
The following python libraries are required:
* numpy
* SimpleITK (pip install SimpleITK)
* SimpleElastix (pip install SimpleITK-SimpleElastix)

## Philosophy

The main file ``pre_process_tools.py`` is meant to:
* Convert Dicom to nifti (MRI+CT);
* Resample CT to 1x1x1 (for brain);
* Register MR to CT (as a result MRI will also have 1x1x1 spacing) using Elastix;
* Segment patient outline on MRI an dilate mask;
* Mask MRI and CT;
* Crop MRI an CT with a small extra margin to the dilated mask;

Each of the task can be run as a subfunction of the main file, as describe in the next section.

### Functions descriptions

**convert_dicom_nifti(input, output)**

	description:
	convert a dicom image to compressed nifti using SimpleITK
	
	arguments:
	input: folder containing dicom series (example 'C:\path\containing\Dicom_series')
	output: output file path for compressed nifti (example: 'C:\path\to\folder\image.nii.gz')

	command line usage:
	python pre_process_tools.py convert_dicom_to_nifti --i 'C:\path\containing\Dicom_series' --o 'C:\path\to\folder\image.nii.gz'


**resample(input, output, spacing)**

	description:
	resample nii.gz image using custom spacing (in mm)

	arguments:
	input: file path input image (example: 'C:\path\to\folder\image.nii.gz')
	output: file path resampled image (example: 'C:\path\to\folder\image_resampled.nii.gz')
	spacing: new spacing in mm (example: (1,1,1))

	command line usage:
	python pre_process_tools.py resample --i 'C:\path\to\folder\image.nii.gz' --o 'C:\path\to\folder\image_resampled.nii.gz' --s (1,1,1)


**create_parameter_map()**
	
	description:
	create a parameter map for registration using elastix, currently no input arguments, returns parameter map object


**register(fixed, moving,parameter, output)**
	
	description:
	register two images using elasix parameter map

	arguments:
	fixed: file path to fixed image for registration (example: 'C:\path\to\folder\fixed.nii.gz')
	moving: file path to moving image for registration (example: 'C:\path\to\folder\moving.nii.gz')
	parameter: parameter map (example: create_parameter_map())
	output: file path to registered image (example: 'C:\path\to\folder\moving_registered.nii.gz')

	command line usage:
	python pre_process_tools.py register --f C:\path\to\folder\fixed.nii.gz' --m 'C:\path\to\folder\moving.nii.gz' --o 'C:\path\to\folder\moving_registered.nii.gz'


**segment(input, output, radius)**
	
	description:
	create a rough body mask for MR/CBCT/CT image

	arguments:
	input: file path input image (example: 'C:\path\to\folder\image.nii.gz')
	output: file path mask (example: 'C:\path\to\folder\mask.nii.gz')
	radius: currently not used (radius to fill holes in mask), default value =  (12,12,12)
	

**mask(input, mask, mask_value, output)**

	description:
	mask an image with provided mask (e.g. created by segment above)

	arguments:
	input: file path input image (example: 'C:\path\to\folder\image.nii.gz')
	mask: file path to mask (example: 'C:\path\to\folder\mask.nii.gz')
	mask_value: value to assign to voxels outside mask (ususally 0 for MR, -1000 for CT)
	output: file path to masked image (example: 'C:\path\to\folder\image_masked.nii.gz')


**crop(input, mask, output)**

	description:
	crop an image with bounding box of mask image

	arguments:
	input: file path input image (example: 'C:\path\to\folder\image.nii.gz')
	mask: file path to mask, used to calculate bounding box (example: 'C:\path\to\folder\mask.nii.gz')
	output: file path to cropped image (example: 'C:\path\to\folder\image_cropped.nii.gz')




