import os
import sys
import tkinter as tk
import winreg as reg
from tkinter import simpledialog

import sentry_sdk
import zufallsworte as zufall


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
)


def ersetze_umlaute(s):
    with sentry_sdk.start_transaction(op="replace_umlauts", name="Umlaute ersetzen"):
        special_char_map = {"ä": "ae", "ü": "ue", "ö": "oe", "ß": "ss"}
        return s.translate(str.maketrans(special_char_map))


def zufallswort():
    with sentry_sdk.start_transaction(op="random_word", name="Zufallswort generieren"):
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
            return erraten()
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
            if value[0] is not None:
                os.environ["HANGMAN_EMAIL"] = value[0]
                sentry_sdk.set_user({"email": value[0]})
                print("Erfolgreich eingeloggt!")
                sentry_sdk.add_breadcrumb(
                    category="info", message="User logged in")
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
            sentry_sdk.add_breadcrumb(
                category="error", message="Invalid email")
            log_in()
        else:
            sentry_sdk.set_user({"email": USER_INP})
            # set the registry key where info will be stored

            # create a key at HKEY_CURRENT_USER\Software\Hangman
            key = reg.CreateKey(reg.HKEY_CURRENT_USER, "Software\\Hangman")
            # set the value of the key to the email address
            reg.SetValueEx(key, "email", 0, reg.REG_SZ, USER_INP)
            # close the key
            reg.CloseKey(key)
            # set the environment variable
            os.environ["HANGMAN_EMAIL"] = USER_INP

            # check if the key was created
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER, "Software\\Hangman", 0, reg.KEY_READ
            )
            value = reg.QueryValueEx(key, "email")
            if value[0] == USER_INP:
                print("Erfolgreich eingeloggt!")
                sentry_sdk.add_breadcrumb(
                    category="info", message="User logged in")
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
            exit()


def main():
    with sentry_sdk.start_transaction(op="main", name="main"):
        # is the OS Windows? Then log in
        if os.name == "nt":
            log_in()

        wort = zufallswort()
        sentry_sdk.add_breadcrumb(
            category="info", message=f"Word chosen: {wort}")
        platzhalter_aktualisieren(wort, [], False)

        erratene_buchstaben, fertig, versuche, maximale_versuche = [], False, 0, 11
        while not fertig and versuche < maximale_versuche:
            momentaner_stand = platzhalter_aktualisieren(
                wort, erratene_buchstaben, True
            )
            erratene_buchstaben.append(erraten(wort, erratene_buchstaben))
            neuer_stand = platzhalter_aktualisieren(
                wort, erratene_buchstaben, False)
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
            sentry_sdk.add_breadcrumb(
                category="info", message=f"Word guessed: {wort}")
            erneut_spielen()
        else:
            print(
                f"Du hast das Wort nicht erraten\nDas richtige Wort war {wort.capitalize()}"
            )
            sentry_sdk.add_breadcrumb(
                category="info", message=f"Word not guessed: {wort}"
            )
            erneut_spielen()


if __name__ == "__main__":
    main()
