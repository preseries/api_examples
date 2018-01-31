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


def get_company_details(known_companies):
    """
    This method is responsible for obtain from PreSeries all the details
    associated to each of the companies we have in the known_companies
    parameter

    :param known_companies: the companies from which we want to obtain the data
    :return: the known_companies extended with all the details obtained from
    the server
    """

    offset = 0
    limit = 10

    companies_filter_template = \
        "only_last_snapshot=true&company_id__in=%s&" \
        "add_details=stages,company,founders,board_members,score_evolution"

    companies_filter = companies_filter_template % (
        ','.join([company['id']
                  for company in known_companies[offset:offset+limit]
                  if 'id' in company]))

    companies = []

    while True:
        response = API.get_company_data(companies_filter)

        # Adding the companies to the list
        companies.extend(response["resources"])

        # check if there are more companies to be queried
        if offset + limit >= len(known_companies):
            return companies

        # Next page
        offset = offset + limit

        # Check the limits
        limit = limit \
            if len(known_companies) - len(companies) >= limit \
            else len(known_companies) - len(companies)

        companies_filter = companies_filter_template % (
            ','.join([company['id']
                      for company in known_companies[offset:offset + limit]
                      if 'id' in company]))


def get_competitors(known_companies):
    """
    This method is responsible for obtain from Competitors of the companies
    we have in the known_companies parameter

    :param known_companies: the companies from which we want to obtain the data
    :return: a map with all the competitors by company id
    """

    offset = 0
    limit = 10

    companies_filter_template = "limit=%d&company_id__in=%s"

    companies_filter = companies_filter_template % (
        limit * 10,
        ','.join([company['id']
                  for company in known_companies[offset:offset+limit]
                  if 'id' in company]))

    by_company = {}

    while True:
        response = API.get_companies_competitors(companies_filter)

        for resource in response["resources"]:
            if resource["company_id"] not in by_company:
                by_company[resource["company_id"]] = []

            by_company[resource["company_id"]].append(resource)

        # check if there are more companies to be queried
        if offset + limit >= len(known_companies):
            return by_company

        # Next page
        offset = offset + limit

        # Check the limits
        limit = limit \
            if len(known_companies) - len(by_company) >= limit \
            else len(known_companies) - len(by_company)

        companies_filter = companies_filter_template % (
            limit * 10,
            ','.join([company['id']
                      for company in known_companies[offset:offset + limit]
                      if 'id' in company]))


def get_similar(known_companies):
    """
    This method is responsible for obtain from Similar companies of the
    companies we have in the known_companies parameter

    :param known_companies: the companies from which we want to obtain the data
    :return: a map with all the competitors by company id
    """

    offset = 0
    limit = 10

    companies_filter_template = "limit=%d&company_id__in=%s"

    companies_filter = companies_filter_template % (
        limit * 10,
        ','.join([company['id']
                  for company in known_companies[offset:offset+limit]
                  if 'id' in company]))

    by_company = {}

    while True:
        response = API.get_companies_similar(companies_filter)

        for resource in response["resources"]:
            if resource["company_id"] not in by_company:
                by_company[resource["company_id"]] = []

            by_company[resource["company_id"]].append(resource)

        # check if there are more companies to be queried
        if offset + limit >= len(known_companies):
            return by_company

        # Next page
        offset = offset + limit

        # Check the limits
        limit = limit \
            if len(known_companies) - len(by_company) >= limit \
            else len(known_companies) - len(by_company)

        companies_filter = companies_filter_template % (
            limit * 10,
            ','.join([company['id']
                      for company in known_companies[offset:offset + limit]
                      if 'id' in company]))


