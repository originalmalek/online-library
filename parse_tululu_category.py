import argparse
import os
import re
import sys
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from environs import Env

from parse_tululu_by_id import parse_book_page, download_txt_book, download_book_image
from parse_tululu_by_id import check_for_redirects, save_books_file


def parse_arguments():
    parser = argparse.ArgumentParser(description='''Программа для скачивания книг и информации
        													о них с сайта https://tululu.org/''')

    parser.add_argument('-s', '--start_page',
                        help='Номер первой cтраницы парсинга',
                        type=int,
                        default=698)
    parser.add_argument('-e', '--end_page',
                        help='Номер последней cтраницы парсинга',
                        type=int,
                        default=701)
    parser.add_argument('-df', '--dest_folder',
                        help='путь к каталогу с результатами парсинга: картинкам, книгам, JSON',
                        type=str,
                        default='/books')
    parser.add_argument('-si', '--skip_imgs',
                        help='Не скачивать картинки',
                        action='store_true')
    parser.add_argument('-st', '--skip_txt',
                        help='Не скачивать книги',
                        action='store_true')
    parser.add_argument('-jn', '--json_name',
                        help='Указать своё имя к *.json файлу с результатами',
                        type=str,
                        default='books.json')
    return parser.parse_args()


def main():
    args = parse_arguments()

    category_page = args.start_page
    end_page = args.end_page
    destination_folder = args.dest_folder
    skip_images = args.skip_imgs
    skip_txt = args.skip_txt
    json_name = args.json_name

    env = Env()
    env.read_env()

    books_folder = os.path.join(destination_folder, env('BOOKS_FOLDER'))
    books_images_folder = os.path.join(destination_folder, 'images')
    books_file_name = os.path.join(destination_folder, json_name)
    category_id = env('CATEGORY_ID')

    os.makedirs(books_folder, exist_ok=True)
    os.makedirs(books_images_folder, exist_ok=True)

    url = 'https://tululu.org/'
    category_url = urljoin(url, f'{category_id}/')

    books = {}

    while category_page <= end_page:
        try:
            response = requests.get(f'{category_url}/{category_page}')
            response.raise_for_status()
            check_for_redirects(response)
        except requests.ConnectionError:
            print('Ошибка соединения, следующая попытка через 60 секунд')
            sleep(60)
            continue
        except requests.HTTPError:
            print(f'Страницы № {category_page} в категории {category_id} не существует')
            save_books_file(books_file_name, books)
            sys.exit(1)

        soup = BeautifulSoup(response.text, 'lxml')

        on_page_books_selector = 'div#content table.d_book'
        on_page_books = soup.select(on_page_books_selector)

        on_page_book = 0
        while on_page_book < len(on_page_books):
            book_id = re.search('\d+', on_page_books[on_page_book].select_one('a')['href'])[0]
            payload = {'id': book_id}
            book_download_url = urljoin(url, 'txt.php')
            book_url = urljoin(url, f'b{book_id}/')
            book_file_name = ""
            try:
                page_response = requests.get(book_url)
                page_response.raise_for_status()
                check_for_redirects(page_response)

                book = parse_book_page(page_response)

                if not skip_txt:
                    book_response = requests.get(book_download_url, params=payload)
                    book_response.raise_for_status()
                    check_for_redirects(book_response)
                    book_file_name = download_txt_book(book_response,
                                                  book['book_name'],
                                                  book_id, books_folder)

                if not skip_images:
                    download_book_image(book['book_image_url'], books_images_folder, book_url)

                books[book_id] = book
                books[book_id]['book_file_name'] = book_file_name

            except requests.ConnectionError:
                print('Ошибка соединения, следующая попытка через 60 секунд')
                sleep(5)
                continue

            except requests.HTTPError:
                print(f'Книги с id {book_id} или описания к ней не существует')

            on_page_book += 1
        category_page += 1
    save_books_file(books_file_name, books)


if __name__ == '__main__':
    main()
