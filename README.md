# api_examples

Examples of how to use the PreSeries.io RESTful API

The aim of this project is to show you how to use the API provided by PreSeries to automate processes inside the company.

You will find all the documentation of the API here: https://preseries.com/developers

Remember that you need to define your credentials as environment variables, as its explained here: https://preseries.com/developers/authentication


## Setup

The first thing we need to do, before execute any of the following examples, is to setup our environment.

To do so, we need to do the following tasks:

### 1. Install Git

Git is a version control system for tracking changes in computer files and coordinating work on those files among multiple people.

Before you start using Git, you have to make it available on your computer. Even if it’s already installed, it’s probably a good idea to update to the latest version. You can either install it as a package or via another installer, or download the source code and compile it yourself.

You will find here the instructions on how to install Git in your computer: [Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)


### 2. Clone this project

We should decide the folder where we want to clone this project. We will reference this folder henceforth as ```$BASE_PATH```.

To clone the project we only need to execute the following commands in a Terminal window:

  
```{bash}
  cd $BASE_PATH
  git clone https://github.com/preseries/api_examples.git
```

A new folder ```api_examples``` should appear now inside the ```$BASE_PATH``` folder with the contents of this Github repo.

### 3. Install Anaconda distribution. 

Anaconda is a freemium open source distribution of the Python and R programming languages that aims to simplify package management and deployment.
  
To install Anaconda we can follow the following instructions, depending on our operating system:
  
  - [Installing on Windows](https://conda.io/docs/user-guide/install/windows.html)
  - [Installing on MAC](https://conda.io/docs/user-guide/install/macos.html)
  - [Installing on Linux](https://conda.io/docs/user-guide/install/linux.html)
  
At the end of the installation we should be able to execute the following command in a new Terminal window:
  
```{bash}
  conda list
```

For a successful installation, a list of installed packages appears.
  
### 4. Create a new conda environment for the examples.

With conda, you can create, export, list, remove and update environments that have different versions of Python and/or packages installed.

We need to create a new environment for our examples, and we will do that executing the following command from a Terminal window:


1. Create the environment

  ```{bash}
    conda-env -c preseries_api_examples python=2.7
  ```
2. When conda asks you to proceed, type __y__:

  ```{bash}
    proceed ([y]/n)?
  ```
  
### 5. Activate the environment and install libraries
 
Before execute any of the examples, we always will need to activate the conda environment. 

Activate the environment:

    - On Windows, in your Anaconda Prompt, ```run activate preseries_api_examples```
    - On macOS and Linux, in your Terminal Window, ```run source activate preseries_api_examples```

We need to change the working directory (current folder) to the ```$BASE_PATH/api_examples``` path where the api_examples code has been cloned. Inside the folder we should be able to see the __setup.py__ file.

If we did not do it before, we would have to install all the required libraries before run the examples:

  ```{bash}
      cd $BASE_PATH/api_examples
      python setup.py install
  ```


## Examples

Before execute any of the following examples we should have to open a new Terminal window and activate our environment as informed in the section [5. Activate the environment and install libraries](#5-activate-the-environment-and-install-libraries).

We also should change our current directory to ```$BASE_PATH/api_examples/src/preseries/api_examples```:

  ```{bash}
      cd $BASE_PATH/api_examples/src/preseries/api_examples
  ```
  
### Create a portfolio from an Excel file

This example shows how to create a new Portfolio using the companies informed in and Excel file. 

If you want to inspect the code you can find it inside the following folder:

```{bash}
$BASE_PATH/src/preseries/preseries_api/portfolio/import_companies
```

To run the code you will need to execute the following command:

```{bash}
python portfolio/import_companies/script.py --file <MY_FILE_PATH> --portfolio-name "<MY PORTFOLIO NAE>" --column-name=<LETTER> --column-country=<LETTER> --column-domain=<LETTER> --skip-rows=<NUMBER> --summary-columns="<LETTERS>"
```

Accepted arguments:

    --file: the path where our excel file is located
    --portfolio-name: the name we want to give to our new portfolio
    --column-name: the letter of the column in the Excel file that contains the name of the company
    --column-country: the letter of the column in the Excel file that contains the name or 3-letter ISO code for the country of the company
    --column-domain: the letter of the column in the Excel file that contains the domain name of the company.
    --skip-rows: the number of rows of the Excel that we want to skip to start reading companies. Useful when the first row contains the column names.
    --summary-columns: here, we can declare a list of column letters separated by whitespace. These columns will be exported in the results files as additional information about the companies processed. Specially useful for those companies for which we were unable to find.

Example:

```{bash}
python portfolio/import_companies/script.py --file /Users/john/Documents/data/Top100.xlsx --portfolio-name "Dummy Port." --column-name=A --column-country=D --column-domain=C --skip-rows=1 --summary-columns="H G"
```

### Export companies data from an Excel file

This example shows how to export all the data available in PreSeries about the companies informed in and Excel file. 

If you want to inspect the code you can find it inside the following folder:

```{bash}
$BASE_PATH/src/preseries/preseries_api/companies/get_companies_data
```

To run the code you will need to execute the following command:

```{bash}
python companies/get_companies_data/script.py --file <MY_FILE_PATH> --column-name=<LETTER> --column-country=<LETTER> --column-domain=<LETTER> --skip-rows=<NUMBER> --summary-columns="<LETTERS>"
```

Accepted arguments:

    --file: the path where our excel file is located
    --column-name: the letter of the column in the Excel file that contains the name of the company
    --column-country: the letter of the column in the Excel file that contains the name or 3-letter ISO code for the country of the company
    --column-domain: the letter of the column in the Excel file that contains the domain name of the company.
    --skip-rows: the number of rows of the Excel that we want to skip to start reading companies. Useful when the first row contains the column names.
    --summary-columns: here, we can declare a list of column letters separated by whitespace. These columns will be exported in the results files as additional information about the companies processed. Specially useful for those companies for which we were unable to find.

Example:

```{bash}
python companies/get_companies_data/script.py --file /Users/john/Documents/data/Top100.xlsx --column-name=A --column-country=D --column-domain=C --skip-rows=1 --summary-columns="H G"
```
