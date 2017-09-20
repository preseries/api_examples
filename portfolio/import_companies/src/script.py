#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import logging
import traceback
import csv
import re
import requests

from Levenshtein import jaro_winkler
from xlrd import open_workbook

PRESERIES_PROTOCOL = 'https'
PRESERIES_HOST = "preseries.io"
PRESERIES_API_VERSION = "zion"

PRESERIES_COMPANIES_SEARCH_ENDPOINT = "/company_search"
PRESERIES_PORTFOLIO_ENDPOINT = "/portfolio"

PRESERIES_USERNAME = os.getenv("PRESERIES_USERNAME", None)
PRESERIES_API_KEY = os.getenv("PRESERIES_API_KEY", None)

if not PRESERIES_USERNAME:
    raise Exception(
        "The PRESERIES_USERNAME environment variable must be set")

if not PRESERIES_API_KEY:
    raise Exception(
        "The PRESERIES_API_KEY environment variable must be set")

PRESERIES_AUTH = "username=%s;api_key=%s" % \
                 (PRESERIES_USERNAME, PRESERIES_API_KEY)

PRESERIES_COMPANIES_URL = (PRESERIES_PROTOCOL + '://' + PRESERIES_HOST +
                           '/' + PRESERIES_API_VERSION +
                           PRESERIES_COMPANIES_SEARCH_ENDPOINT +
                           '?%s' % PRESERIES_AUTH)

PRESERIES_PORTFOLIO_URL = (PRESERIES_PROTOCOL + '://' + PRESERIES_HOST +
                           '/' + PRESERIES_API_VERSION +
                           PRESERIES_PORTFOLIO_ENDPOINT +
                           '?%s' % PRESERIES_AUTH)

REGEX_MATCHER_UUID = re.compile(r"[a-zA-Z0-9_]{24}")
REGEX_MATCHER_DOMAIN = re.compile(r"(.*://)?(?:www\.)?(.[^/]+).*")

COUNTRIES_NAME = []
COUNTRIES_3LETTER_CODE = []
COUNTRIES_2LETTER_CODE = []


def load_valid_countries():
    # Loading all the valid contry codes and names
    with open('countries.csv', 'rb') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            COUNTRIES_NAME.append(row[0].lower())
            COUNTRIES_2LETTER_CODE.append(row[1].lower())
            COUNTRIES_3LETTER_CODE.append(row[2].lower())


def excel2num(col_name):
    """
    Function to translate an Excel column name to a number/index
    
    :param col_name: the column name. Ex. 'A'
    :return: the index of the column
    """
    return reduce(lambda s, a: s*26+ord(a)-ord('A')+1, col_name, 0) - 1


def resolve_country(country_text):
    """
    We are going to look for the best match between the country_text informed
     and the ISO 3166-1 alfa-3 code
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

    similarity_ratios = reversed(sorted(similarity_ratios, key=lambda x: x[1]))

    return similarity_ratios.next()[0]


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


def select_best_company(query_params, candidates):
    """
    We are going to calculate the avg distance between the expected value for
     each parameter (name, domain) and the values of the candidates for them

    :param query_params: the values to check
    :param candidates: all the companies that matched with the previous params
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
            (float(sum(candidate_ratios))/len(candidate_ratios), candidate))

    # The best match first
    ratios = reversed(sorted(ratios, key=lambda x: x[0]))

    # Return the select candidate being the best match
    return ratios.next()[1]


def get_search_data(args):
    """
    This method is responsible for build the query parameters that we are going
    to use to look for the companies in PreSeries informed in the Excel file.
    
    The query string will have only the id criteria or the name/country_code 
        if the id is not informed. The domain won't we used in the query, we 
        will use it later for discriminate when we receive multiple companies as
        the result of the search.
    
    :param args: arguments passed to the script
    :return: a list where each row is one company which contains a tuple with 
    two items, the query string to look in preseries for the company and
    the map with all the parameters used in the query
    """

    logging.debug("Looking for the first sheet in the Excel.")
    wb = open_workbook(args.file_name)
    first_sheet = wb.sheets()[0]
    logging.debug("Sheet name [%s]." % first_sheet.name)

    companies_query = []

    for row in range(args.skip_rows, first_sheet.nrows):

        logging.debug("Processing row: %d" % row)

        if args.column_id:
            company_id = first_sheet.cell_value(row, excel2num(args.column_id))
            companies_query.append((
                "id=%s" % company_id, {"row": row, "id": company_id}))
            continue

        query_string = ""
        query_params = {"row": row}

        if args.column_name and \
                first_sheet.cell_value(row, excel2num(args.column_name)):
            company_name = first_sheet.cell_value(
                row, excel2num(args.column_name))

            query_string += "&" if len(query_string) > 0 else ""
            query_string += "name__icontains=%s" % company_name
            query_params["name"] = company_name

        if args.column_domain:
            company_domain = resolve_domain(
                first_sheet.cell_value(row, excel2num(args.column_domain)))

            if company_domain:
                # We only use the domain to solve multiplicity in results
                # not during the PreSeries search
                query_params["domain"] = company_domain

        if args.column_country and \
                first_sheet.cell_value(row, excel2num(args.column_country)):
            country_code = resolve_country(first_sheet.cell_value(
                row, excel2num(args.column_country)))

            query_string += "&" if len(query_string) > 0 else ""
            query_string += "country_code=%s" % country_code
            query_params['country_code'] = country_code

        companies_query.append((query_string, query_params))

    return companies_query


