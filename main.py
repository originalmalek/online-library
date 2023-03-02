import requests
import os


def check_for_redirects(response):
    if response.status_code != 200:
        raise requests.HTTPError


def download_book(url, book_id):
    url = url + str(book_id)

    response = requests.get(url, allow_redirects=False)

    try:
        check_for_redirects(response)
        filename = f'book{book_id}.txt'
        with open(f'books/{filename}', 'wb') as file:
            file.write(response.content)
    except requests.HTTPError:
        return False


def downolad_books(url, start_id: int, end_id: int):
    os.makedirs('books', exist_ok=True)
    for book_id in range(start_id, end_id + 1):
        download_book(url, book_id)


if __name__ == '__main__':
    url = 'https://tululu.org/txt.php?id='
    downolad_books(url, 1, 10)

