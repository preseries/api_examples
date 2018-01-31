# api_examples
Examples of how to use the PreSeries.io RESTful API

This project will show how to use the API provided by PreSeries to automate 
processes inside the company.

You will find all the documentation of the API here: 
https://preseries.com/developers

## src/preseries/preseries_api/portfolio/import_companies

This example shows how to create a new Portfolio using the companies 
informed in and Excel file. 

You can run the script, after do the setup of the python environment, executing the following command from the folder  `src/preseries/api_examples`:

```{bash}
python portfolio/import_companies/script.py --file data/Top100.xlsx --portfolio-name "Dummy Port." --column-name=A --column-country=D --column-domain=C --skip-rows=1 --summary-columns="H G"
```


## src/preseries/preseries_api/companies/get_companies_data

This example shows how to export all the data available in 
PreSeries about the companies informed in and Excel file. 

You can run the script, after do the setup of the python environment, executing the following command from the folder  `src/preseries/api_examples`:

```{bash}
python companies/get_companies_data/script.py --file data/Top100.xlsx --column-name=A --column-country=E --column-domain=B --skip-rows=1 --summary-columns="J"
```
