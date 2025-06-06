
from lmdb_simple import LmdbDict
from multiprocessing import Pool

TEST_DB_PATH = 'test.db'

test_reader_dict = LmdbDict(TEST_DB_PATH)

def reader_worker_test(key_to_read):
    val_returned = test_reader_dict[key_to_read]
    print(f"{key_to_read=} | {val_returned=}")
    return val_returned


def main():

    test_writer_dict = LmdbDict(TEST_DB_PATH, writer=True)

    dict_to_write = {
        'one': 1,
        2: 'two',
        'three': 3,
        4:'four',
        'five':5,
        6:'six',
    }

    for k, v in dict_to_write.items():
        test_writer_dict[k] = v

    with Pool(2) as p:
        for val_returned in p.imap_unordered(reader_worker_test, list(dict_to_write.keys())):
            print(f"{val_returned=}")

if __name__ == '__main__':
    main()





