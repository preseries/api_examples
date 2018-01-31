import csv
import os
import re
import logging
import urllib
from Levenshtein import jaro_winkler
from xlrd import open_workbook

from common.api import PreSeriesAPI

REGEX_MATCHER_UUID = re.compile(r"[a-zA-Z0-9_]{24}")
REGEX_MATCHER_DOMAIN = re.compile(r"(.*://)?(?:www\.)?(.[^/]+).*")

COUNTRIES_NAME = []
COUNTRIES_2LETTER_CODE = []
COUNTRIES_3LETTER_CODE = []

script_path = os.path.dirname(os.path.abspath(__file__))

# Loading the Country ISO codes
with open('%s/countries.csv' % script_path, 'rb') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        COUNTRIES_NAME.append(row[0].lower())
        COUNTRIES_2LETTER_CODE.append(row[1].lower())
        COUNTRIES_3LETTER_CODE.append(row[2].lower())


DEFAULT_API = PreSeriesAPI()


class PreSeriesUtils(object):
    """This class encapsulates some common utility methods

    """

    @staticmethod
    def excel2num(col_name):
        """
        Function to translate an Excel column name to a number/index

        :param col_name: the column name. Ex. 'A'
        :return: the index of the column
        """
        return reduce(lambda s, a: s * 26 + ord(a) - ord('A') + 1, col_name,
                      0) - 1

    @staticmethod
    def encoding_conversion(company_data):
        """
        We use this function to convert all the string values in the
        company_data map into utf-8 versions of the strings

        :param company_data: the company values loaded from the server
        :return: the company values with the string ones converted into utf-8
        """
        for key, value in company_data.iteritems():
            if isinstance(value, (str, unicode)):
                company_data[key] = value.encode('utf-8')

        return company_data

    @staticmethod
    def resolve_country(country_text):
        """
        We are going to look for the best match between the country_text
        informed and the ISO 3166-1 alfa-3 code
        :param country_text: the text about the country
        :return: the ISO 3166-1 alfa-3 code
        """

        country_text = str(country_text.lower())

        # Check if the country_text is an ISO 3166-1 alfa-3 code
        try:
            if COUNTRIES_3LETTER_CODE.index(country_text):
                return country_text.upper()
        except ValueError:
            pass

        # Check if the country_text is an ISO 3166-1 alfa-2 code
        try:
            if COUNTRIES_2LETTER_CODE.index(country_text):
                return COUNTRIES_3LETTER_CODE[
                    COUNTRIES_2LETTER_CODE.index(country_text)].upper()
        except ValueError:
            pass

        # Check if the country_text is a recognized name
        try:
            if COUNTRIES_NAME.index(country_text):
                return COUNTRIES_3LETTER_CODE[
                    COUNTRIES_NAME.index(country_text)].upper()
        except ValueError:
            pass

        # Look for the closest name to the one informed using
        # the levenshtein distance
        similarity_ratios = []
        for index, valid_country_name in enumerate(COUNTRIES_NAME):
            similarity_ratios.append((
                COUNTRIES_3LETTER_CODE[index].upper(),
                jaro_winkler(valid_country_name, str(country_text))))

        similarity_ratios = reversed(
            sorted(similarity_ratios, key=lambda x: x[1]))

        return similarity_ratios.next()[0]

    @staticmethod
    def resolve_domain(url):
        """
        Clean the url to get only the domain part.
        Ex:
            url = http://stackoverflow.com/questions/5343288/get-url/
            domaon =  stackoverflow.com

        :param url: the url from which we will get the domain
        :return: the domain name associated to the informed url
        """

        if url:
            matcher = REGEX_MATCHER_DOMAIN.match(url)
            if matcher:
                return matcher.group(2)

        return None

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

    @staticmethod
    def get_search_data(file_name, column_id=None, column_name=None,
                        column_country=None, column_domain=None,
                        skip_rows=False):
        """
        This method is responsible for build the query parameters that
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

        companies_query = []
        for row in range(skip_rows, first_sheet.nrows):

            logging.debug("Processing row: %d" % row)

            if column_id:
                company_id = first_sheet.cell_value(
                    row, PreSeriesUtils.excel2num(column_id))
                companies_query.append((
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

            companies_query.append(
                (urllib.urlencode(query_string), query_params))

        return companies_query, first_sheet

    @staticmethod
    def xpath_get(mydict, path, default=""):
        elem = mydict
        try:
            for x in path.strip("/").split("/"):
                elem = elem.get(x)
        except Exception:
            elem = default
            pass

        return elem

    @staticmethod
    def dump_opbjects(headers, fields, resources):

        rows = []
        rows.append(headers)

        for resource in resources:
            row = [field_value.encode('utf-8').decode('utf-8', 'ignore')
                   if isinstance(field_value, (str, unicode))
                   else '|'.join([
                        item.encode('utf-8').decode('utf-8', 'ignore')
                        if isinstance(item, (str, unicode))
                        else item for item in field_value])
            if isinstance(field_value, (list))
            else field_value for field_value in [
                PreSeriesUtils.xpath_get(resource, field_name)
                for field_name in fields]]

            rows.append(row)

        return rows
