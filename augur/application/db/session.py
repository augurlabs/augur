import time
import random
from sqlalchemy.orm import Session
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError
from sqlalchemy import func

from typing import Optional, List, Union
from psycopg2.errors import DeadlockDetected

# from augur.tasks.util.random_key_auth import RandomKeyAuth
from augur.tasks.util.worker_util import remove_duplicates_by_uniques


def remove_null_characters_from_string(string):

    if string:
        return string.replace("\x00", "\uFFFD")

    return string

def remove_null_characters_from_strings_in_dict(data, fields):

    for field in fields:

        # ensure the field exits in the dict
        try:
            data[field] = remove_null_characters_from_string(data[field])
        except KeyError:
            print(
                f"Error tried to remove null characters from the field: {field}, but it wasn't present in the dict")
            continue

        except AttributeError:
            continue

    return data

def remove_null_characters_from_list_of_dicts(data_list, fields):

    for value in data_list:
        value = remove_null_characters_from_strings_in_dict(value, fields)

    return data_list

class DatabaseSession(Session):

    def __init__(self, logger, engine=None, from_msg=None, **kwargs):
    
        self.logger = logger
        self.engine = engine
        self.session = self
        self.engine_created = False

        if self.engine is None:
            self.logger.debug("Passing engine will be required soon")
            from augur.application.db.engine import DatabaseEngine

            self.engine_created = True

            self.engine = DatabaseEngine().engine
            if from_msg:
                logger.debug(f"ENGINE CREATE: {from_msg}")
            else:
                logger.debug(f"ENGINE CREATE")

        super().__init__(self.engine, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):

        if self.engine_created:
            self.engine.dispose()
        
        self.close()

    def __del__(self):
        self.close()
    
    def execute_sql(self, sql_text):

        with self.engine.begin() as connection:

            return_data = connection.execute(sql_text)  

        return return_data

    def fetchall_data_from_sql_text(self,sql_text):

        with self.engine.begin() as connection:

            result = connection.execute(sql_text)
        return [dict(row) for row in result.mappings()]

    def insert_data(self, data_input: Union[List[dict], dict], table, natural_keys: List[str], return_columns: Optional[List[str]] = None, string_fields: Optional[List[str]] = None, on_conflict_update:bool = True) -> Optional[List[dict]]:

        if isinstance(data_input, list) is False:
            
            # if a dict is passed to data then 
            # convert it to a list with one value
            if isinstance(data_input, dict) is True:
                data = [data_input]
            
            else:
                self.logger.info("Data must be a list or a dict")
                return None
        else:
            data = list(data_input)

        if len(data) == 0:
            # self.logger.info("Gave no data to insert, returning...")
            return None

        if isinstance(data[0], dict) is False: 
            self.logger.info("Must be list of dicts")
            return None

        # remove any duplicate data 
        # this only counts something as a duplicate if every field is the same
        data = remove_duplicates_by_uniques(data, natural_keys)

        # remove null data from string fields
        if string_fields and isinstance(string_fields, list):
            data = remove_null_characters_from_list_of_dicts(data, string_fields)

        # creates list of arguments to tell sqlalchemy what columns to return after the data is inserted
        returning_args = []
        if return_columns:
            for column in return_columns:
                argument = getattr(table, column)
                returning_args.append(argument)

        # creates insert on table
        # that returns cols specificed in returning_args
        # and inserts the data specified in data
        # NOTE: if return_columns does not have an values this still works
        stmnt = postgresql.insert(table).returning(*returning_args).values(data)


        if on_conflict_update:

            # create a dict that the on_conflict_do_update method requires to be able to map updates whenever there is a conflict. See sqlalchemy docs for more explanation and examples: https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#updating-using-the-excluded-insert-values
            setDict = {}
            base_table = getattr(table, "__table__", table)
            for key in data[0].keys():
                existing_col = getattr(base_table.c, key)
                setDict[key] = func.coalesce(getattr(stmnt.excluded, key), existing_col)
                
            stmnt = stmnt.on_conflict_do_update(
                #This might need to change
                index_elements=natural_keys,
                
                #Columns to be updated
                set_ = setDict
            )

        else:
            stmnt = stmnt.on_conflict_do_nothing(
                index_elements=natural_keys
            )


        # print(str(stmnt.compile(dialect=postgresql.dialect())))
        attempts = 0
        # creates list from 1 to 10
        sleep_time_list = list(range(10,66))
        deadlock_detected = False


        # if there is no data to return then it executes the insert then returns nothing
        if not return_columns:
            # TODO: duplicate-looking code alert
            while attempts < 10:
                try:
                    #begin keyword is needed for sqlalchemy 2.x
                    #this is because autocommit support was removed in 2.0
                    with self.engine.begin() as connection:
                        connection.execute(stmnt)
                        break
                except OperationalError as e:
                    # print(str(e).split("Process")[1].split(";")[0])
                    if isinstance(e.orig, DeadlockDetected):
                        deadlock_detected = True
                        sleep_time = random.choice(sleep_time_list)
                        self.logger.debug(f"Deadlock detected on {table.__table__} table...trying again in {round(sleep_time)} seconds: transaction size: {len(data)}")
                        time.sleep(sleep_time)

                        attempts += 1
                        continue
                    
                    raise e

                except Exception as e:
                    #self.logger.info(e)
                    if len(data) == 1:
                        raise e
                   
                    time.sleep(3)
                    first_half = data[:len(data)//2]
                    second_half = data[len(data)//2:]

                    self.insert_data(first_half, table, natural_keys, return_columns, string_fields, on_conflict_update)
                    self.insert_data(second_half,table, natural_keys, return_columns, string_fields, on_conflict_update)

            else:
                self.logger.error("Unable to insert data in 10 attempts")
                return None

            if deadlock_detected is True:
                self.logger.error("Made it through even though Deadlock was detected")

            # success  
            return None
        

        # othewise it gets the requested return columns and returns them as a list of dicts
        while attempts < 10:
            try:
                with self.engine.begin() as connection:
                    return_data_tuples = connection.execute(stmnt)
                    break
            except OperationalError as e:
                if isinstance(e.orig, DeadlockDetected):
                    sleep_time = random.choice(sleep_time_list)
                    self.logger.debug(f"Deadlock detected on {table.__table__} table...trying again in {round(sleep_time)} seconds: transaction size: {len(data)}")
                    time.sleep(sleep_time)

                    attempts += 1
                    continue   

                raise e

            except Exception as e:
                if len(data) == 1:
                    raise e
                
                time.sleep(3)
                first_half = data[:len(data)//2]
                second_half = data[len(data)//2:]

                self.insert_data(first_half, table, natural_keys, return_columns, string_fields, on_conflict_update)
                self.insert_data(second_half, table, natural_keys, return_columns, string_fields, on_conflict_update)

        else:
            self.logger.error("Unable to insert and return data in 10 attempts")
            return None

        if deadlock_detected is True:
            self.logger.error("Made it through even though Deadlock was detected")

        return_data = [dict(row) for row in return_data_tuples.mappings()]
        
        #no longer working in sqlalchemy 2.x
        #for data_tuple in return_data_tuples:
        #    return_data.append(dict(data_tuple))

        # using on confilict do nothing does not return the 
        # present values so this does gets the return values
        if not on_conflict_update:

            conditions = []
            for column in natural_keys:

                column_values = [value[column] for value in data]

                column = getattr(table, column)

                conditions.append(column.in_(tuple(column_values)))

            result = (
                self.query(table).filter(*conditions).all()
            )

            for row in result:

                return_dict = {}
                for field in return_columns:

                    return_dict[field] = getattr(row, field)

                return_data.append(return_dict)


        return return_data