def dump_company_objects(companies_details):
    """ This methods generates s CSV-like version of the Company objects, a
    list of rows with columns
    """

    # These are the basic fields of the companies that we want to export
    headers = [
        'PreSeries ID'.encode('utf8'),
        'Name'.encode('utf8'),
        'Elevator Pitch'.encode('utf8'),
        'Foundation date'.encode('utf8'),
        'Domain'.encode('utf8'),
        'Status'.encode('utf8'),
        'Country'.encode('utf8'),
        'City'.encode('utf8'),
        'Stage'.encode('utf8'),
        'Areas'.encode('utf8'),
        'Top Area'.encode('utf8'),
        'Headcount'.encode('utf8'),
        'Num of Founders'.encode('utf8'),
        'Locations'.encode('utf8'),
        'Diversification'.encode('utf8'),
        'Funding rounds'.encode('utf8'),
        'Total Funding'.encode('utf8'),
        'First funding on'.encode('utf8'),
        'Days to first funding'.encode('utf8'),
        'Last funding on'.encode('utf8'),
        'Days since last funding'.encode('utf8'),
        'Num of MBAs'.encode('utf8'),
        'Num of PhDs'.encode('utf8'),
        'Num of patents first year'.encode('utf8'),
        'Num of patents last year'.encode('utf8'),
        'Twitter bio'.encode('utf8'),
        'Twitter followers'.encode('utf8'),
        'Twitter following'.encode('utf8'),
        'Twitter tweets'.encode('utf8'),
        'Twitter url'.encode('utf8'),
        'Crunchbase url'.encode('utf8'),
        'LinkedIn url'.encode('utf8'),
        'Facebook url'.encode('utf8'),
        'Google Plus url'.encode('utf8'),
        'IPO %'.encode('utf8'),
        'Acquired %'.encode('utf8'),
        'Defunct %'.encode('utf8'),
        'Ratio - Influencer'.encode('utf8'),
        'Ratio - Traction'.encode('utf8'),
        'Country Rank'.encode('utf8'),
        'Country Rank Change'.encode('utf8'),
        'Country Rank Percentile'.encode('utf8'),
        'Country Rank Percentile Change'.encode('utf8'),
        'Area Rank'.encode('utf8'),
        'Area Rank Change'.encode('utf8'),
        'Area Rank Percentile'.encode('utf8'),
        'Area Rank Percentile Change'.encode('utf8'),
        'World Rank'.encode('utf8'),
        'World Rank Change'.encode('utf8'),
        'World Rank Percentile'.encode('utf8'),
        'World Rank Percentile Change'.encode('utf8'),
        'Score'.encode('utf8'),
        'Score Change'.encode('utf8'),
        'Tracked from'.encode('utf8'),
        'Updated on'.encode('utf8')]

    fields = [
        "company_id",
        "name",
        "company/elevator_pitch",
        "foundation_date",
        "domain",
        "status",
        "country_code",
        "city",
        "stage",
        "areas",
        "top_area",
        "headcount",
        "num_of_cofounders",
        "locations_list",
        "diversity_list",
        "funding_count",
        "funding_sum",
        "first_funding_on",
        "days_to_first_funding",
        "last_funding_on",
        "days_since_last_funding",
        "num_of_mbas",
        "num_of_phds",
        "num_patents_1st_year",
        "num_patents_on_exit_0",
        "twitter_bio",
        "twitter_followers",
        "twitter_following",
        "twitter_tweets",
        "twitter_url",
        "company/crunchbase_url",
        "company/linkedin_url",
        "company/facebook_url",
        "company/googleplus_url",
        "transition_ipo",
        "transition_acquired",
        "transition_defunct",
        "ratio_influencer",
        "ratio_traction",
        "country_rank",
        "country_rank_change",
        "country_rank_percentile",
        "country_rank_percentile_change",
        "area_rank",
        "area_rank_change",
        "area_rank_percentile",
        "area_rank_percentile_change",
        "world_rank",
        "world_rank_change",
        "world_rank_percentile",
        "world_rank_percentile_change",
        "score",
        "score_change",
        "tracked_from",
        "updated_on",
    ]

    return PreSeriesUtils.dump_opbjects(headers, fields, companies_details)


def dump_person_objects(founders):
    """ This methods generates s CSV-like version of the Company persons, a
    list of rows with columns
    """

    # These are the basic fields of the companies that we want to export
    headers = [
        'Company ID'.encode('utf8'),
        'Company Name'.encode('utf8'),
        'PreSeries ID'.encode('utf8'),
        'Firstname'.encode('utf8'),
        'Lastname'.encode('utf8'),
        'Crunchbase URL'.encode('utf8'),
        'Crunchbase Id'.encode('utf8'),
        'LinkedIn URL'.encode('utf8'),
        'Facebook URL'.encode('utf8'),
        'Twitter URL'.encode('utf8'),
        'Google+ URL'.encode('utf8'),
        'Gender'.encode('utf8'),
        'Birthdate'.encode('utf8'),
        'Updated on'.encode('utf8')]

    fields = [
        "company_id",
        "company_name",
        "person_id",
        "first_name",
        "last_name",
        "crunchbase_url",
        "crunchbase_uuid",
        "linkedin_url",
        "facebook_url",
        "twitter_url",
        "google_plus_url",
        "gender",
        "born",
        "updated",
    ]

    return PreSeriesUtils.dump_opbjects(headers, fields, founders)


