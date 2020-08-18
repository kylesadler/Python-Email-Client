""" contains classes for arbitrary collections of farms storing arbitrary farm fields.
    To create a custom collection, extend Farm Collection.
        override self.save_fields and any other functions if needed
"""

import pymongo
import logging
import traceback

class FarmCollection:

    def __init__(self, db, col):
        self.client = pymongo.MongoClient("localhost", 27017)
        self.farms = self.client[db][col]
        self.name = ' '.join([__name__, db, col])
        self.logger = logging.getLogger(self.name)
        self.save_fields = ('_id',) # tuple of fields saved: override this to save different fields. None to save all fields

    def __del__(self): 
        self.close()

    def close(self):
        self.client.close()

    def save(self, farm):
        if farm not in self:
            self.farms.insert(self.convert(farm))
        else:
            self.logger.debug(self.name + ': duplicate farm')

    def __contains__(self, farm):
        return self.farms.count_documents(self.convert(farm)) > 0

    def count(self):
        return self.farms.count_documents({})
    
    def reset(self):
        self.farms.remove({})

    def convert(self, farm):
        """ convert farm to form that can be saved / queried (based on self.save_fields) """
        output = {}
        fields = self.save_fields or farm
        for key in fields:
            output['__' + key] = farm[key] # ensure all fields are unique
        return output

    def get(self, query=None):
        if query is not None:
            return self.farms.find(self.convert(query))
        else:
            return self.farms.find()

class SeenFarms(FarmCollection):
    def __init__(self, name):
        super().__init__('seen_farms', name)

class ModifiedFarms(FarmCollection):
    """ stores all fields and new_value. 
        farm object must have a 'field' attribute which is the field that is modified
        new_value is the new value of this field
    """

    def __init__(self, name):
        super().__init__('modified_farms', name)
        self.save_fields = None # save all fields

    def save(self, farm, new_fields):
        # store new_value
        to_store = {'farm': farm, 'new_value': new_fields[farm['field']]}
        
        if to_store not in self:
            super().save(to_store)
        else:
            query = self.convert({'farm' : farm})
            assert self.farms.count_documents(query) == 1
            self.farms.update_one(query, { "$set": {'__new_value': new_fields[farm['field']]} })

    def __contains__(self, query):
        # search for farm in DB (ignore new value)
        if 'farm' in query:
            return super().__contains__({'farm' : query['farm']})
        else:
            return super().__contains__({'farm' : query})
