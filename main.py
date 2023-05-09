import sys

import requests
import zufallsworte as zufall


def ersetze_umlaute(s):
    special_char_map = {"ä": "ae", "ü": "ue", "ö": "oe", "ß": "ss"}
    return s.translate(str.maketrans(special_char_map))


def zufallswort():
    z_wort = zufall.zufallswoerter(1)
    return ersetze_umlaute(z_wort[0].lower())


def erraten(dev=False):
    if dev:
        print(f"DEBUG: Das Wort ist {wort}")
    versuch = input("Einen Buchstaben eingeben > ").lower()
    if len(versuch) > 1:
        print("Bitte gib nur einen Buchstaben ein!")
        return erraten()
    if versuch in wort and versuch not in erratene_buchstaben and versuch != "":
        return versuch
    return versuch


def platzhalter_aktualisieren(richtiges_wort, liste, print_out):
    if len(liste) == 0:
        wort_platzhalter = "_" * len(wort)
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


if __name__ == "__main__":
    wort = zufallswort()
    platzhalter_aktualisieren(wort, [], False)

    erratene_buchstaben, fertig, versuche, maximale_versuche = [], False, 0, 11
    while not fertig and versuche < maximale_versuche:
        momentaner_stand = platzhalter_aktualisieren(
            wort, erratene_buchstaben, True)
        erratene_buchstaben.append(erraten())
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
            dict.fromkeys(erratene_buchstaben_sortiert))
        print(
            f"Versuchte Buchstaben: {[buchstabe.lower() + '' for buchstabe in erratene_buchstaben_sortiert]}"
        )

    if fertig:
        print(f"Du hast das Wort {wort.capitalize()} erraten!")
        sys.exit()
    else:
        print(
            f"Du hast das Wort nicht erraten\nDas richtige Wort war {wort.capitalize()}"
        )
        sys.exit()
