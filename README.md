# api_examples

Example queries for the PreSeries.io RESTful API

This documentation is step-by-step instruction guide on how to get the PreSeries API up and running and start performing queries in matter of minutes. The PreSeries API allows for an easy automate of PreSeries-related querie. Moreover, it integrates seamlessly with other software solutions. Do not hesitate to contact us at support@preseries.com for any questions, comments, or requests regarding our API and/or its related documentation.

This page focuses on how to set up a local environment in order import/export PreSeries predictions for lists of companies (in Excel format). The complete PreSeries API documentation can be found here: https://preseries.com/developers

Before starting with the instructions, please remember that you need to define your credentials as environment variables. More information can be found here: https://preseries.com/developers/authentication


## Setup

Before executing any of the examples mentioned in this document, you need to configure the environment properly. Please follow the instructions below:

### 1. Install Git

Git is a version control system for tracking changes in computer files and coordinating work on those files among multiple people.

Before you start using Git, you have to make it available on your computer. Even if Git is already installed, it is probably a good idea to update it to the latest version. You can either install it as a package, via another installer, or download the source code and compile it yourself.

You will find here the instructions on how to install Git on your computer: [Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)


### 2. Clone this project

You need to create a folder where the project will be cloned. We will reference to this folder as ```BASE_PATH```.

In order to clone the project to the folder we need to execute the following commands in a Terminal window:

  
```{bash}
  cd <BASE_PATH>
  git clone https://github.com/preseries/api_examples.git
```

  NOTE: You need to change <BASE_PATH> for the real path where the `api_examples` project will be cloned.

A new folder ```api_examples``` should appear now inside the ```BASE_PATH``` folder along with the contents of the cloned Github repo.

### 3. Install Anaconda distribution. 

Anaconda is a freemium open source distribution of the Python and R programming languages that aims to simplify package management and deployment.
  
To install Anaconda, choose the version corresponding to your operating system:
  
  - [Installing on Windows](https://conda.io/docs/user-guide/install/windows.html)
  - [Installing on MAC](https://conda.io/docs/user-guide/install/macos.html)
  - [Installing on Linux](https://conda.io/docs/user-guide/install/linux.html)

After the installation, it is necessary to update the ```$PATH``` environment variable to take into account the path to the bin directory of the new Anaconda installation. You need to edit the ```.bashrc``` file. Remember the path where Anaconda is installed, usually at the base of you home directory, under the folder anaconda3 (or 4, depending on the version installed).

You need to add the following line into your shell profile filec(you need to open a new Terminal window):

```{bash}
  cd $HOME
  echo "export PATH=$PATH:$HOME/anaconda3/bin" >> .bashrc
```

At the end of the installation you should be able to execute the following command (you need to open a new Terminal window):
  
```{bash}
  conda list
```

If a list of installed packages appears, you have succesfully completed the installation.
  
### 4. Create a new conda environment for the examples.

With conda, you can create, export, list, remove and update environments that have different versions of Python and/or packages installed.

You need to create a new environment to later run your examples. You now need to execute the following command from a Terminal window:


1. Create the environment

  ```{bash}
    conda create -n preseries_api_examples python=2.7
  ```
2. When conda asks you to proceed, type __y__:

  ```{bash}
    proceed ([y]/n)?
  ```
  
### 5. Activate the environment and install libraries
 
Before executing any of the examples, always remember to activate the conda environment. 

Activate the environment:

    - On Windows, in your Anaconda Prompt, run ```activate preseries_api_examples```
    
    - On macOS and Linux, in your Terminal Window, run ```source activate preseries_api_examples```

You need to change the working directory (current folder) to the ```$BASE_PATH/api_examples``` path where the api_examples code has been cloned. Inside the folder you should be able to see the __setup.py__ file.

If you did not do it before, you need to install all the required libraries before running the examples:

  ```{bash}
      cd <BASE_PATH>/api_examples
      python setup.py install
  ```


## Examples

Before executing any of the following examples you need to open a new Terminal window and activate your environment as informed in the section [5. Activate the environment and install libraries](#5-activate-the-environment-and-install-libraries).

You also should change your current directory to ```<BASE_PATH>/api_examples/src/preseries/api_examples```:

  ```{bash}
      cd <BASE_PATH>/api_examples/src/preseries/api_examples
  ```
  
### Create a portfolio from an Excel file

This example shows how to create a new Portfolio using the companies informed in and Excel file. 

If you want to inspect the code you can find it inside the following folder:

```{bash}
<BASE_PATH>/src/preseries/preseries_api/portfolio/import_companies
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

This example shows how to export all the data available in PreSeries about companies informed in an Excel file. 

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
