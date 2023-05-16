import json
import os
import random
import sys
import tkinter as tk
import winreg as reg
from tkinter import simpledialog

import requests
import sentry_sdk
import zufallsworte as zufall

globals()["version"] = "stable-09.1"


def before_send(event, hint):
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, (KeyboardInterrupt, SystemExit)):
            print("Programm wurde beendet!")
            return None
    return event


sentry_sdk.init(
    dsn="https://7c71cffadff9423a983843ddd3fe96a3@o1363527.ingest.sentry.io/4505154639364096",
    traces_sample_rate=1.0,
    before_send=before_send,
    profiles_sample_rate=1.0,
    server_name="wortraetsel-frontend",
    release=globals()["version"],
)


def ersetze_umlaute(s):
    with sentry_sdk.start_transaction(op="replace_umlauts", name="Umlaute ersetzen"):
        special_char_map = {"ä": "ae", "ü": "ue", "ö": "oe", "ß": "ss"}
        return s.translate(str.maketrans(special_char_map))


def zufallswort():
    with sentry_sdk.start_transaction(op="random_word", name="Zufallswort generieren"):
        if not globals().get("language"):
            language = ""
        else:
            language = globals()["language"]
        while language != "de" and language != "fi":
            language = input("Welche Sprache? (de/fi) > ").lower()
        globals()["language"] = language

        if language == "fi":
            finish_words_url = "https://raw.githubusercontent.com/hugovk/everyfinnishword/master/kaikkisanat.txt"
            r = requests.get(finish_words_url)
            words = r.text.split("\n")
            words_list = [word for word in words if len(word) > 3]
            return ersetze_umlaute(random.choice(words_list).lower())
        else:
            z_wort = zufall.zufallswoerter(1)
            return ersetze_umlaute(z_wort[0].lower())


def erraten(wort, erratene_buchstaben, dev=False):
    with sentry_sdk.start_transaction(op="guess", name="Buchstaben erraten"):
        if dev:
            print(f"DEBUG: Das Wort ist {wort}")

        versuch = input("Einen Buchstaben eingeben > ").lower()
        if len(versuch) > 1:
            print("Bitte gib nur einen Buchstaben ein!")
            sentry_sdk.add_breadcrumb(
                category="error", message="More than one letter entered: " + versuch
            )
            return erraten(wort, erratene_buchstaben)
        if versuch in wort and versuch not in erratene_buchstaben and versuch != "":
            return versuch
        return versuch


def platzhalter_aktualisieren(richtiges_wort, liste, print_out):
    with sentry_sdk.start_transaction(
            op="update_placeholder", name="Platzhalter aktualisieren"
    ):
        if len(liste) == 0:
            wort_platzhalter = "_" * len(richtiges_wort)
            if print_out:
                print(wort_platzhalter)
                return wort_platzhalter
        else:
            aktualisiert = [
                buchstabe if buchstabe in liste else "_" for buchstabe in richtiges_wort
            ]
            if print_out:
                print("".join(aktualisiert))
            return "".join(aktualisiert)


def hangman(num_guesses):
    with sentry_sdk.start_transaction(op="draw_hangman", name="Hangman zeichnen"):
        stages = [  # The stages of the hangman ASCII art
            """
               --------
               |      |
               |      O
               |     \\|/
               |      |
               |     / \\
               -
            """,
            """
               --------
               |      |
               |      O
               |     \\|/
               |      |
               |     / 
               -
            """,
            """
               --------
               |      |
               |      O
               |     \\|/
               |      |
               |      
               -
            """,
            """
               --------
               |      |
               |      O
               |     \\|
               |      |
               |     
               -
            """,
            """
               --------
               |      |
               |      O
               |      |
               |      |
               |     
               -
            """,
            """
               --------
               |      |
               |      O
               |    
               |      
               |     
               -
            """,
            """
               --------
               |      |
               |      
               |    
               |      
               |     
               -
            """,
            """
               --------
               |      
               |      
               |    
               |      
               |     
               -
            """,
            """
    
               |      
               |      
               |    
               |      
               |     
               -
            """,
            """
    
    
               |    
               |      
               |     
               -
            """,
            """
    
    
    
               |    
               |     
               -
            """,
            """
    
    
    
    
               |     
               -
            """,
            """
    
    
    
    
    
               -
            """,
        ]

        return stages[num_guesses - 1] if num_guesses <= 12 else None