def find_companies(companies_query):
    """
    We are going to get all the Companies from PreSeries using the search url 
    calculated for each Company informed in the Excel file.
     
    :param companies_query: the query_string and parameters for each company
        we need to look for.
    :return: the companies found and the ones that were not founded
    """
    found_companies = []
    unknown_companies = []

    for query_string, query_params in companies_query:
        # We download a maximum of 100 companies from the total that
        # matches the search criteria (limit=100)
        url = "%s&limit=100&%s" % (PRESERIES_COMPANIES_URL, query_string)
        logging.debug("PreSeries URL: %s" % url)

        try:
            resp = requests.get(url).json()
        except Exception as e:
            logging.exception("Unable to get the results "
                              "from the server for URL: %s" % url)
            raise e

        # # We get multiple companies as a response.
        if resp['meta']['total_count'] > 1:
            best_candidate = select_best_company(query_params, resp['objects'])
            logging.warn("More than one match!\n"
                         "Params: %s \n"
                         "Selected candidate: %s" %
                         (query_params, best_candidate))
            found_companies.append(best_candidate)
        elif resp['meta']['total_count'] == 0:
            logging.warn("Unknown company: %s" % query_params)
            unknown_companies.append(query_params)
        else:
            found_companies.append(resp['objects'][0])

    return found_companies, unknown_companies


def create_portfolio(portfolio_name, companies):
    """
    It will create a new portfolio with all the companies requested in the
    original Excel file
    
    :param portfolio_name: the name we will use for the new portfolio 
    :param companies: all the companies found during the search
    :return: the ID of the new portfolio
    """

    body = {
        "name": portfolio_name,
        "companies": [company['id'] for company in companies]
    }

    logging.debug("PreSeries URL: %s" % PRESERIES_PORTFOLIO_URL)

    try:
        resp = requests.post(PRESERIES_PORTFOLIO_URL, json=body)
        return resp.text
    except Exception as e:
        logging.exception("Unable to create the portfolio. " 
                          "Portfolio: %s" % body)
        raise e


def main(args=sys.argv[1:]):
    """ Main
    :param args: List of arguments
    """

    try:
        logging.basicConfig(level=logging.DEBUG)

        # Process arguments
        parser = argparse.ArgumentParser(
            description="Import Companies into Portfolio",
            epilog="PreSeries, Inc")

        # The path to the file that contains the companies to import
        parser.add_argument('--file',
                            required=True,
                            action='store',
                            dest='file_name',
                            default=None,
                            type=str,
                            help="The path to the file that contains the "
                                 "companies to find and add to the portfolio."
                                 " Ex. '$HOME/files/companies.xls")

        # The name of the portfolio
        parser.add_argument('--portfolio-name',
                            required=True,
                            action='store',
                            dest='portfolio_name',
                            default=None,
                            type=str,
                            help="The path to be used as a local repository for"
                                 " all the instances of the same workflow."
                                 " Ex. '/data/etlprocess/papis_dataset'")

        # The letter of the column holding the PreSeries ID
        parser.add_argument('--column-id',
                            required=False,
                            action='store',
                            dest='column_id',
                            default=None,
                            help="The letter of the column that contains "
                                 "information about the PreSeries ID"
                                 " Ex. A")

        # The letter of the column holding the Company Name
        parser.add_argument('--column-name',
                            required=False,
                            action='store',
                            dest='column_name',
                            default=None,
                            help="The letter of the column that holds the"
                                 " company name"
                                 "Ex. 'PreSeries'")

        # The letter of the column holding the Company Country
        parser.add_argument('--column-country',
                            required=False,
                            type=str,
                            action='store',
                            dest='column_country',
                            default=None,
                            help="The letter of the column that holds the"
                                 " company country name following the"
                                 " ISO 3166 label or ISO 3166-1 alpha-3 letter."
                                 "If there is no match, we will use fuzzy logic"
                                 " to find the closest value."
                                 "Ex. 'Spain' or 'ESP'")

        # The letter of the column holding the Company Domain Name
        parser.add_argument('--column-domain',
                            required=False,
                            type=str,
                            action='store',
                            dest='column_domain',
                            default=None,
                            help="The letter of the column that holds the"
                                 " company domain name. We will clean up the"
                                 "value if it has other url characters like / "
                                 "or http, etc."
                                 "Ex. 'https://preseries.com' or "
                                 "'preseries.com'")

        # The number of rows we need to skip to get access to the company data
        # useful if the first rows are not related to the data itself, for
        # instance the header
        parser.add_argument('--skip-rows',
                            required=False,
                            type=int,
                            action='store',
                            dest='skip_rows',
                            default=0,
                            help="The number of rows we need to skip to get"
                                 " access to the data"
                                 "Ex. 1")

        args, unknown = parser.parse_known_args(args)

        load_valid_countries()

        companies_query = get_search_data(args)

        found_companies, unknown_companies = find_companies(companies_query)

        portfolio_id = create_portfolio(args.portfolio_name, found_companies)

        logging.info("Unknown companies: %s" % unknown_companies)

        logging.info(
            "Portfolio: http://preseries.com/dashboard/portfolio/"
            "companies?portfolio_id=%s" % portfolio_id)

    except Exception as ex:
        logging.exception("ERROR processing the task. Exception: [%s]" % ex)
        logging.exception("Stacktrace [%s]" % traceback.format_exc())
        exit(2)


if __name__ == "__main__":
    main()
