from loader import load_archives
from search import search_by_tag

def main():
    archives = load_archives()
    results = search_by_tag(archives, "example")

    for entry in results:
        print(f"[{entry['id']}] {entry['content']}")

if __name__ == "__main__":
    main()
