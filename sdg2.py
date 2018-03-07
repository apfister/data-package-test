from datapackage import Package, exceptions
from arcgis.gis import GIS
import csv
import getpass

SDG_DATA_FOLDER = 'sdg_data'
GOAL_NUMBER = '2'
OUTPUT_CSV_FILE = 'outputdata_to_publish'
OUTPUT_CSV_FAIL_FILE = 'outputdata_parsing_fails'
SCHEMA_FILE_NAME = 'datapackage.json'
DATA_RESOURCE_NAME = 'data'

# read in the data schema JSON file
package = Package('{0}/{1}/{2}'.format(SDG_DATA_FOLDER, GOAL_NUMBER, SCHEMA_FILE_NAME))

# infer the csv file column data types
# this may not be working correctly
package.infer('**/*.csv')

resource = package.get_resource(DATA_RESOURCE_NAME)

# need to get to the fields object on the schema for the csv headers
resource_descriptor = resource.descriptor
schema = resource_descriptor['schema']

# flatten fields to array for csv headers
fieldnames = [f['name'] for f in schema['fields']]

# not sure if this is needed
resource.infer()

# parse the rows from the `resource` object
rows = []
try:
    rows = resource.read(keyed=True, cast=False)
except exceptions.DataPackageException as exception:
    print (exception)
    if exception.multiple:
        for error in exception.errors:
            print (error)

# re-structure csv fields for arcgis & save to csv file
csv_file = '{0}/{1}/{2}.csv'.format(SDG_DATA_FOLDER, GOAL_NUMBER, OUTPUT_CSV_FILE)

fail_rows = []
with open(csv_file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        # test for value float data types in `Val` column
        # if it's found, write it to good file; if not, stash and write to a fail file
        row_value = row['Val']
        try:
            float_val = float(row_value)
            writer.writerow(row)
        except:
            fail_rows.append(row)
            pass

# write out the fail rows that didn't have a float value in the `Val` column
csv_fail_file = '{0}/{1}/{2}.csv'.format(SDG_DATA_FOLDER, GOAL_NUMBER, OUTPUT_CSV_FAIL_FILE)
with open(csv_fail_file, 'w', newline='') as csvfailfile:
    fail_writer = csv.DictWriter(csvfailfile, fieldnames=fieldnames)
    fail_writer.writeheader()
    fail_writer.writerows(fail_rows)

# add CSV as Item to ArcGIS Online
username = getpass.getpass(prompt='Username:')
password = getpass.getpass()
gis = GIS("https://www.arcgis.com", username, password)

print ('Adding CSV as Item to ArcGIS Online ..')
csv_item = gis.content.add({}, csv_file)

# only publish a hosted table service for now
publish_params = {
    'locationType': 'none',
    'name': 'sdg_{0}_indicator_data'.format(GOAL_NUMBER)
}

print ('Publishing CSV as Feature Service ..')
csv_lyr = csv_item.publish(publish_params)

print ('layer available at :: {0}/home/item.html?id={1}'.format(gis._portal.url, csv_lyr.id))
print ('done!')