def log_in():
    with sentry_sdk.start_transaction(op="log_in", name="Anmeldung"):
        try:
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER, "Software\\Hangman", 0, reg.KEY_READ
            )
            value = reg.QueryValueEx(key, "email")
            value2 = reg.QueryValueEx(key, "secret")
            if value[0] is not None and value2[0] is not None:
                os.environ["HANGMAN_EMAIL"] = value[0]
                sentry_sdk.set_user({"email": value[0], "id": value2[0]})
                os.environ["HANGMAN_SECRET"] = value2[0]
                print("Erfolgreich eingeloggt!")
                sentry_sdk.add_breadcrumb(category="info", message="User logged in")
                return
        except FileNotFoundError:
            pass

        # use tkinter window to ask for email-address

        ROOT = tk.Tk()
        ROOT.withdraw()
        # the input dialog
        USER_INP = simpledialog.askstring(
            title="Hangman",
            prompt="Bitte gib deine Email-Adresse ein, um deine Punkte zu speichern. Deine "
                   "Email-Adresse wird nicht an Dritte weitergegeben.",
        )

        if "@" not in USER_INP or "." not in USER_INP or USER_INP is None:
            print("Bitte gib eine gültige Email-Adresse ein!")
            sentry_sdk.add_breadcrumb(category="error", message="Invalid email")
            log_in()
        else:
            sentry_sdk.set_user({"email": USER_INP})
            # set the registry key where info will be stored

            api = "https://wortraetsel-api.onrender.com/addUser"
            template = json.dumps({"email": USER_INP})
            headers = {"Content-Type": "application/json"}
            response = requests.post(api, data=template, headers=headers)
            # if we parse the response as json, we get a key called "id" which is the secret
            # key for the user
            secret = response.json()["id"]

            # create a key at HKEY_CURRENT_USER\Software\Hangman
            key = reg.CreateKey(reg.HKEY_CURRENT_USER, "Software\\Hangman")
            # set the value of the key to the email address
            reg.SetValueEx(key, "email", 0, reg.REG_SZ, USER_INP)
            # set the value of the key to the secret
            reg.SetValueEx(key, "secret", 0, reg.REG_SZ, secret)

            # close the key
            reg.CloseKey(key)
            # set the environment variable
            os.environ["HANGMAN_EMAIL"] = USER_INP
            os.environ["HANGMAN_SECRET"] = secret

            sentry_sdk.set_user({"email": USER_INP, "id": secret})

            # check if the key was created
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER, "Software\\Hangman", 0, reg.KEY_READ
            )
            value = reg.QueryValueEx(key, "email")
            value2 = reg.QueryValueEx(key, "secret")
            if value[0] == USER_INP and value2[0] == secret:
                print("Erfolgreich eingeloggt!")
                sentry_sdk.add_breadcrumb(category="info", message="User logged in")
            else:
                print("Fehler beim Einloggen!")
                sentry_sdk.add_breadcrumb(
                    category="error", message="User not logged in"
                )
                log_in()


def erneut_spielen():
    with sentry_sdk.start_transaction(op="replay_console", name="erneut spielen"):
        print("Tippe 'j' in die Konsole, um erneut zu spielen.")
        sentry_sdk.add_breadcrumb(category="info", message="Play again?")
        if input().lower().startswith("j") or input().lower().startswith("y"):
            sentry_sdk.add_breadcrumb(
                category="info", message="User wants to play again"
            )
            main()
        else:
            sentry_sdk.add_breadcrumb(
                category="info", message="User does not want to play again"
            )
            print("Auf Wiedersehen!")
            sentry_sdk.add_breadcrumb(category="info", message="Game ended")
            sys.exit()


