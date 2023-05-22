from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import re
import os
from environs import Env
import json
from pathvalidate import sanitize_filename
from time import sleep

def check_for_redirects(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(response_page):
    soup = BeautifulSoup(response_page.text, 'lxml')

    book_name, book_author = soup.find('h1').text.split('::')
    book_name = sanitize_filename(book_name.strip())
    book_author = sanitize_filename(book_author.strip())
    book_image_url = soup.find('div', class_='bookimage').find('img')['src']
    book_comments = soup.find_all('div', class_='texts')
    book_genres = soup.find('span', class_='d_book').find_all('a')

    comments = [book_comment.find('span').text for book_comment in book_comments]
    genres = [book_genre.text for book_genre in book_genres]

    return {'book_name': book_name,
            'book_author': book_author,
            'book_image_url': book_image_url,
            'book_comments': comments,
            'book_genres': genres}


def download_txt_book(response, book_name, book_id, books_folder):
    file_name = f'{book_id}. {book_name}.txt'

    with open(os.path.join(books_folder, file_name), 'wb') as file:
        file.write(response.content)


def download_book_image(book_image_url, books_images_folder, url):
    image_name = os.path.basename(book_image_url)

    full_image_url = urljoin(url, book_image_url)

    response = requests.get(full_image_url)
    response.raise_for_status()

    with open(os.path.join(books_images_folder, image_name), 'wb') as file:
        file.write(response.content)


def save_books_file(books_file_name, books):
    with open(books_file_name, 'w') as fp:
        json.dump(books, fp, ensure_ascii=False)


def main():
    url = 'https://tululu.org/'
    category_id = 'l55'
    category_url = urljoin(url, category_id)
    category_page = 1

    books = {}

    env = Env()
    env.read_env()

    books_folder = env('BOOKS_FOLDER')
    books_images_folder = env('BOOKS_IMAGES_FOLDER')
    books_file_name = env('BOOKS_FILE_NAME')

    os.makedirs(books_folder, exist_ok=True)
    os.makedirs(books_images_folder, exist_ok=True)

    while category_page < 3:

        response = requests.get(f'{category_url}/{category_page}')

        soup = BeautifulSoup(response.text, 'lxml')
        on_page_books = soup.find('div', {'id': 'content'}).find_all('table', class_='d_book')

        for book in on_page_books:
            book_id = re.search('\d+', book.find('a')['href'])[0]
            payload = {'id': book_id}
            book_download_url = urljoin(url, 'txt.php')
            book_url = urljoin(url, f'b{book_id}/')

            try:
                response_book = requests.get(book_download_url, params=payload)
                response_book.raise_for_status()

                response_page = requests.get(book_url)
                response_page.raise_for_status()

                check_for_redirects(response_book)
                check_for_redirects(response_page)

                book = parse_book_page(response_page)

                download_txt_book(response_book, book['book_name'], book_id, books_folder)
                download_book_image(book['book_image_url'], books_images_folder, book_url)
                print(book_id)
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
