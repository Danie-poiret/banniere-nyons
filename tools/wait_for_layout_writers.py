"""Wait for shared HTML writers; defer normally when they are still working."""

import json
import os
import subprocess
import time


WRITERS = {
    "Appliquer la mise a jour VivreAnyons",
    "Actualiser uniquement l’accueil de Vivre à Nyons",
    "Actualiser uniquement les cartes du portail immobilier",
    "Compléter le SEO après génération du site",
    "Harmoniser les liens des pages avec le slash final",
    "Autour de Nyons — préparation et catalogue",
    "Actualiser les horaires de bus à Nyons",
    "Actualiser uniquement les manifestations de Nyons",
    "Actualiser et vérifier Nyons en direct",
    "Restaurer les photos originales des fiches",
    "Importer photos Pont Roman",
    "Actualiser et vérifier la météo de Nyons",
}


def active_writers(repository):
    result = subprocess.run(
        ["gh", "api", f"repos/{repository}/actions/runs?branch=main&per_page=100"],
        check=True, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    runs = json.loads(result.stdout)["workflow_runs"]
    return [run["name"] for run in runs
            if run["name"] in WRITERS and run["status"] != "completed"]


def wait_for_writers(repository, timeout_seconds=300, poll_seconds=5):
    deadline = time.monotonic() + timeout_seconds
    quiet = 0
    while True:
        active = active_writers(repository)
        quiet = 0 if active else quiet + 1
        if quiet >= 2:
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(poll_seconds, remaining))


def main():
    # API/authentication errors deliberately propagate: they are real failures.
    ready = wait_for_writers(os.environ["GITHUB_REPOSITORY"])
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"ready={str(ready).lower()}\n")
    if not ready:
        message = (
            "Un générateur est encore actif ; préparation reportée sans modifier "
            "les pages. Sa fin déclenchera une nouvelle préparation."
        )
        print(f"::notice::{message}")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
                summary.write(message + "\n")


if __name__ == "__main__":
    main()