def haeufigkeit(buchstabe) -> float:
    letter_frequencies = [
        ("E", 17.40),
        ("N", 9.78),
        ("I", 7.55),
        ("S", 7.27),
        ("R", 7.00),
        ("A", 6.51),
        ("T", 6.15),
        ("D", 5.08),
        ("H", 4.76),
        ("U", 4.35),
        ("L", 3.44),
        ("C", 3.06),
        ("G", 3.01),
        ("M", 2.53),
        ("O", 2.51),
        ("B", 1.89),
        ("W", 1.89),
        ("F", 1.66),
        ("K", 1.21),
        ("Z", 1.13),
        ("P", 0.79),
        ("V", 0.67),
        ("SS", 0.31),  # two-letter alternative for "ß"
        ("J", 0.27),
        ("Y", 0.04),
        ("X", 0.03),
        ("Q", 0.02),
    ]

    for letter, frequency in letter_frequencies:
        if letter == buchstabe.upper():
            return frequency
    return 0


def getRanking(user_secret) -> int:
    # Wir holen uns die Liste aller User
    api = "https://wortraetsel-api.onrender.com/getAllUsers"
    response = requests.get(api)
    users = response.json()
    # Die response enthält sieht so aus:
    # [
    #     {
    #         "userId": "secret",
    #         "score": 700
    #     }
    # ]
    # Wir sortieren die Liste nach dem Score
    users.sort(key=lambda x: x["score"], reverse=True)
    # Wir suchen den User mit dem übergebenen Secret
    for index, user in enumerate(users):
        if user["userId"] == user_secret:
            return index + 1
    return -1


def punkte_system(versuche, wort, erratene_buchstaben, geloest):
    print("Diese Runde ist vorbei!")
    benutzer_secret = os.environ["HANGMAN_SECRET"]
    if benutzer_secret and benutzer_secret != "":
        if geloest:
            # calculate points
            points = 1000 - (versuche * 100)
            # get the user's secret
            secret = os.environ["HANGMAN_SECRET"]
            # get the current points
            api = "https://wortraetsel-api.onrender.com/getUser/" + secret
            response = requests.get(api)
            current_points = response.json()["score"]
            # add the points
            api = "https://wortraetsel-api.onrender.com/updatescore"
            template = json.dumps({"userId": secret, "score": current_points + points})
            headers = {"Content-Type": "application/json"}
            response = requests.post(api, data=template, headers=headers)
            # get the new points
            api = "https://wortraetsel-api.onrender.com/getUser/" + secret
            response = requests.get(api)
            new_points = response.json()["score"]
            # print the points
            print(f"Du hast Jetzt {new_points} Punkte! (+{points})")
            sentry_sdk.add_breadcrumb(
                category="info", message=f"User got {points} points"
            )
            print(f"Damit bist du auf Platz {getRanking(secret)}!")
            sentry_sdk.add_breadcrumb(
                category="info", message=f"User is now on rank {getRanking(secret)}"
            )

        else:  # if the user lost
            # get the user's secret
            secret = os.environ["HANGMAN_SECRET"]
            # get the current points
            api = "https://wortraetsel-api.onrender.com/getUser/" + secret
            response = requests.get(api)
            current_points = response.json()["score"]
            # remove the points based on the length of the word and how many letters were guessed.
            # we get the percentage of not guessed letters. This percentage then is removed from the points.
            percentage = 0
            for letter in wort:
                if letter not in erratene_buchstaben:
                    percentage += 1
            percentage = percentage / len(wort) * 100
            points = int(percentage)

            points = points * -1
            if current_points + points < 0:
                current_points = 0
                points = 0
            # add the points to the user's score
            api = "https://wortraetsel-api.onrender.com/updatescore"
            template = json.dumps({"userId": secret, "score": current_points + points})
            headers = {"Content-Type": "application/json"}
            requests.post(api, data=template, headers=headers)
            print(
                f"Du hast {points} Punkte verloren!, du hast jetzt {current_points + points} Punkte"
            )
            sentry_sdk.add_breadcrumb(
                category="info", message=f"User lost {points} points"
            )
            print(f"Damit bist du auf Platz {getRanking(secret)}!")
            sentry_sdk.add_breadcrumb(
                category="info", message=f"User is now on rank {getRanking(secret)}"
            )

    else:
        sentry_sdk.add_breadcrumb(category="info", message="No secret found")
        print(
            "Cloud-Variable HANGMAN_SECRET nicht gefunden. Punkte werden nicht gespeichert."
        )


