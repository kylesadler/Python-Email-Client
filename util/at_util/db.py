import pymongo
import logging
import getpass
from .tunnels import MongoDBTunnel

logger = logging.getLogger(__name__)


def get_db(local=False):
    if local:
        return MongoDBTunnel(None, None, None, None, None, local=True)
    else:
        return MongoDBTunnel(*get_auth()[:5])


def get_auth():
    return getpass.getpass('Authentication: ').split(',')


def test_permissions(ip, ssh_user, ssh_pkey, auths, collections):
    """ Tests permissions of database users using the current server's login information

        ip = "x.x.x.x"
        ssh_user = "x"
        ssh_pkey = "/path/to/pkey"
        auths = [                           # list of each user's login info
            ("user1","pass1"),              # in (username, password) tuples
            ("user2","pass2"),
            ("userN","passN"),
        ]
        collections = ('col1','col2','colN') # collection names of collections to test
    """

    for auth in auths:
        db = MongoDBTunnel(ip, ssh_user, ssh_pkey, auth[0], auth[1])
        print('testing '+auth[0])
        
        for col in collections:
            print("\t"+col,end=": ")
            try:
                count = db[col].count_documents({})
                print(count)
            except:
                print("error")
            
        db.close()


def print_update(count, total, col=''):
    """ prints an update to the screen. col is collection name """
    if len(str(col)) > 0: col = f'{col}: '
    print(f'\r{col}{count} / {total}', end=' '*20)
    if count == total: print()


def get_id_dict(farm):
    # return dict with 'important' fields. used to check for duplicates
    output = {}
    for key in ('price', 'title', 'acres', 'description'):
        if key in farm:
            output[key] = farm[key]
    return output


def copy_collection(source, destination, overwrite=False, add=False, prod_col=None):
    """
        copies source to destination
        source and destination are both MongoDBTunnel collections with open connections
        @input overwrite overwrite the destination collection
        @input add add the source collection to the destination collection without clearing the contents
        @input prod_col (production collection) MongoDBTunnel collection to cross reference for removing duplicates
    """
    # title = source.db_name + ' to ' + destination.db_name # for printing updates to the screen
    if not add and destination.count_documents({}) > 0:
        assert overwrite, 'destination collection is full: '+str(destination)
        destination.delete_many({}) # clear destination
        logger.warning('overwriting collection ' + str(destination))
        
    seen_farms = {}
    total = source.count_documents({})
    count = 0
    bulk = destination.initialize_unordered_bulk_op()

    for farm in source.find():
        count += 1
        
        id_dict = get_id_dict(farm)
        id_string = str(id_dict)

        if id_string not in seen_farms and (prod_col is None or prod_col.count_documents(id_dict) == 0):
            bulk.insert(farm)
            seen_farms[id_string] = 1
        
        if count % 500 == 0:
            try:
                bulk.execute()
                bulk = destination.initialize_ordered_bulk_op()
            except pymongo.errors.InvalidOperation: # no farms to copy
                pass
            
            print_update(count, total)

            
    if count % 500 != 0:
        try:
            bulk.execute()
        except pymongo.errors.InvalidOperation: # no farms to copy
            pass
    
    print_update(count, total)
    print()


def prompt_copy_collection(source, destination, add=False, prod_col=None):
    """ prompts the user to force overwrite when copying a collection """

    print(f'\nSource:\n{source}\n\nDestination:\n{destination}\n')
    if prod_col is not None:
        print(f'Duplicate Filter:\n{prod_col}\n')

    try:
        copy_collection(source, destination, add=add, prod_col=prod_col)
        print('done')
    except AssertionError:
        yes_no = input('Would you like to force this operation?\n' \
                        + 'WARNING this will overwrite the data in the destination database\n')

        if yes_no.lower() in ('yes', 'y'):
            print('forcing overwrite...')
            copy_collection(source, destination, overwrite=True, add=add, prod_col=prod_col)
            print('done')
        else:
            print('exiting...')

def field_exists(field, farm):
    """ returns True if farm[field] exists and isn't None
        farm is a Farm object
        field is a string
    """
    return field in farm and farm[field] is not None

def all_fields_exist(field_list, farm):
    """ returns True if all fields exist and have values on farm object
        farm is a Farm object
        field_list is list of strings
    """
    for field in field_list:
        if not field_exists(field, farm):
            return False

    return True
