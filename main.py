import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

def check_for_redirects(response):
    if response.status_code != 200:
        raise requests.HTTPError


def get_book_info(book_id):
    response = requests.get(f'https://tululu.org/b{book_id}/')
    soup = BeautifulSoup(response.text, 'lxml')

    book_name = sanitize_filename(soup.find('h1').text.split('::')[0].strip())
    book_author = sanitize_filename(soup.find('h1').text.split('::')[1].strip())

    return {'book_name': book_name,
            'book_author': book_author}

def download_txt(url, book_id, folder='books/'):
    url = url + str(book_id)
    response = requests.get(url, allow_redirects=False)

    try:
        check_for_redirects(response)
        book_info = get_book_info(book_id)
        file_name = f'{book_id}. {book_info["book_name"]}.txt'

        with open(os.path.join(folder, file_name), 'wb') as file:
            file.write(response.content)
    except requests.HTTPError:
        return False


def downolad_books(url: str, start_id: int, end_id: int, folder: str = 'books/'):
    os.makedirs(folder, exist_ok=True)
    for book_id in range(start_id, end_id + 1):
        download_txt(url, book_id)


if __name__ == '__main__':
    url = 'https://tululu.org/txt.php?id='
    downolad_books(url, 1, 10)

