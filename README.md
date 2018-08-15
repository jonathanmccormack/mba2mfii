# MBA2MFII

## Introduction

MBA2MFII is designed to quickly and accurately convert data from the [Measuring Mobile Broadband America](https://www.fcc.gov/general/measuring-mobile-broadband-performance) ("MBA" or "FCC Speed Test") app released by the [Federal Communications Commission](https://www.fcc.gov/) ("FCC") into the [Challenge Speed Test](https://www.usac.org/_res/documents/hc/pdf/MF-II-Challenge-Process_Data-Specifications.pdf) CSV file format required for the [Mobility Fund Phase II](https://www.fcc.gov/mobility-fund-phase-2) ("MF-II") Challenge Process.  Data recorded by the FCC Speed Test app can be exported in JSON format, which must be converted in order to be uploaded into the MF-II Challenge Process Portal, hosted by the [Universal Service Administrative Company](https://www.usac.org/) ("USAC").

Additional information about the MF-II Challenge Process, how to participate, and the USAC MF-II Challenge Portal is available on the [MF-II webpage](https://www.fcc.gov/mobility-fund-phase-2).

## System Requirements

MBA2MFII is a Python command-line program that is intended for POSIX platforms (Linux, macOS, etc.), but should work on Windows, and requires Python 3 in order to run.

## Usage

### Command-line

```console
Usage: mba2mfii [options] [INPUTS] [OUTPUT]

Optional Parameters:
    -i, --device-imei           Use specified Device IMEI
    -d, --device-id             Override device detection and use specified Device ID
    -p, --provider-id           Override provider detection and use specified Provider ID
        --clobber               Overwrite existing output file
        --dry-run               Perform all actions except writing output file
        --verbose               Increase verbosity to DEBUG level
    -h, --help, --usage         Show this usage message and quit
        --version               Show version information about this script
```

## Release Notes

### MBA2MFII Tool 0.0.1 [2018-08-15]

* Initial release