def main():
    with sentry_sdk.start_transaction(op="main", name="main"):
        # is the OS Windows? Then log in
        if os.name == "nt":
            log_in()

        wort = zufallswort()
        sentry_sdk.add_breadcrumb(category="info", message=f"Word chosen: {wort}")
        platzhalter_aktualisieren(wort, [], False)

        erratene_buchstaben, fertig, versuche, maximale_versuche = [], False, 0, 11
        while not fertig and versuche < maximale_versuche:
            momentaner_stand = platzhalter_aktualisieren(
                wort, erratene_buchstaben, True
            )
            erratene_buchstaben.append(erraten(wort, erratene_buchstaben))
            neuer_stand = platzhalter_aktualisieren(wort, erratene_buchstaben, False)
            fertig = "_" not in neuer_stand
            if not fertig:
                versuche += neuer_stand == momentaner_stand
                print(hangman(maximale_versuche - versuche))
            print(f"Du hast noch {maximale_versuche - versuche} Versuche")
            erratene_buchstaben_sortiert = sorted(erratene_buchstaben)
            # Alle kleinschreiben
            erratene_buchstaben_sortiert = [
                buchstabe.lower() for buchstabe in erratene_buchstaben_sortiert
            ]
            # Doppelte entfernen
            erratene_buchstaben_sortiert = list(
                dict.fromkeys(erratene_buchstaben_sortiert)
            )
            print(
                f"Versuchte Buchstaben: {[buchstabe.lower() + '' for buchstabe in erratene_buchstaben_sortiert]}"
            )

        if fertig:
            print(f"Du hast das Wort {wort.capitalize()} erraten!")
            sentry_sdk.add_breadcrumb(category="info", message=f"Word guessed: {wort}")
            punkte_system(versuche, wort, erratene_buchstaben, True)
            erneut_spielen()
        else:
            print(
                f"Du hast das Wort nicht erraten\nDas richtige Wort war {wort.capitalize()}"
            )
            sentry_sdk.add_breadcrumb(
                category="info", message=f"Word not guessed: {wort}"
            )
            punkte_system(versuche, wort, erratene_buchstaben, False)
            erneut_spielen()


def update_check():
    release_url = (
        "https://api.github.com/repos/Spotlightforbugs/Wortraetsel/releases/latest"
    )
    with sentry_sdk.start_transaction(op="update_check", name="Update check"):
        try:
            response = requests.get(release_url)
            response.raise_for_status()
            release = response.json()
            if release["tag_name"] != globals()["version"]:
                print(
                    f"Es gibt eine neue Version von Hangman ({release['tag_name']})\nDu hast Version {globals()['version']}"
                )
                print(
                    "Lade die neue Version herunter unter " + release["html_url"] + "\n"
                )
                sentry_sdk.add_breadcrumb(category="info", message="Update available")
        except requests.exceptions.RequestException as e:
            print("Fehler beim Update-Check")
            sentry_sdk.add_breadcrumb(category="error", message="Update check failed")
            sentry_sdk.capture_exception(e)


if __name__ == "__main__":
    print("Nach Updates suchen...")
    update_check()
    print("Starte Hangman...")
    main()
