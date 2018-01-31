import csv
import os
import re
import logging
import urllib
from Levenshtein import jaro_winkler
from xlrd import open_workbook

from common.api import PreSeriesAPI
from common.utils import PreSeriesUtils

REGEX_MATCHER_UUID = re.compile(r"[a-zA-Z0-9_]{24}")
REGEX_MATCHER_DOMAIN = re.compile(r"(.*://)?(?:www\.)?(.[^/]+).*")

COUNTRIES_NAME = []
COUNTRIES_2LETTER_CODE = []
COUNTRIES_3LETTER_CODE = []

script_path = os.path.dirname(os.path.abspath(__file__))

# Loading the Country ISO codes
with open('%s/countries.csv' % script_path, 'rb') as f:
    reader = csv.reader(f, delimiter='\t')
    for country in reader:
        COUNTRIES_NAME.append(country[0].lower())
        COUNTRIES_2LETTER_CODE.append(country[1].lower())
        COUNTRIES_3LETTER_CODE.append(country[2].lower())


DEFAULT_API = PreSeriesAPI()


class PreSeriesSearcher(object):
    """This class encapsulates the logic to look for companies in PreSeries
    based on some basic information about them
    """

    def __init__(self, preseries_api=DEFAULT_API):
        self.api = preseries_api
        self.companies_query = []

    @staticmethod
    def select_best_company(query_params, candidates):
        """
        We are going to calculate the avg distance between the expected value
         for each parameter (name, domain) and the values of the candidates
         for them

        :param query_params: the values to check
        :param candidates: all the companies that matched with the
                previous params
        :return: the selected candidate that better match
        """

        logging.debug("Looking for the best match...")

        # All the distances for each param for each candidate
        ratios = []

        for index, candidate in enumerate(candidates):
            logging.debug("Candidate #%d: %s" % (index, candidate))
            candidate_ratios = []
            for param_name, param_value in query_params.iteritems():
                if param_name in candidate and candidate[param_name]:
                    candidate_ratios.append(
                        jaro_winkler(
                            str(param_value),
                            str(candidate[param_name].encode('utf-8'))))

            # Calculate the distance ratio as the AVG between all the computed
            # ratios for the candidate
            ratios.append(
                (float(sum(candidate_ratios)) / (len(query_params) - 1),
                 candidate))

        # The best match first
        ratios = reversed(sorted(ratios, key=lambda x: x[0]))

        # Return the select candidate being the best match
        return ratios.next()[1]

    def read_search_data_from_excel(
            self, file_name, column_id=None, column_name=None,
            column_country=None, column_domain=None, skip_rows=False):
        """
        This method is responsible for extract from an Excel file all the
        companies we will need to find in PreSeries.

        for build the query parameters that
        we are going to use to look for the companies in PreSeries informed
        in an Excel file.

        The query string will have only the id criteria or the name of the
         company if the id is not informed. The domain and country_code won't
         be used in the query, we will use them later for select the best
         match from all the candidates that matched the query.

        :return: a list where each row is one company which contains a tuple
            with two items, the query string to look in preseries for the
            company and the map with all the parameters used in the query
        """

        logging.debug("Looking for the first sheet in the Excel.")
        wb = open_workbook(file_name)
        first_sheet = wb.sheets()[0]
        logging.debug("Sheet name [%s]." % first_sheet.name)

        self.companies_query = []
        for row in range(skip_rows, first_sheet.nrows):

            logging.debug("Processing row: %d" % row)

            if column_id:
                company_id = first_sheet.cell_value(
                    row, PreSeriesUtils.excel2num(column_id))
                self.companies_query.append((
                    "id=%s" % company_id, {"row": row, "id": company_id}))
                continue

            query_string = {}
            query_params = {"row": row}

            if column_name and \
                    first_sheet.cell_value(
                        row, PreSeriesUtils.excel2num(column_name)):

                try:
                    company_name = first_sheet.cell_value(
                        row,
                        PreSeriesUtils.excel2num(column_name)).encode('cp1252')
                except UnicodeEncodeError:
                    company_name = first_sheet.cell_value(
                        row,
                        PreSeriesUtils.excel2num(column_name)).encode('utf-8')
                    pass

                query_string['name__icontains'] = company_name
                query_params["name"] = company_name

            if column_domain:
                company_domain = PreSeriesUtils.resolve_domain(
                    first_sheet.cell_value(
                        row, PreSeriesUtils.excel2num(column_domain)))

                if company_domain:
                    # We only use the domain after the search to select the
                    # best candidate
                    query_params["domain"] = company_domain

            if column_country and \
                    first_sheet.cell_value(
                        row, PreSeriesUtils.excel2num(column_country)):
                country_code = PreSeriesUtils.resolve_country(
                    first_sheet.cell_value(
                        row, PreSeriesUtils.excel2num(column_country)))

                if country_code:
                    # We only use the country_code after the search to
                    # select the best candidate
                    query_params['country_code'] = country_code

            self.companies_query.append(
                (urllib.urlencode(query_string), query_params))

    def search_companies(self):
        """
        We are going to get all the Companies from PreSeries using the search
        url calculated for each Company.

        We use the internal field "companies_query" to prepare the search.
        This property has a list of tuples, where each tuple contains the
        following information:
            - the "query string" to do the REST query
            - the "company_details" as a map with all the field-values of
                the company we want to look for in PreSeries.

        Ex.

            query_string = name__icontains=prese
            company_details = {
                "name": "PreSeries",
                "country_code": "ESP",
                "domain": "preseries.com"
            }

        The query string could, and should, not use all the company properties
        in the query to be more flexible. For instance, we can only prepare
        query strings using the "name" property to get from PreSeries
        as much companies as possible, to use later all the other properties
        (country_code, domain, etc) to decide which company is more likely to
        be the company we are looking for.

        :return: the companies found and the ones that were not found
        """
        found_companies = []
        unknown_companies = []

        for query_string, company_details in self.companies_query:
            # We download a maximum of 100 companies from the total that
            # matches the search criteria (limit=100)
            query = "limit=100&%s" % query_string
            logging.debug("Query: %s" % query)

            resp = self.api.search_companies(query_string=query)

            # We get multiple companies as a response.
            if resp['meta']['total_count'] > 1:
                best_candidate = PreSeriesUtils.select_best_company(
                    company_details, resp['objects'])

                logging.warn("More than one match!\n"
                             "Params: %s \n"
                             "Selected candidate: %s" %
                             (company_details, best_candidate))

                company_data = {"row": company_details["row"]}
                company_data.update(best_candidate)

                found_companies.append(
                    PreSeriesUtils.encoding_conversion(company_data))

            elif resp['meta']['total_count'] == 0:
                logging.warn("Unknown company: %s" % company_details)
                unknown_companies.append(company_details)

            else:
                company_data = {"row": company_details["row"]}
                company_data.update(resp["objects"][0])
                found_companies.append(
                    PreSeriesUtils.encoding_conversion(company_data))

        return found_companies, unknown_companies
