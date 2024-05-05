cases={
'what type of soil is found under commercial buildings within 100 meters of the forest':{
  "search_entities": [
    {
      "entity": "soil",
      "description": "type",
      "id": 1
    },
    {
      "entity": "buildings",
      "type": "commercial",
      "id": 2
    },
    {
      "entity": "forest",
      "description": None,
      "id": 3
    }
  ],
  "relationships": [
    "#1 under #2",
    "#2 within 100 meters of the #3"
  ]
},
'Which farmlands are on soil unsuitable for agriculture':{
  "search_entities": [
    {
      "entity": "farmlands",
      "description": None,
      "id": 1
    },
    {
      "entity": "soil",
      "type": "unsuitable for agriculture",
      "id": 2
    }
  ],
  "relationships": [
    "#1 on #2"
  ]
},
'Which buildings are in soil unsuitable for buildings':{
  "search_entities": [
    {
      "entity": "buildings",
      "description": None,
      "id": 1
    },
    {
      "entity": "soil",
      "type": "unsuitable for buildings",
      "id": 2
    }
  ],
  "relationships": [
    "#1 in #2"
  ]
},

'which buildings for commercial are in landuse which is forest':{
  "search_entities": [
    {
      "entity": "buildings",
      "description": 'commercial',
      "id": 1
    },
    {
      "entity": "landuse",
      "type": "forest",
      "id": 2
    }
  ],
  "relationships": [
    "#1 in #2"
  ]
},



}