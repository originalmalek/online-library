import argparse
import os
import re
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from environs import Env

from parse_tululu_by_id import check_for_redirects, parse_book_page, download_txt_book, download_book_image
from parse_tululu_by_id import save_books_file


def main():
    parser = argparse.ArgumentParser(description='''Программа для скачивания книг и информации
    													о них с сайта https://tululu.org/''')

    parser.add_argument('-s', '--start_page',
                        help='Номер первой cтраницы парсинга',
                        type=int,
                        default=1)
    parser.add_argument('-e', '--end_page',
                        help='Номер последней cтраницы парсинга',
                        type=int,
                        default=702)
    parser.add_argument('-df', '--dest_folder',
                        help='путь к каталогу с результатами парсинга: картинкам, книгам, JSON',
                        type=str,
                        default='')
    parser.add_argument('-si', '--skip_imgs',
                        help='Не скачивать картинки',
                        type=int,
                        default=0)
    parser.add_argument('-st', '--skip_txt',
                        help='Не скачивать книги',
                        type=int,
                        default=0)
    parser.add_argument('-jn', '--json_name',
                        help='Указать своё имя к *.json файлу с результатами',
                        type=str,
                        default='books.json')
    args = parser.parse_args()


    start_page = args.start_page
    end_page = args.end_page
    destination_folder = args.dest_folder
    skip_images = args.skip_imgs
    skip_txt = args.skip_txt
    json_name = args.json_name

    url = 'https://tululu.org/'

    books = {}

    env = Env()
    env.read_env()

    books_folder = os.path.join(destination_folder, env('BOOKS_FOLDER'))
    books_images_folder = os.path.join(destination_folder, env('BOOKS_IMAGES_FOLDER'))
    books_file_name = os.path.join(destination_folder, json_name)
    category_id = env('CATEGORY_ID')

    category_url = urljoin(url, category_id)

    response = requests.get(category_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    last_page_selector = 'a.npage'
    last_page = int(soup.select(last_page_selector)[-1].text)

    if end_page == None or end_page > last_page:
        end_page = last_page

    os.makedirs(books_folder, exist_ok=True)
    os.makedirs(books_images_folder, exist_ok=True)

    for category_page in range(start_page, end_page):

        response = requests.get(f'{category_url}/{category_page}')
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        on_page_books_selector = 'div#content table.d_book'
        on_page_books = soup.select(on_page_books_selector)

        for book in on_page_books:
            book_id = re.search('\d+', book.select_one('a')['href'])[0]
            payload = {'id': book_id}
            book_download_url = urljoin(url, 'txt.php')
            book_url = urljoin(url, f'b{book_id}/')

            try:
                response_page = requests.get(book_url)
                response_page.raise_for_status()

                check_for_redirects(response_page)
                book = parse_book_page(response_page)

                if skip_txt == 0:
                    response_book = requests.get(book_download_url, params=payload)
                    response_book.raise_for_status()
                    check_for_redirects(response_book)
                    download_txt_book(response_book, book['book_name'], book_id, books_folder)

                if skip_images == 0:
                    download_book_image(book['book_image_url'], books_images_folder, book_url)
                books[book_id] = book

            except requests.ConnectionError:
                print('Ошибка соединения, следующая попытка через 60 секунд')
                sleep(60)
                continue

            except requests.HTTPError:
                print(f'Книги с id {book_id} или описания к ней не существует')

        category_page += 1

    save_books_file(books_file_name, books)


if __name__ == '__main__':
    main()
