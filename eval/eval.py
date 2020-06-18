# coding: utf8

from argparse import ArgumentParser

def main():

    parser = ArgumentParser(
        description='Split data into train/dev/test sets')
    parser.add_argument(
        '-test-file', '--input-dir', help='Path to the directory containing the data files')
    parser.add_argument(
        '-output-dir', '--output-dir', help='Path to the output directory to save the datasets')
    parser.add_argument(
        '-data-name', '--data-name', help='Name of the data to save')
    parser.add_argument(
        '--dev-size', default=10, type=int, help='Size of the development set as percentage')
    parser.add_argument(
        '--test-size', default=10, type=int, help='Size of the testing set as percentage')
    args = parser.parse_args()

    


if __name__ == "__main__":
    main()