def dump_stages_objects(founders):
    """ This methods generates s CSV-like version of the Company stages, a
    list of rows with columns
    """

    # These are the basic fields of the companies that we want to export
    headers = [
        'Company ID'.encode('utf8'),
        'Company Name'.encode('utf8'),
        'Stage Name'.encode('utf8'),
        'Start Date'.encode('utf8'),
        'End Date'.encode('utf8'),
        'First Round Date'.encode('utf8'),
        'Last Round Date'.encode('utf8'),
        'Total Investment'.encode('utf8'),
        'Total Rounds'.encode('utf8')]

    fields = [
        "company_id",
        "company_name",
        "stage",
        "start_date",
        "end_date",
        "first_round_date",
        "last_round_date",
        "investment_amount",
        "total_rounds"
    ]

    return PreSeriesUtils.dump_opbjects(headers, fields, founders)


def dump_rounds_objects(founders):
    """ This methods generates s CSV-like version of the Company objects, a
    list of rows with columns
    """

    # These are the basic fields of the companies that we want to export
    headers = [
        'Company ID'.encode('utf8'),
        'Company Name'.encode('utf8'),
        'Stage Name'.encode('utf8'),
        'Date'.encode('utf8'),
        'Funding Type'.encode('utf8'),
        'Series'.encode('utf8'),
        'Amount'.encode('utf8')]

    fields = [
        "company_id",
        "company_name",
        "stage",
        "date",
        "funding_type",
        "series",
        "amount"
    ]

    return PreSeriesUtils.dump_opbjects(headers, fields, founders)


def dump_competitors_objects(competitors_by_company):
    """ This methods generates s CSV-like version of the competitors of
    of each company
    """

    # These are the basic fields of the competitors that we want to export
    headers = [
        'Company ID'.encode('utf8'),
        'Company Name'.encode('utf8'),
        'Competitor Id'.encode('utf8'),
        'Competitor Name'.encode('utf8'),
        'Competitor Score'.encode('utf8'),
        'Distance Btw Companies'.encode('utf8'),
        'Max Distance in Cluster'.encode('utf8'),
        'Similarity'.encode('utf8')]

    fields = [
        "company_id",
        "company_name",
        "competitor_company_id",
        "competitor_company_name",
        "competitor_company_score",
        "distance",
        "max_distance",
        "similarity"
    ]

    resources = []
    [resources.extend(competitors)
     for competitors in competitors_by_company.values()]

    return PreSeriesUtils.dump_opbjects(headers, fields, resources)


def dump_similar_objects(similar_by_company):
    """ This methods generates s CSV-like version of the similar companies
    of each company
    """

    # These are the basic fields of the similar that we want to export
    headers = [
        'Company ID'.encode('utf8'),
        'Company Name'.encode('utf8'),
        'Similar Company Id'.encode('utf8'),
        'Similar Company Name'.encode('utf8'),
        'Similar Company Score'.encode('utf8'),
        'Distance Btw Companies'.encode('utf8'),
        'Max Distance in Cluster'.encode('utf8'),
        'Similarity'.encode('utf8')]

    fields = [
        "company_id",
        "company_name",
        "similar_company_id",
        "similar_company_name",
        "similar_company_score",
        "distance",
        "max_distance",
        "similarity"
    ]

    resources = []
    [resources.extend(similar) for similar in similar_by_company.values()]

    return PreSeriesUtils.dump_opbjects(headers, fields, resources)


