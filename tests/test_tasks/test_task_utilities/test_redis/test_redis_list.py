import pytest
from augur.tasks.init.redis_connection import get_redis_connection
from augur.tasks.util.redis_list import RedisList

list_name = "list"

@pytest.fixture()
def redis_list():

    redis_list = RedisList(list_name)

    yield redis_list

    redis = get_redis_connection()

    redis.flushdb()

def test_redis_list_append(redis_list):

    redis = get_redis_connection()

    string = "Hello world, how are you?"

    string_array = string.split(" ")

    for word in string_array:
        redis_list.append(word)

    for i in range(0, len(string_array)):
    
        assert redis.lindex(redis_list.redis_list_key, i) == string_array[i]

length_data_1 = [1, 2, 3, 4, 5]
length_data_2 = []
@pytest.mark.parametrize("data", [length_data_1, length_data_2])
def test_redis_list_length(redis_list, data):

    # print(f"Data: {data}. Data length: {len(data)}")
    redis = get_redis_connection()

    if data:
        redis.rpush(redis_list.redis_list_key, *data)

    assert redis.llen(redis_list.redis_list_key)  == len(data)


# def test_redis_list_contains(redis_list):

#     insert_values = [i for i in range(2, 10, 2)]

#     redis.rpush(redis_list.redis_list_key, *insert_values)

#     for item in insert_values:
#         assert redis_list.contains(item) == True

#     assert redis_list.contains(5) == False
#     assert redis_list.contains(1000) == False
#     assert redis_list.contains(50) == False


extend_data_1 = [i for i in range(2, 10, 2)]
extend_data_2 = []
@pytest.mark.parametrize("data", [extend_data_1, extend_data_2])
def test_redis_list_extend(redis_list, data):

    redis = get_redis_connection()

    redis_list.extend(data)

    for i in range(0, len(data)):
    
        assert int(redis.lindex(redis_list.redis_list_key, i)) == data[i]        






