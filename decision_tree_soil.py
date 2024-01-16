"""


# Soil Type Decision Tree

- Is it primarily composed of peat?
  - Yes
    - Is it mainly lowland marsh?
      - Yes
        - Is it related to highland marsh?
          - Yes
            - 79
          - No
            - Contains mineral deposits?
              - Yes
                - Contains carbonate?
                  - Yes
                    - 67
                  - No
                    - 78
              - No
                - 78a
      - No
        - Contains mineral deposits?
          - Yes
            - 80a, 80b
          - No
            - Related to alpine substrates?
              - Yes
                - 850
              - No
                - 77
  - No
    - Is it primarily gley?
      - Yes
        - Contains mineral deposits?
          - Yes
            - Related to valley sediments?
              - Yes
                - Contains carbonate?
                  - Yes
                    - 64c, 62c
                  - No
                    - Is it primarily clay or silt?
                      - Yes
                        - 73c
                      - No
                        - Is it more loamy?
                          - Yes
                            - 74
                          - No
                            - 75
              - No
                - Contains carbonate?
                  - Yes
                    - 66b
                  - No
                    - 65c
          - No
            - Related to alpine substrates?
              - Yes
                - 75c
              - No
                - Related to gravel?
                  - Yes
                    - Rich in humus?
                      - Yes
                        - Mainly silt to clay?
                          - Yes
                            - 73f
                          - No
                            - 72f
                      - No
                        - Mainly sand?
                          - Yes
                            - 72c
                          - No
                            - Granite or gneiss composition?
                              - Yes
                                - 61a
                              - No
                                - Other
                  - No
                    - Other
      - No
        - Other


"""
from gpt_api_singel import change_statement
soil_types = {
    "78a": "Fast ausschließlich Niedermoor und Übergangsmoor aus Torf über kristallinen Substraten mit weitem Bodenartenspektrum",
    "80a": "Fast ausschließlich (flacher) Gley über Niedermoor aus (flachen) mineralischen Ablagerungen mit weitem Bodenartenspektrum über Torf, vergesellschaftet mit (Kalk)Erdniedermoor",
    "80b": "Überwiegend (Gley-)Rendzina und kalkhaltiger Gley über Niedermoor aus Alm über Torf, engräumig vergesellschaftet mit Kalkniedermoor und Kalkerdniedermoor aus Torf",
    "78": "Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum",
    "75": "Fast ausschließlich Moorgley, Anmoorgley und Oxigley aus Lehmgrus bis Sandgrus (Talsediment)",
    "75c": "Bodenkomplex: Vorherrschend Gley und Anmoorgley, gering verbreitet Moorgley aus (Kryo-)Sandschutt (Granit oder Gneis), selten Niedermoor aus Torf",
    "850": "Bodenkomplex: Humusgleye, Moorgleye, Anmoorgleye und Niedermoore aus alpinen Substraten mit weitem Bodenartenspektrum",
    "72f": "Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche",
    "65c": "Fast ausschließlich Anmoorgley, Niedermoorgley und Nassgley aus Lehmsand bis Lehm (Talsediment); im Untergrund carbonathaltig",
    "73f": "Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche",
    "72c": "Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Talsediment)",
    "66b": "Fast ausschließlich Anmoorgley aus Lehm bis Schluff, selten Ton (See- oder Flusssediment); im Untergrund carbonathaltig",
    "61a": "Bodenkomplex: Vorherrschend Anmoorgley und Pseudogley, gering verbreitet Podsol aus (Kryo-)Sandschutt (Granit oder Gneis) über Sandschutt bis Sandgrus (Basislage, verfestigt)",
    "79": "Fast ausschließlich Hochmoor und Erdhochmoor aus Torf",
    "64c": "Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel) über Carbonatsandkies (Schotter), gering verbreitet aus Talsediment",
    "73c": "Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Talsediment)",
    "74": "Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von Lehm und Torf über Sand bis Lehm (Talsediment)",
    "62c": "Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel oder Alm) über tiefem Carbonatsandkies (Schotter)",
    "77": "Fast ausschließlich Kalkniedermoor und Kalkerdniedermoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum; verbreitet mit Wiesenkalk durchsetzt",
    "67": "Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von (Carbonat-)Lehm bis Schluff und Torf über Carbonatsandkies (Schotter)"
}
def analyse(word):
    prompt= 'I will present you with a question about the nature of soil. Please answer this question by referring to the information provided in the statements I give you. Sentence you need to judge:%s. Your response should be in JSON format. If the answer is correct, return {"judge": True}. If the answer is incorrect, return {"judge": False}, If there is not enough information for you to tell if is correct,return {"judge": not know} '%word

    # if change_statement(prompt,ques1,'4')['judge']:
    question_1 = "Is it primarily composed of peat?"
    question_2 = "Is it mainly lowland marsh?"
    question_3 = "Is it related to highland marsh?"
    question_4 = "Contains mineral deposits?"
    question_5 = "Contains carbonate?"
    question_6 = "Related to alpine substrates?"
    question_7 = "Is it primarily gley?"
    question_8 = "Related to valley sediments?"
    question_9 = "Is it primarily clay or silt?"
    question_10 = "Is it more loamy?"
    question_11 = "Related to gravel?"
    question_12 = "Rich in humus?"
    question_13 = "Mainly silt to clay?"
    question_14 = "Mainly sand?"
    question_15 = "Granite or gneiss composition?"
        # Python script to guide the user through the decision tree using input questions

    # Define the questions
    questions = [
        "Is it primarily composed of peat? (y/n): ",
        "Is it mainly lowland marsh? (y/n): ",
        "Is it related to highland marsh? (y/n): ",
        "Contains mineral deposits? (y/n): ",
        "Contains carbonate? (y/n): ",
        "Related to alpine substrates? (y/n): ",
        "Is it primarily gley? (y/n): ",
        "Related to valley sediments? (y/n): ",
        "Is it primarily clay or silt? (y/n): ",
        "Is it more loamy? (y/n): ",
        "Related to gravel? (y/n): ",
        "Rich in humus? (y/n): ",
        "Mainly silt to clay? (y/n): ",
        "Mainly sand? (y/n): ",
        "Granite or gneiss composition? (y/n): "
    ]

    # Function to determine the label
    def determine_label(answers):
        if answers[0] == 'y':  # Peat
            if answers[1] == 'y':  # Lowland marsh
                if answers[2] == 'y':  # Highland marsh
                    return "79"
                else:  # Not highland marsh
                    if answers[3] == 'y':  # Mineral deposits
                        if answers[4] == 'y':  # Carbonate
                            return "67"
                        else:  # No carbonate
                            return "78"
                    else:  # No mineral deposits
                        return "78a"
            else:  # Not lowland marsh
                if answers[3] == 'y':  # Mineral deposits
                    return "80a, 80b"
                else:  # No mineral deposits
                    if answers[5] == 'y':  # Alpine substrates
                        return "850"
                    else:  # Not alpine substrates
                        return "77"
        else:  # Not peat
            if answers[6] == 'y':  # Gley
                if answers[3] == 'y':  # Mineral deposits
                    if answers[7] == 'y':  # Valley sediments
                        if answers[4] == 'y':  # Carbonate
                            return "64c, 62c"
                        else:  # No carbonate
                            if answers[8] == 'y':  # Clay or silt
                                return "73c"
                            else:  # Not clay or silt
                                if answers[9] == 'y':  # Loamy
                                    return "74"
                                else:  # Not loamy
                                    return "75"
                    else:  # Not valley sediments
                        if answers[4] == 'y':  # Carbonate
                            return "66b"
                        else:  # No carbonate
                            return "65c"
                else:  # No mineral deposits
                    if answers[5] == 'y':  # Alpine substrates
                        return "75c"
                    else:  # Not alpine substrates
                        if answers[10] == 'y':  # Gravel
                            if answers[11] == 'y':  # Humus
                                if answers[12] == 'y':  # Silt to clay
                                    return "73f"
                                else:  # Not silt to clay
                                    return "72f"
                            else:  # Not humus
                                if answers[13] == 'y':  # Sand
                                    return "72c"
                                else:  # Not sand
                                    if answers[14] == 'y':  # Granite or gneiss
                                        return "61a"
                                    else:  # Not granite or gneiss
                                        return "Other"
                        else:  # Not gravel
                            return "Other"
            else:  # Not gley
                return "Other"


    answers = []
    for question in questions:
        each_answer=change_statement(prompt, question.replace(" (y/n): ", ""), '4')['judge']
        if each_answer==True:
            answers.append('y')
        elif each_answer==False:
            answers.append('n')
        elif each_answer== "not know":

            break
    answers_human = []
    for num, question in enumerate(questions):
        if num>len(answers)-1:
            answers_human = input(question)
            answers.append(answers_human.lower())
    answers.extend(answers_human)
    label = determine_label(answers)
    return label


print(analyse('Bodenkomplex: Humusgleye, Moorgleye, Anmoorgleye und Niedermoore aus alpinen Substraten mit weitem Bodenartenspektrum'))