def write_export(file_name, companies, competitors, similar):
    """
    This method is responsible for export the information available in the
    companies structure, competitors list, and similar list, with the data
    requested to PreSeries in the <file_name> Excel file.

    :param file_name: the name of the file to be generated
    :param companies: all the data requested to PreSeries for each company
    :param competitors: the list of competitors per company
    :param similar: the list of similar companies per company
    """

    # Prepare the Excel file
    workbook = Workbook()

    companies_sheet = workbook.add_sheet('Companies')
    company_details_rows = dump_company_objects(companies)
    for index, company in enumerate(company_details_rows):
        [companies_sheet.write(index, value_index, value)
         for value_index, value in enumerate(company)]

    # Export Founders
    founders_sheet = workbook.add_sheet('Founders')
    founders = []
    for company in companies:
        if "founders" in company:
            for person in company["founders"]:
                person["company_id"] = company["company_id"]
                person["company_name"] = company["name"]
                founders.append(person)
    founders_rows = dump_person_objects(founders)
    for index, person in enumerate(founders_rows):
        [founders_sheet.write(index, value_index, value)
         for value_index, value in enumerate(person)]

    # Export Board Members
    board_members_sheet = workbook.add_sheet('Board Members')
    board_members = []
    for company in companies:
        if "board_members" in company:
            for person in company["board_members"]:
                person["company_id"] = company["company_id"]
                person["company_name"] = company["name"]
                board_members.append(person)
    board_members_rows = dump_person_objects(board_members)
    for index, person in enumerate(board_members_rows):
        [board_members_sheet.write(index, value_index, value)
         for value_index, value in enumerate(person)]

    # Export Stages
    stages_sheet = workbook.add_sheet('Stages')
    stages = []
    for company in companies:
        if "stages" in company:
            for stage_name, stage in company["stages"].iteritems():
                stage["company_id"] = company["company_id"]
                stage["company_name"] = company["name"]
                stages.append(stage)
    stages_rows = dump_stages_objects(stages)
    for index, stage in enumerate(stages_rows):
        [stages_sheet.write(index, value_index, value)
         for value_index, value in enumerate(stage)]

    # Export Rounds
    rounds_sheet = workbook.add_sheet('Rounds')
    rounds = []
    for company in companies:
        if "stages" in company:
            for stage_name, stage in company["stages"].iteritems():
                if "rounds" in stage:
                    for round in stage["rounds"]:
                        round["company_id"] = company["company_id"]
                        round["company_name"] = company["name"]
                        round["stage"] = stage_name
                        rounds.append(round)
    rounds_rows = dump_rounds_objects(rounds)
    for index, round in enumerate(rounds_rows):
        [rounds_sheet.write(index, value_index, value)
         for value_index, value in enumerate(round)]

    # Export Competitors
    competitors_sheet = workbook.add_sheet('Competitors')
    competitors_details_rows = dump_competitors_objects(competitors)
    for index, competitor in enumerate(competitors_details_rows):
        [competitors_sheet.write(index, value_index, value)
         for value_index, value in enumerate(competitor)]

    # Export Similar
    similar_sheet = workbook.add_sheet('Similar')
    similar_details_rows = dump_similar_objects(similar)
    for index, similar_record in enumerate(similar_details_rows):
        [similar_sheet.write(index, value_index, value)
         for value_index, value in enumerate(similar_record)]

    # Save the Excel file
    workbook.save(file_name)


def write_to_file(file_name, companies, summary_columns, wb_sheet):
    """
    This method generates a new Excel file with the name <file_name> that will
    contains the data found in PreSeries for each entry in the original excel
    file


    :param file_name: the name of the file to be generated
    :param companies: a list of companies with the basic data found in PreSeries
    :param summary_columns: the columns in the original file that will be
        used in the new file to give more information about the companies.
    :param wb_sheet: the excel sheet of the original file where we will find
        the summary fields of the companies.
    """
    workbook = Workbook()
    companies_sheet = workbook.add_sheet('Companies')

    # Build the header names
    header = ["Original Row", "Company Name", "Domain", "Country"]
    header.extend(summary_columns) \
        if summary_columns and len(summary_columns) > 0 else None
    [companies_sheet.write(0, index, value)
     for index, value in enumerate(header)]

    for index, company_data in enumerate(companies):
        companies_sheet.write(1 + index, 0, company_data["row"])
        companies_sheet.write(
            1 + index, 1, company_data["name"].decode('utf-8', 'ignore')
            if "name" in company_data else "")
        companies_sheet.write(
            1 + index, 2, company_data["country_code"]
            if "country_code" in company_data else "")
        companies_sheet.write(
            1 + index, 3, company_data["domain"]
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

            companies_sheet.write(1 + index, 4 + index2,
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
            description="Export Company Data",
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

        companies_details = get_company_details(known_companies)

        competitors_by_company = get_competitors(known_companies)

        similars_by_company = get_similar(known_companies)

        import json
        with open('companies.json', 'w') as outfile:
            json.dump(companies_details, outfile)
        with open('competitors.json', 'w') as outfile:
            json.dump(competitors_by_company, outfile)
        with open('similar.json', 'w') as outfile:
            json.dump(similars_by_company, outfile)

        write_export("Companies_export.xls", companies_details,
                     competitors_by_company, similars_by_company)

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

    except Exception as ex:
        logging.exception("ERROR processing the task. Exception: [%s]" % ex)
        logging.exception("Stacktrace [%s]" % traceback.format_exc())
        exit(2)


if __name__ == "__main__":
    main()
