from ask_functions import details_pick
soil_dict = {
    '61a': '61a: Bodenkomplex: Vorherrschend Anmoorgley und Pseudogley, gering verbreitet Podsol aus (Kryo-)Sandschutt (Granit oder Gneis) über Sandschutt bis Sandgrus (Basislage, verfestigt)',
    '62c': '62c: Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel oder Alm) über tiefem Carbonatsandkies (Schotter)',
    '65c': '65c: Fast ausschließlich Anmoorgley, Niedermoorgley und Nassgley aus Lehmsand bis Lehm (Talsediment); im Untergrund carbonathaltig',
    '66b': '66b: Fast ausschließlich Anmoorgley aus Lehm bis Schluff, selten Ton (See- oder Flusssediment); im Untergrund carbonathaltig',
    '67': '67: Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von (Carbonat-)Lehm bis Schluff und Torf über Carbonatsandkies (Schotter)',
    '72c': '72c: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Talsediment)',
    '72f': '72f: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Sand (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche',
    '64c': '64c: Fast ausschließlich kalkhaltiger Anmoorgley aus Schluff bis Lehm (Flussmergel) über Carbonatsandkies (Schotter), gering verbreitet aus Talsediment',
    '73c': '73c: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Talsediment)',
    '73f': '73f: Vorherrschend Anmoorgley und humusreicher Gley, gering verbreitet Niedermoorgley aus (skelettführendem) Schluff bis Lehm, selten aus Ton (Substrate unterschiedlicher Herkunft); außerhalb rezenter Talbereiche',
    '74': '74: Fast ausschließlich Gley über Niedermoor und Niedermoor-Gley aus Wechsellagerungen von Lehm und Torf über Sand bis Lehm (Talsediment)',
    '75': '75: Fast ausschließlich Moorgley, Anmoorgley und Oxigley aus Lehmgrus bis Sandgrus (Talsediment)',
    '75c': '75c: Bodenkomplex: Vorherrschend Gley und Anmoorgley, gering verbreitet Moorgley aus (Kryo-)Sandschutt (Granit oder Gneis), selten Niedermoor aus Torf',
    '77': '77: Fast ausschließlich Kalkniedermoor und Kalkerdniedermoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum; verbreitet mit Wiesenkalk durchsetzt',
    '78': '78: Vorherrschend Niedermoor und Erdniedermoor, gering verbreitet Übergangsmoor aus Torf über Substraten unterschiedlicher Herkunft mit weitem Bodenartenspektrum',
    '78a': '78a: Fast ausschließlich Niedermoor und Übergangsmoor aus Torf über kristallinen Substraten mit weitem Bodenartenspektrum',
    '79': '79: Fast ausschließlich Hochmoor und Erdhochmoor aus Torf',
    '80a': '80a: Fast ausschließlich (flacher) Gley über Niedermoor aus (flachen) mineralischen Ablagerungen mit weitem Bodenartenspektrum über Torf, vergesellschaftet mit (Kalk)Erdniedermoor',
    '80b': '80b: Überwiegend (Gley-)Rendzina und kalkhaltiger Gley über Niedermoor aus Alm über Torf, engräumig vergesellschaftet mit Kalkniedermoor und Kalkerdniedermoor aus Torf',
    '850': '850: Bodenkomplex: Humusgleye, Moorgleye, Anmoorgleye und Niedermoore aus alpinen Substraten mit weitem Bodenartenspektrum'}
print(details_pick('good for planting potatoes', list(soil_dict.values())))