import subprocess

from src.loader import load_archives
from src.search import search_by_tag
from src.tag_extraction import extract_tags

MODEL_NAME = "FYN-X-02"  # Replace with your actual Ollama model name


def retrieve_archives(archives, tags, limit=5):
    results = []

    for tag in tags:
        matches = search_by_tag(archives, tag)
        for match in matches:
            if match not in results:
                results.append(match)

        if len(results) >= limit:
            break

    return results[:limit]


def format_archives(entries):
    if not entries:
        return "No relevant archival records were found."

    lines = []
    for entry in entries:
        header = (
            f"- [{entry['type'].upper()} | "
            f"{entry['confidence']} confidence | "
            f"{entry['era']}]"
        )
        lines.append(header)
        lines.append(f"  {entry['content']}")

    return "\n".join(lines)


def build_prompt(user_input, archive_block):
    prompt = (
        "ARCHIVAL CONTEXT (internal records provided to the droid):\n"
        f"{archive_block}\n\n"
        "--------------------\n"
        "CURRENT INTERACTION\n"
        "--------------------\n"
        f"User: {user_input}\n"
        "Droid:"
    )
    return prompt


def run_ollama(prompt):
    process = subprocess.run(
        ["ollama", "run", MODEL_NAME],
        input=prompt,
        text=True,
        encoding="utf-8",
        capture_output=True
    )


    if process.returncode != 0:
        raise RuntimeError(process.stderr)

    return process.stdout


def main():
    archives = load_archives()

    print("FYN-X online. Enter your query.")
    print("Type 'exit' to shut down.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("FYN-X powering down.")
            break

        tags = extract_tags(user_input)
        retrieved = retrieve_archives(archives, tags)
        archive_block = format_archives(retrieved)

        prompt = build_prompt(user_input, archive_block)
        response = run_ollama(prompt)

        print("\nFYN-X:", response.strip(), "\n")


if __name__ == "__main__":
    main()
