# MBA2MFII

## Introduction

MBA2MFII is designed to quickly and accurately convert data from the [Measuring Mobile Broadband America](https://www.fcc.gov/general/measuring-mobile-broadband-performance) ("MBA" or "FCC Speed Test") app released by the [Federal Communications Commission](https://www.fcc.gov/) ("FCC") into the [Challenge Speed Test](https://www.usac.org/_res/documents/hc/pdf/MF-II-Challenge-Process_Data-Specifications.pdf) CSV file format required for the [Mobility Fund Phase II](https://www.fcc.gov/mobility-fund-phase-2) ("MF-II") Challenge Process.  Data recorded by the FCC Speed Test app can be exported in JSON format, which must be converted in order to be uploaded into the MF-II Challenge Process Portal, hosted by the [Universal Service Administrative Company](https://www.usac.org/) ("USAC").

Additional information about the MF-II Challenge Process, how to participate, and the USAC MF-II Challenge Portal is available on the [MF-II webpage](https://www.fcc.gov/mobility-fund-phase-2).

## Installing

MBA2MFII is a command-line script that supports Python 2.7 or Python 3.

Install and update using pip:

```console
pip install git+https://github.com/jonathanmccormack/mba2mfii
```

## Usage

### Command-line

```console
Usage: mba2mfii [options] [INPUT]... [OUTPUT]

Optional Parameters:
    -i, --device-imei           Use specified Device IMEI
    -d, --device-id             Override device detection and use specified Device ID
    -p, --provider-id           Override provider detection and use specified Provider ID
        --clobber               Overwrite existing output file
        --dry-run               Perform all actions except writing output file
        --verbose               Increase verbosity to DEBUG level
    -h, --help                  Show this usage message and quit
        --version               Show version information about this script
```

### Description

Converts one or more INPUTs to OUTPUT.

Arguments provided for INPUT should be either an individual JSON file or a folder containing JSON files exported from the FCC Speed Test app.  INPUT files are converted and exported as OUTPUT in CSV format matching the Challenge Speed Test file structure.
