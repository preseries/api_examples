#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import logging
import traceback

from common.api import PreSeriesAPI
from common.utils import PreSeriesUtils
from common.searcher import PreSeriesSearcher

from xlrd import open_workbook
from xlwt import Workbook

API = PreSeriesAPI()


def write_to_file(file_name, companies, summary_columns, wb_sheet):
    """
    This method generates a new Excel file the name <file_name> with
    the data associated to all the companies passed as parameter in companies


    :param file_name: the name of the file to be generated
    :param companies: all the companies found and not found in PreSeries with
        its reference to the row num of the original file
    :param summary_columns: the columns in the original file that will be
        used in the new file to give more information about the companies.
    :param wb_sheet: the excel sheet of the original file where we will find
        the summary fields of the companies.
    """
    workbook = Workbook()
    sheet = workbook.add_sheet('Companies')

    # Build the header names
    header = ["Original Row", "Company Name", "Domain", "Country"]
    header.extend(summary_columns) \
        if summary_columns and len(summary_columns) > 0 else None
    [sheet.write(0, index, value) for index, value in enumerate(header)]

    for index, company_data in enumerate(companies):
        sheet.write(1 + index, 0, company_data["row"])
        sheet.write(1 + index, 1, company_data["name"].decode('utf-8', 'ignore')
                    if "name" in company_data else "")
        sheet.write(1 + index, 2, company_data["country_code"]
                    if "country_code" in company_data else "")
        sheet.write(1 + index, 3, company_data["domain"]
                    if "domain" in company_data else "")
        for index2, summary_column in enumerate(summary_columns):
            try:
                columnvalue = wb_sheet.cell_value(
                    company_data["row"],
                    PreSeriesUtils.excel2num(summary_column)).encode('cp1252')
            except UnicodeEncodeError:
                columnvalue = wb_sheet.cell_value(
                    company_data["row"],
                    PreSeriesUtils.excel2num(summary_column)).encode('utf-8')
                pass

            sheet.write(1 + index, 4 + index2,
                        columnvalue.decode('utf-8', 'ignore'))
    workbook.save(file_name)


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

        # The letters of the columns that we want to use as addiction info
        # about the companies to be included in the output files.
        parser.add_argument('--summary-columns',
                            required=False,
                            type=str,
                            nargs='+',
                            action='store',
                            dest='summary_columns',
                            default=None,
                            help="The letters of the columns that we want"
                                 " to use to reference companies in the"
                                 " original excel file."
                                 "Ex. G H JJ")

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

        searcher = PreSeriesSearcher(preseries_api=API)

        searcher.read_search_data_from_excel(
            args.file_name, column_id=args.column_id,
            column_name=args.column_name, column_country=args.column_country,
            column_domain=args.column_domain, skip_rows=args.skip_rows)

        known_companies, unknown_companies = searcher.search_companies()

        # We create a portfolio with the companies that were found during
        # the search, that are the ones that contains the PreSeries ID (id) in
        # the data structure
        portfolio_id = API.create_portfolio(
            args.portfolio_name,
            [company["id"] for company in known_companies if "id" in company])

        # Reading the sheet that contains all the details about the companies
        # to be found. We will use this sheet to extract the summary fields
        # of each company for enrich the final Excel file.
        wb = open_workbook(args.file_name)
        wb_sheet = wb.sheets()[0]

        write_to_file('Unknown_companies.xls',
                      unknown_companies, args.summary_columns, wb_sheet)

        write_to_file('Known_companies.xls',
                      known_companies, args.summary_columns, wb_sheet)

        logging.info("Unknown companies: %d" % len(unknown_companies))
        logging.info("Known companies: %d" % len(known_companies))

        logging.info(
            "Portfolio: http://preseries.com/dashboard/portfolio/"
            "companies?portfolio_id=%s" % portfolio_id)

    except Exception as ex:
        logging.exception("ERROR processing the task. Exception: [%s]" % ex)
        logging.exception("Stacktrace [%s]" % traceback.format_exc())
        exit(2)


if __name__ == "__main__":
    main()
