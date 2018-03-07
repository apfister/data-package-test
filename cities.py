from datapackage import Package, exceptions
from arcgis.gis import GIS
import csv
import getpass

# read the schema
package = Package('cities/dataresource.json')

# infer the data types for each column in the data
package.infer('**/*.csv')

# get the 'cities' dataset as a `resource`
resource = package.get_resource('cities')

# don't know if this is needed
resource.infer()

# read out the indivdiual rows to an array
rows = []
try:
    rows = resource.read(keyed=True, cast=True)
except exceptions.DataPackageException as exception:
    print (exception)
    if exception.multiple:
        for error in exception.errors:
            print (error)

# re-structure csv fields for arcgis & save to csv file
csv_file = 'cities/forpublish.csv'
with open(csv_file, 'w', newline='') as csvfile:
    fieldnames = ['city', 'x', 'y']

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        row_loc = row['location']

        if row_loc is not None:
            writer.writerow({'city': row['city'],
            'x': row['location'][1],
            'y': row['location'][0]
            })

# add CSV as Item to ArcGIS Online
username = getpass.getpass(prompt='Username:')
password = getpass.getpass()
gis = GIS("https://www.arcgis.com", username, password)


print ('Adding CSV as Item to ArcGIS Online ..')
csv_item = gis.content.add({}, csv_file)

publish_params = {
    'location_type': 'csv',
    'name': 'cities',
    'latitudeFieldName': 'y',
    'longitudeFieldName': 'x'
}

print ('Publishing CSV as Feature Service ..')
csv_lyr = csv_item.publish(publish_params)

# print (csv_lyr.__dict__)
print ('layer available at :: {0}/home/item.html?id={1}'.format(gis._portal.url, csv_lyr.id))
print ('done!')
