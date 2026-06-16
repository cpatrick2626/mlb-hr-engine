const rect = (x, y, w, h) => ({ t: "rect", x, y, w, h });
const circle = (cx, cy, r) => ({ t: "circle", cx, cy, r });

const country = (record) => ({
  ...record,
  flag_asset: `assets/flags/${record.id}.svg`,
});

export const COUNTRIES = [
  country({
    "id": "france",
    "iso2": "FR",
    "iso3": "FRA",
    "name": "France",
    "capital": "Paris",
    "continent": "Europe",
    "languages": [
      "French"
    ],
    "flag_asset": "assets/flags/france.svg",
    "theme_colors": [
      "#0055A4",
      "#FFFFFF",
      "#EF4135"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#0055A4",
      "#FFFFFF",
      "#EF4135"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "italy",
    "iso2": "IT",
    "iso3": "ITA",
    "name": "Italy",
    "capital": "Rome",
    "continent": "Europe",
    "languages": [
      "Italian"
    ],
    "flag_asset": "assets/flags/italy.svg",
    "theme_colors": [
      "#009246",
      "#FFFFFF",
      "#CE2B37"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#009246",
      "#FFFFFF",
      "#CE2B37"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "ireland",
    "iso2": "IE",
    "iso3": "IRL",
    "name": "Ireland",
    "capital": "Dublin",
    "continent": "Europe",
    "languages": [
      "Irish",
      "English"
    ],
    "flag_asset": "assets/flags/ireland.svg",
    "theme_colors": [
      "#169B62",
      "#FFFFFF",
      "#FF883E"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#169B62",
      "#FFFFFF",
      "#FF883E"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "belgium",
    "iso2": "BE",
    "iso3": "BEL",
    "name": "Belgium",
    "capital": "Brussels",
    "continent": "Europe",
    "languages": [
      "Dutch",
      "French",
      "German"
    ],
    "flag_asset": "assets/flags/belgium.svg",
    "theme_colors": [
      "#2D2926",
      "#FDDA24",
      "#EF3340"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#2D2926",
      "#FDDA24",
      "#EF3340"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "germany",
    "iso2": "DE",
    "iso3": "DEU",
    "name": "Germany",
    "capital": "Berlin",
    "continent": "Europe",
    "languages": [
      "German"
    ],
    "flag_asset": "assets/flags/germany.svg",
    "theme_colors": [
      "#2D2926",
      "#DD0000",
      "#FFCE00"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      }
    ],
    "flag_colors": [
      "#2D2926",
      "#DD0000",
      "#FFCE00"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "netherlands",
    "iso2": "NL",
    "iso3": "NLD",
    "name": "Netherlands",
    "capital": "Amsterdam",
    "continent": "Europe",
    "languages": [
      "Dutch"
    ],
    "flag_asset": "assets/flags/netherlands.svg",
    "theme_colors": [
      "#AE1C28",
      "#FFFFFF",
      "#21468B"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      }
    ],
    "flag_colors": [
      "#AE1C28",
      "#FFFFFF",
      "#21468B"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "poland",
    "iso2": "PL",
    "iso3": "POL",
    "name": "Poland",
    "capital": "Warsaw",
    "continent": "Europe",
    "languages": [
      "Polish"
    ],
    "flag_asset": "assets/flags/poland.svg",
    "theme_colors": [
      "#FFFFFF",
      "#DC143C"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 100
          }
        ]
      }
    ],
    "flag_colors": [
      "#FFFFFF",
      "#DC143C"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Zloty",
    "population": ""
  }),
  country({
    "id": "ukraine",
    "iso2": "UA",
    "iso3": "UKR",
    "name": "Ukraine",
    "capital": "Kyiv",
    "continent": "Europe",
    "languages": [
      "Ukrainian"
    ],
    "flag_asset": "assets/flags/ukraine.svg",
    "theme_colors": [
      "#0057B7",
      "#FFD700"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 100
          }
        ]
      }
    ],
    "flag_colors": [
      "#0057B7",
      "#FFD700"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Hryvnia",
    "population": ""
  }),
  country({
    "id": "austria",
    "iso2": "AT",
    "iso3": "AUT",
    "name": "Austria",
    "capital": "Vienna",
    "continent": "Europe",
    "languages": [
      "German"
    ],
    "flag_asset": "assets/flags/austria.svg",
    "theme_colors": [
      "#ED2939",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      }
    ],
    "flag_colors": [
      "#ED2939",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "japan",
    "iso2": "JP",
    "iso3": "JPN",
    "name": "Japan",
    "capital": "Tokyo",
    "continent": "Asia",
    "languages": [
      "Japanese"
    ],
    "flag_asset": "assets/flags/japan.svg",
    "theme_colors": [
      "#FFFFFF",
      "#BC002D"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "disc",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 150,
            "cy": 100,
            "r": 60
          }
        ]
      }
    ],
    "flag_colors": [
      "#FFFFFF",
      "#BC002D"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Yen",
    "population": ""
  }),
  country({
    "id": "sweden",
    "iso2": "SE",
    "iso3": "SWE",
    "name": "Sweden",
    "capital": "Stockholm",
    "continent": "Europe",
    "languages": [
      "Swedish"
    ],
    "flag_asset": "assets/flags/sweden.svg",
    "theme_colors": [
      "#006AA7",
      "#FECC02"
    ],
    "flag_regions": [
      {
        "id": "blue_top_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 90,
            "h": 82
          }
        ]
      },
      {
        "id": "blue_top_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 126,
            "y": 0,
            "w": 174,
            "h": 82
          }
        ]
      },
      {
        "id": "blue_bottom_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 118,
            "w": 90,
            "h": 82
          }
        ]
      },
      {
        "id": "blue_bottom_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 126,
            "y": 118,
            "w": 174,
            "h": 82
          }
        ]
      },
      {
        "id": "yellow_cross",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 90,
            "y": 0,
            "w": 36,
            "h": 82
          },
          {
            "t": "rect",
            "x": 90,
            "y": 82,
            "w": 36,
            "h": 36
          },
          {
            "t": "rect",
            "x": 90,
            "y": 118,
            "w": 36,
            "h": 82
          },
          {
            "t": "rect",
            "x": 0,
            "y": 82,
            "w": 90,
            "h": 36
          },
          {
            "t": "rect",
            "x": 126,
            "y": 82,
            "w": 174,
            "h": 36
          }
        ]
      }
    ],
    "flag_colors": [
      "#006AA7",
      "#FECC02"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Krona",
    "population": ""
  }),
  country({
    "id": "denmark",
    "iso2": "DK",
    "iso3": "DNK",
    "name": "Denmark",
    "capital": "Copenhagen",
    "continent": "Europe",
    "languages": [
      "Danish"
    ],
    "flag_asset": "assets/flags/denmark.svg",
    "theme_colors": [
      "#C8102E",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "red_top_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 90,
            "h": 82
          }
        ]
      },
      {
        "id": "red_top_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 126,
            "y": 0,
            "w": 174,
            "h": 82
          }
        ]
      },
      {
        "id": "red_bottom_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 118,
            "w": 90,
            "h": 82
          }
        ]
      },
      {
        "id": "red_bottom_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 126,
            "y": 118,
            "w": 174,
            "h": 82
          }
        ]
      },
      {
        "id": "white_cross",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 90,
            "y": 0,
            "w": 36,
            "h": 82
          },
          {
            "t": "rect",
            "x": 90,
            "y": 82,
            "w": 36,
            "h": 36
          },
          {
            "t": "rect",
            "x": 90,
            "y": 118,
            "w": 36,
            "h": 82
          },
          {
            "t": "rect",
            "x": 0,
            "y": 82,
            "w": 90,
            "h": 36
          },
          {
            "t": "rect",
            "x": 126,
            "y": 82,
            "w": 174,
            "h": 36
          }
        ]
      }
    ],
    "flag_colors": [
      "#C8102E",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Krone",
    "population": ""
  }),
  country({
    "id": "spain",
    "iso2": "ES",
    "iso3": "ESP",
    "name": "Spain",
    "capital": "Madrid",
    "continent": "Europe",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/spain.svg",
    "theme_colors": [
      "#AA151B",
      "#F1BF00"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      }
    ],
    "flag_colors": [
      "#AA151B",
      "#F1BF00"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "portugal",
    "iso2": "PT",
    "iso3": "PRT",
    "name": "Portugal",
    "capital": "Lisbon",
    "continent": "Europe",
    "languages": [
      "Portuguese"
    ],
    "flag_asset": "assets/flags/portugal.svg",
    "theme_colors": [
      "#006600",
      "#FF0000",
      "#FFD100"
    ],
    "flag_regions": [
      {
        "id": "left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 120,
            "h": 200
          }
        ]
      },
      {
        "id": "right",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 120,
            "y": 0,
            "w": 180,
            "h": 200
          }
        ]
      },
      {
        "id": "disc",
        "color": 2,
        "shapes": [
          {
            "t": "circle",
            "cx": 120,
            "cy": 100,
            "r": 34
          }
        ]
      }
    ],
    "flag_colors": [
      "#006600",
      "#FF0000",
      "#FFD100"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "switzerland",
    "iso2": "CH",
    "iso3": "CHE",
    "name": "Switzerland",
    "capital": "Bern",
    "continent": "Europe",
    "languages": [
      "German",
      "French",
      "Italian",
      "Romansh"
    ],
    "flag_asset": "assets/flags/switzerland.svg",
    "theme_colors": [
      "#D52B1E",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "red_top_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 90,
            "h": 80
          }
        ]
      },
      {
        "id": "red_top_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 210,
            "y": 0,
            "w": 90,
            "h": 80
          }
        ]
      },
      {
        "id": "red_bottom_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 120,
            "w": 90,
            "h": 80
          }
        ]
      },
      {
        "id": "red_bottom_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 210,
            "y": 120,
            "w": 90,
            "h": 80
          }
        ]
      },
      {
        "id": "white_cross",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 120,
            "y": 50,
            "w": 60,
            "h": 100
          },
          {
            "t": "rect",
            "x": 90,
            "y": 80,
            "w": 30,
            "h": 40
          },
          {
            "t": "rect",
            "x": 180,
            "y": 80,
            "w": 30,
            "h": 40
          }
        ]
      }
    ],
    "flag_colors": [
      "#D52B1E",
      "#FFFFFF"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Franc",
    "population": ""
  }),
  country({
    "id": "norway",
    "iso2": "NO",
    "iso3": "NOR",
    "name": "Norway",
    "capital": "Oslo",
    "continent": "Europe",
    "languages": [
      "Norwegian"
    ],
    "flag_asset": "assets/flags/norway.svg",
    "theme_colors": [
      "#BA0C2F",
      "#FFFFFF",
      "#00205B"
    ],
    "flag_regions": [
      {
        "id": "red_top_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 84,
            "h": 76
          }
        ]
      },
      {
        "id": "red_top_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 132,
            "y": 0,
            "w": 168,
            "h": 76
          }
        ]
      },
      {
        "id": "red_bottom_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 124,
            "w": 84,
            "h": 76
          }
        ]
      },
      {
        "id": "red_bottom_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 132,
            "y": 124,
            "w": 168,
            "h": 76
          }
        ]
      },
      {
        "id": "white_cross",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 84,
            "y": 0,
            "w": 48,
            "h": 76
          },
          {
            "t": "rect",
            "x": 84,
            "y": 76,
            "w": 48,
            "h": 48
          },
          {
            "t": "rect",
            "x": 84,
            "y": 124,
            "w": 48,
            "h": 76
          },
          {
            "t": "rect",
            "x": 0,
            "y": 76,
            "w": 84,
            "h": 48
          },
          {
            "t": "rect",
            "x": 132,
            "y": 76,
            "w": 168,
            "h": 48
          }
        ]
      },
      {
        "id": "blue_cross",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 96,
            "y": 0,
            "w": 24,
            "h": 76
          },
          {
            "t": "rect",
            "x": 96,
            "y": 76,
            "w": 24,
            "h": 48
          },
          {
            "t": "rect",
            "x": 96,
            "y": 124,
            "w": 24,
            "h": 76
          },
          {
            "t": "rect",
            "x": 0,
            "y": 88,
            "w": 96,
            "h": 24
          },
          {
            "t": "rect",
            "x": 120,
            "y": 88,
            "w": 180,
            "h": 24
          }
        ]
      }
    ],
    "flag_colors": [
      "#BA0C2F",
      "#FFFFFF",
      "#00205B"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Krone",
    "population": ""
  }),
  country({
    "id": "finland",
    "iso2": "FI",
    "iso3": "FIN",
    "name": "Finland",
    "capital": "Helsinki",
    "continent": "Europe",
    "languages": [
      "Finnish",
      "Swedish"
    ],
    "flag_asset": "assets/flags/finland.svg",
    "theme_colors": [
      "#FFFFFF",
      "#003580"
    ],
    "flag_regions": [
      {
        "id": "white_top_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 90,
            "h": 82
          }
        ]
      },
      {
        "id": "white_top_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 126,
            "y": 0,
            "w": 174,
            "h": 82
          }
        ]
      },
      {
        "id": "white_bottom_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 118,
            "w": 90,
            "h": 82
          }
        ]
      },
      {
        "id": "white_bottom_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 126,
            "y": 118,
            "w": 174,
            "h": 82
          }
        ]
      },
      {
        "id": "blue_cross",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 90,
            "y": 0,
            "w": 36,
            "h": 82
          },
          {
            "t": "rect",
            "x": 90,
            "y": 82,
            "w": 36,
            "h": 36
          },
          {
            "t": "rect",
            "x": 90,
            "y": 118,
            "w": 36,
            "h": 82
          },
          {
            "t": "rect",
            "x": 0,
            "y": 82,
            "w": 90,
            "h": 36
          },
          {
            "t": "rect",
            "x": 126,
            "y": 82,
            "w": 174,
            "h": 36
          }
        ]
      }
    ],
    "flag_colors": [
      "#FFFFFF",
      "#003580"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "iceland",
    "iso2": "IS",
    "iso3": "ISL",
    "name": "Iceland",
    "capital": "Reykjavik",
    "continent": "Europe",
    "languages": [
      "Icelandic"
    ],
    "flag_asset": "assets/flags/iceland.svg",
    "theme_colors": [
      "#003897",
      "#FFFFFF",
      "#D72828"
    ],
    "flag_regions": [
      {
        "id": "blue_top_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 84,
            "h": 76
          }
        ]
      },
      {
        "id": "blue_top_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 132,
            "y": 0,
            "w": 168,
            "h": 76
          }
        ]
      },
      {
        "id": "blue_bottom_left",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 124,
            "w": 84,
            "h": 76
          }
        ]
      },
      {
        "id": "blue_bottom_right",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 132,
            "y": 124,
            "w": 168,
            "h": 76
          }
        ]
      },
      {
        "id": "white_cross",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 84,
            "y": 0,
            "w": 48,
            "h": 76
          },
          {
            "t": "rect",
            "x": 84,
            "y": 76,
            "w": 48,
            "h": 48
          },
          {
            "t": "rect",
            "x": 84,
            "y": 124,
            "w": 48,
            "h": 76
          },
          {
            "t": "rect",
            "x": 0,
            "y": 76,
            "w": 84,
            "h": 48
          },
          {
            "t": "rect",
            "x": 132,
            "y": 76,
            "w": 168,
            "h": 48
          }
        ]
      },
      {
        "id": "red_cross",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 96,
            "y": 0,
            "w": 24,
            "h": 76
          },
          {
            "t": "rect",
            "x": 96,
            "y": 76,
            "w": 24,
            "h": 48
          },
          {
            "t": "rect",
            "x": 96,
            "y": 124,
            "w": 24,
            "h": 76
          },
          {
            "t": "rect",
            "x": 0,
            "y": 88,
            "w": 84,
            "h": 24
          },
          {
            "t": "rect",
            "x": 120,
            "y": 88,
            "w": 180,
            "h": 24
          }
        ]
      }
    ],
    "flag_colors": [
      "#003897",
      "#FFFFFF",
      "#D72828"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Krona",
    "population": ""
  }),
  country({
    "id": "greece",
    "iso2": "GR",
    "iso3": "GRC",
    "name": "Greece",
    "capital": "Athens",
    "continent": "Europe",
    "languages": [
      "Greek"
    ],
    "flag_asset": "assets/flags/greece.svg",
    "theme_colors": [
      "#0D5EAF",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 22,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 44,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r3",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 66,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r4",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 88,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r5",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 110,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r6",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 132,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r7",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 154,
            "w": 300,
            "h": 22
          }
        ]
      },
      {
        "id": "r8",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 176,
            "w": 300,
            "h": 24
          }
        ]
      }
    ],
    "flag_colors": [
      "#0D5EAF",
      "#FFFFFF"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "croatia",
    "iso2": "HR",
    "iso3": "HRV",
    "name": "Croatia",
    "capital": "Zagreb",
    "continent": "Europe",
    "languages": [
      "Croatian"
    ],
    "flag_asset": "assets/flags/croatia.svg",
    "theme_colors": [
      "#FF0000",
      "#FFFFFF",
      "#171796"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      }
    ],
    "flag_colors": [
      "#FF0000",
      "#FFFFFF",
      "#171796"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Euro",
    "population": ""
  }),
  country({
    "id": "czech-republic",
    "iso2": "CZ",
    "iso3": "CZE",
    "name": "Czech Republic",
    "capital": "Prague",
    "continent": "Europe",
    "languages": [
      "Czech"
    ],
    "flag_asset": "assets/flags/czech-republic.svg",
    "theme_colors": [
      "#FFFFFF",
      "#D7141A",
      "#11457E"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,0 130,100 0,200"
          }
        ]
      }
    ],
    "flag_colors": [
      "#FFFFFF",
      "#D7141A",
      "#11457E"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Koruna",
    "population": ""
  }),
  country({
    "id": "romania",
    "iso2": "RO",
    "iso3": "ROU",
    "name": "Romania",
    "capital": "Bucharest",
    "continent": "Europe",
    "languages": [
      "Romanian"
    ],
    "flag_asset": "assets/flags/romania.svg",
    "theme_colors": [
      "#002B7F",
      "#FCD116",
      "#CE1126"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#002B7F",
      "#FCD116",
      "#CE1126"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Leu",
    "population": ""
  }),
  country({
    "id": "brazil",
    "iso2": "BR",
    "iso3": "BRA",
    "name": "Brazil",
    "capital": "Brasilia",
    "continent": "South America",
    "languages": [
      "Portuguese"
    ],
    "flag_asset": "assets/flags/brazil.svg",
    "theme_colors": [
      "#009C3B",
      "#FFDF00",
      "#002776"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "diamond",
        "color": 1,
        "shapes": [
          {
            "t": "polygon",
            "points": "150,30 250,100 150,170 50,100"
          }
        ]
      },
      {
        "id": "disc",
        "color": 2,
        "shapes": [
          {
            "t": "circle",
            "cx": 150,
            "cy": 100,
            "r": 42
          }
        ]
      }
    ],
    "flag_colors": [
      "#009C3B",
      "#FFDF00",
      "#002776"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Real",
    "population": ""
  }),
  country({
    "id": "argentina",
    "iso2": "AR",
    "iso3": "ARG",
    "name": "Argentina",
    "capital": "Buenos Aires",
    "continent": "South America",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/argentina.svg",
    "theme_colors": [
      "#74ACDF",
      "#FFFFFF",
      "#F6B40E"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      }
    ],
    "flag_colors": [
      "#74ACDF",
      "#FFFFFF",
      "#F6B40E"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Peso",
    "population": ""
  }),
  country({
    "id": "chile",
    "iso2": "CL",
    "iso3": "CHL",
    "name": "Chile",
    "capital": "Santiago",
    "continent": "South America",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/chile.svg",
    "theme_colors": [
      "#FFFFFF",
      "#D52B1E",
      "#0039A6"
    ],
    "flag_regions": [
      {
        "id": "top",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "bottom-left",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "canton",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 100
          }
        ]
      }
    ],
    "flag_colors": [
      "#FFFFFF",
      "#D52B1E",
      "#0039A6"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Peso",
    "population": ""
  }),
  country({
    "id": "peru",
    "iso2": "PE",
    "iso3": "PER",
    "name": "Peru",
    "capital": "Lima",
    "continent": "South America",
    "languages": [
      "Spanish",
      "Quechua",
      "Aymara"
    ],
    "flag_asset": "assets/flags/peru.svg",
    "theme_colors": [
      "#D91023",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#D91023",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Sol",
    "population": ""
  }),
  country({
    "id": "colombia",
    "iso2": "CO",
    "iso3": "COL",
    "name": "Colombia",
    "capital": "Bogota",
    "continent": "South America",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/colombia.svg",
    "theme_colors": [
      "#FCD116",
      "#003893",
      "#CE1126"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 50
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 150,
            "w": 300,
            "h": 50
          }
        ]
      }
    ],
    "flag_colors": [
      "#FCD116",
      "#003893",
      "#CE1126"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Peso",
    "population": ""
  }),
  country({
    "id": "venezuela",
    "iso2": "VE",
    "iso3": "VEN",
    "name": "Venezuela",
    "capital": "Caracas",
    "continent": "South America",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/venezuela.svg",
    "theme_colors": [
      "#F4D900",
      "#0038A8",
      "#EF3340"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      }
    ],
    "flag_colors": [
      "#F4D900",
      "#0038A8",
      "#EF3340"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Bolivar",
    "population": ""
  }),
  country({
    "id": "mexico",
    "iso2": "MX",
    "iso3": "MEX",
    "name": "Mexico",
    "capital": "Mexico City",
    "continent": "North America",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/mexico.svg",
    "theme_colors": [
      "#006847",
      "#FFFFFF",
      "#CE1126"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#006847",
      "#FFFFFF",
      "#CE1126"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Peso",
    "population": ""
  }),
  country({
    "id": "guatemala",
    "iso2": "GT",
    "iso3": "GTM",
    "name": "Guatemala",
    "capital": "Guatemala City",
    "continent": "North America",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/guatemala.svg",
    "theme_colors": [
      "#4997D0",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#4997D0",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Quetzal",
    "population": ""
  }),
  country({
    "id": "cuba",
    "iso2": "CU",
    "iso3": "CUB",
    "name": "Cuba",
    "capital": "Havana",
    "continent": "North America",
    "languages": [
      "Spanish"
    ],
    "flag_asset": "assets/flags/cuba.svg",
    "theme_colors": [
      "#002A8F",
      "#FFFFFF",
      "#CF142B"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 40
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 40,
            "w": 300,
            "h": 40
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 80,
            "w": 300,
            "h": 40
          }
        ]
      },
      {
        "id": "r3",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 120,
            "w": 300,
            "h": 40
          }
        ]
      },
      {
        "id": "r4",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 160,
            "w": 300,
            "h": 40
          }
        ]
      },
      {
        "id": "triangle",
        "color": 2,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,0 130,100 0,200"
          }
        ]
      }
    ],
    "flag_colors": [
      "#002A8F",
      "#FFFFFF",
      "#CF142B"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Peso",
    "population": ""
  }),
  country({
    "id": "jamaica",
    "iso2": "JM",
    "iso3": "JAM",
    "name": "Jamaica",
    "capital": "Kingston",
    "continent": "North America",
    "languages": [
      "English"
    ],
    "flag_asset": "assets/flags/jamaica.svg",
    "theme_colors": [
      "#009B3A",
      "#FED100",
      "#000000"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "cross-yellow-1",
        "color": 1,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,0 120,0 150,70 120,100 0,100"
          }
        ]
      },
      {
        "id": "cross-yellow-2",
        "color": 1,
        "shapes": [
          {
            "t": "polygon",
            "points": "300,0 180,0 150,70 180,100 300,100"
          }
        ]
      },
      {
        "id": "cross-yellow-3",
        "color": 1,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,200 120,200 150,130 120,100 0,100"
          }
        ]
      },
      {
        "id": "cross-yellow-4",
        "color": 1,
        "shapes": [
          {
            "t": "polygon",
            "points": "300,200 180,200 150,130 180,100 300,100"
          }
        ]
      },
      {
        "id": "cross-black-1",
        "color": 2,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,0 140,100 0,100"
          }
        ]
      },
      {
        "id": "cross-black-2",
        "color": 2,
        "shapes": [
          {
            "t": "polygon",
            "points": "300,0 160,100 300,100"
          }
        ]
      },
      {
        "id": "cross-black-3",
        "color": 2,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,200 140,100 0,100"
          }
        ]
      },
      {
        "id": "cross-black-4",
        "color": 2,
        "shapes": [
          {
            "t": "polygon",
            "points": "300,200 160,100 300,100"
          }
        ]
      }
    ],
    "flag_colors": [
      "#009B3A",
      "#FED100",
      "#000000"
    ],
    "difficulty": "expert",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dollar",
    "population": ""
  }),
  country({
    "id": "united-states",
    "iso2": "US",
    "iso3": "USA",
    "name": "United States",
    "capital": "Washington, D.C.",
    "continent": "North America",
    "languages": [
      "English"
    ],
    "flag_asset": "assets/flags/united-states.svg",
    "theme_colors": [
      "#B22234",
      "#FFFFFF",
      "#3C3B6E"
    ],
    "flag_regions": [
      {
        "id": "stripe-0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 15,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 30,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-3",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 45,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-4",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 60,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-5",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 75,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-6",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 90,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-7",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 105,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-8",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 120,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-9",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 135,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-10",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 150,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-11",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 165,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-12",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 180,
            "w": 300,
            "h": 20
          }
        ]
      },
      {
        "id": "canton",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 120,
            "h": 105
          }
        ]
      }
    ],
    "flag_colors": [
      "#B22234",
      "#FFFFFF",
      "#3C3B6E"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dollar",
    "population": ""
  }),
  country({
    "id": "canada",
    "iso2": "CA",
    "iso3": "CAN",
    "name": "Canada",
    "capital": "Ottawa",
    "continent": "North America",
    "languages": [
      "English",
      "French"
    ],
    "flag_asset": "assets/flags/canada.svg",
    "theme_colors": [
      "#FF0000",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 75,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 75,
            "y": 0,
            "w": 150,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 225,
            "y": 0,
            "w": 75,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#FF0000",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dollar",
    "population": ""
  }),
  country({
    "id": "china",
    "iso2": "CN",
    "iso3": "CHN",
    "name": "China",
    "capital": "Beijing",
    "continent": "Asia",
    "languages": [
      "Mandarin Chinese"
    ],
    "flag_asset": "assets/flags/china.svg",
    "theme_colors": [
      "#DE2910",
      "#FFDE00"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "star-main",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 60,
            "cy": 50,
            "r": 16
          }
        ]
      },
      {
        "id": "star-1",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 96,
            "cy": 28,
            "r": 7
          }
        ]
      },
      {
        "id": "star-2",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 118,
            "cy": 50,
            "r": 7
          }
        ]
      },
      {
        "id": "star-3",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 118,
            "cy": 84,
            "r": 7
          }
        ]
      },
      {
        "id": "star-4",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 96,
            "cy": 106,
            "r": 7
          }
        ]
      }
    ],
    "flag_colors": [
      "#DE2910",
      "#FFDE00"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Yuan",
    "population": ""
  }),
  country({
    "id": "south-korea",
    "iso2": "KR",
    "iso3": "KOR",
    "name": "South Korea",
    "capital": "Seoul",
    "continent": "Asia",
    "languages": [
      "Korean"
    ],
    "flag_asset": "assets/flags/south-korea.svg",
    "theme_colors": [
      "#FFFFFF",
      "#CD2E3A",
      "#0047A0",
      "#000000"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "yin",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 150,
            "cy": 100,
            "r": 34
          }
        ]
      },
      {
        "id": "yang",
        "color": 2,
        "shapes": [
          {
            "t": "circle",
            "cx": 150,
            "cy": 100,
            "r": 18
          }
        ]
      },
      {
        "id": "bar-1",
        "color": 3,
        "shapes": [
          {
            "t": "rect",
            "x": 40,
            "y": 36,
            "w": 48,
            "h": 12
          }
        ]
      },
      {
        "id": "bar-2",
        "color": 3,
        "shapes": [
          {
            "t": "rect",
            "x": 40,
            "y": 56,
            "w": 48,
            "h": 12
          }
        ]
      },
      {
        "id": "bar-3",
        "color": 3,
        "shapes": [
          {
            "t": "rect",
            "x": 212,
            "y": 132,
            "w": 48,
            "h": 12
          }
        ]
      },
      {
        "id": "bar-4",
        "color": 3,
        "shapes": [
          {
            "t": "rect",
            "x": 212,
            "y": 152,
            "w": 48,
            "h": 12
          }
        ]
      }
    ],
    "flag_colors": [
      "#FFFFFF",
      "#CD2E3A",
      "#0047A0",
      "#000000"
    ],
    "difficulty": "expert",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Won",
    "population": ""
  }),
  country({
    "id": "india",
    "iso2": "IN",
    "iso3": "IND",
    "name": "India",
    "capital": "New Delhi",
    "continent": "Asia",
    "languages": [
      "Hindi",
      "English"
    ],
    "flag_asset": "assets/flags/india.svg",
    "theme_colors": [
      "#FF9933",
      "#FFFFFF",
      "#138808",
      "#000080"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "wheel",
        "color": 3,
        "shapes": [
          {
            "t": "circle",
            "cx": 150,
            "cy": 100,
            "r": 16
          }
        ]
      }
    ],
    "flag_colors": [
      "#FF9933",
      "#FFFFFF",
      "#138808",
      "#000080"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Rupee",
    "population": ""
  }),
  country({
    "id": "thailand",
    "iso2": "TH",
    "iso3": "THA",
    "name": "Thailand",
    "capital": "Bangkok",
    "continent": "Asia",
    "languages": [
      "Thai"
    ],
    "flag_asset": "assets/flags/thailand.svg",
    "theme_colors": [
      "#A51931",
      "#FFFFFF",
      "#2D2A4A"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 40
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 40,
            "w": 300,
            "h": 40
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 80,
            "w": 300,
            "h": 80
          }
        ]
      },
      {
        "id": "r3",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 160,
            "w": 300,
            "h": 40
          }
        ]
      }
    ],
    "flag_colors": [
      "#A51931",
      "#FFFFFF",
      "#2D2A4A"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Baht",
    "population": ""
  }),
  country({
    "id": "vietnam",
    "iso2": "VN",
    "iso3": "VNM",
    "name": "Vietnam",
    "capital": "Hanoi",
    "continent": "Asia",
    "languages": [
      "Vietnamese"
    ],
    "flag_asset": "assets/flags/vietnam.svg",
    "theme_colors": [
      "#DA251D",
      "#FFDF00"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "star",
        "color": 1,
        "shapes": [
          {
            "t": "circle",
            "cx": 150,
            "cy": 100,
            "r": 24
          }
        ]
      }
    ],
    "flag_colors": [
      "#DA251D",
      "#FFDF00"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dong",
    "population": ""
  }),
  country({
    "id": "indonesia",
    "iso2": "ID",
    "iso3": "IDN",
    "name": "Indonesia",
    "capital": "Jakarta",
    "continent": "Asia",
    "languages": [
      "Indonesian"
    ],
    "flag_asset": "assets/flags/indonesia.svg",
    "theme_colors": [
      "#FF0000",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 100
          }
        ]
      }
    ],
    "flag_colors": [
      "#FF0000",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Rupiah",
    "population": ""
  }),
  country({
    "id": "philippines",
    "iso2": "PH",
    "iso3": "PHL",
    "name": "Philippines",
    "capital": "Manila",
    "continent": "Asia",
    "languages": [
      "Filipino",
      "English"
    ],
    "flag_asset": "assets/flags/philippines.svg",
    "theme_colors": [
      "#0038A8",
      "#CE1126",
      "#FFFFFF",
      "#FCD116"
    ],
    "flag_regions": [
      {
        "id": "top",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "bottom",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "triangle",
        "color": 2,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,0 140,100 0,200"
          }
        ]
      },
      {
        "id": "sun",
        "color": 3,
        "shapes": [
          {
            "t": "circle",
            "cx": 50,
            "cy": 100,
            "r": 16
          }
        ]
      }
    ],
    "flag_colors": [
      "#0038A8",
      "#CE1126",
      "#FFFFFF",
      "#FCD116"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Peso",
    "population": ""
  }),
  country({
    "id": "malaysia",
    "iso2": "MY",
    "iso3": "MYS",
    "name": "Malaysia",
    "capital": "Kuala Lumpur",
    "continent": "Asia",
    "languages": [
      "Malay"
    ],
    "flag_asset": "assets/flags/malaysia.svg",
    "theme_colors": [
      "#CC0001",
      "#FFFFFF",
      "#010066",
      "#FFCC00"
    ],
    "flag_regions": [
      {
        "id": "stripe-0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 15,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 30,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-3",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 45,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-4",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 60,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-5",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 75,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-6",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 90,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-7",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 105,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-8",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 120,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-9",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 135,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-10",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 150,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "stripe-11",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 165,
            "w": 300,
            "h": 15
          }
        ]
      },
      {
        "id": "canton",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 120,
            "h": 105
          }
        ]
      },
      {
        "id": "star",
        "color": 3,
        "shapes": [
          {
            "t": "circle",
            "cx": 60,
            "cy": 52,
            "r": 18
          }
        ]
      }
    ],
    "flag_colors": [
      "#CC0001",
      "#FFFFFF",
      "#010066",
      "#FFCC00"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Ringgit",
    "population": ""
  }),
  country({
    "id": "singapore",
    "iso2": "SG",
    "iso3": "SGP",
    "name": "Singapore",
    "capital": "Singapore",
    "continent": "Asia",
    "languages": [
      "English",
      "Malay",
      "Mandarin Chinese",
      "Tamil"
    ],
    "flag_asset": "assets/flags/singapore.svg",
    "theme_colors": [
      "#EF3340",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "top",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 100
          }
        ]
      },
      {
        "id": "bottom",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 100,
            "w": 300,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#EF3340",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dollar",
    "population": ""
  }),
  country({
    "id": "egypt",
    "iso2": "EG",
    "iso3": "EGY",
    "name": "Egypt",
    "capital": "Cairo",
    "continent": "Africa",
    "languages": [
      "Arabic"
    ],
    "flag_asset": "assets/flags/egypt.svg",
    "theme_colors": [
      "#CE1126",
      "#FFFFFF",
      "#000000",
      "#C09300"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "r2",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "emblem",
        "color": 3,
        "shapes": [
          {
            "t": "circle",
            "cx": 150,
            "cy": 100,
            "r": 16
          }
        ]
      }
    ],
    "flag_colors": [
      "#CE1126",
      "#FFFFFF",
      "#000000",
      "#C09300"
    ],
    "difficulty": "medium",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Pound",
    "population": ""
  }),
  country({
    "id": "morocco",
    "iso2": "MA",
    "iso3": "MAR",
    "name": "Morocco",
    "capital": "Rabat",
    "continent": "Africa",
    "languages": [
      "Arabic",
      "Amazigh"
    ],
    "flag_asset": "assets/flags/morocco.svg",
    "theme_colors": [
      "#C1272D",
      "#006233"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "star",
        "color": 1,
        "shapes": [
          {
            "t": "polygon",
            "points": "150,60 165,95 203,95 172,118 184,154 150,132 116,154 128,118 97,95 135,95"
          }
        ]
      }
    ],
    "flag_colors": [
      "#C1272D",
      "#006233"
    ],
    "difficulty": "expert",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dirham",
    "population": ""
  }),
  country({
    "id": "nigeria",
    "iso2": "NG",
    "iso3": "NGA",
    "name": "Nigeria",
    "capital": "Abuja",
    "continent": "Africa",
    "languages": [
      "English"
    ],
    "flag_asset": "assets/flags/nigeria.svg",
    "theme_colors": [
      "#008753",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "r0",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r1",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 100,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      },
      {
        "id": "r2",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 200,
            "y": 0,
            "w": 100,
            "h": 200
          }
        ]
      }
    ],
    "flag_colors": [
      "#008753",
      "#FFFFFF"
    ],
    "difficulty": "easy",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Naira",
    "population": ""
  }),
  country({
    "id": "kenya",
    "iso2": "KE",
    "iso3": "KEN",
    "name": "Kenya",
    "capital": "Nairobi",
    "continent": "Africa",
    "languages": [
      "Swahili",
      "English"
    ],
    "flag_asset": "assets/flags/kenya.svg",
    "theme_colors": [
      "#000000",
      "#BB0000",
      "#006600",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "top",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "mid",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "bot",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "shield",
        "color": 3,
        "shapes": [
          {
            "t": "rect",
            "x": 130,
            "y": 60,
            "w": 40,
            "h": 80
          }
        ]
      }
    ],
    "flag_colors": [
      "#000000",
      "#BB0000",
      "#006600",
      "#FFFFFF"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Shilling",
    "population": ""
  }),
  country({
    "id": "south-africa",
    "iso2": "ZA",
    "iso3": "ZAF",
    "name": "South Africa",
    "capital": "Pretoria",
    "continent": "Africa",
    "languages": [
      "Zulu",
      "Xhosa",
      "Afrikaans",
      "English"
    ],
    "flag_asset": "assets/flags/south-africa.svg",
    "theme_colors": [
      "#DE3831",
      "#007A4D",
      "#000000",
      "#FFB612",
      "#FFFFFF"
    ],
    "flag_regions": [
      {
        "id": "top",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "mid",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 67,
            "w": 300,
            "h": 66
          }
        ]
      },
      {
        "id": "bot",
        "color": 2,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 133,
            "w": 300,
            "h": 67
          }
        ]
      },
      {
        "id": "chevron",
        "color": 3,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,0 150,100 0,200 40,200 180,100 40,0"
          }
        ]
      },
      {
        "id": "accent",
        "color": 4,
        "shapes": [
          {
            "t": "polygon",
            "points": "0,0 160,100 0,200 20,200 170,100 20,0"
          }
        ]
      }
    ],
    "flag_colors": [
      "#DE3831",
      "#007A4D",
      "#000000",
      "#FFB612",
      "#FFFFFF"
    ],
    "difficulty": "expert",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Rand",
    "population": ""
  }),
  country({
    "id": "australia",
    "iso2": "AU",
    "iso3": "AUS",
    "name": "Australia",
    "capital": "Canberra",
    "continent": "Oceania",
    "languages": [
      "English"
    ],
    "flag_asset": "assets/flags/australia.svg",
    "theme_colors": [
      "#012169",
      "#FFFFFF",
      "#C8102E"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "canton",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 120,
            "h": 100
          }
        ]
      },
      {
        "id": "star",
        "color": 2,
        "shapes": [
          {
            "t": "circle",
            "cx": 200,
            "cy": 110,
            "r": 18
          }
        ]
      }
    ],
    "flag_colors": [
      "#012169",
      "#FFFFFF",
      "#C8102E"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dollar",
    "population": ""
  }),
  country({
    "id": "new-zealand",
    "iso2": "NZ",
    "iso3": "NZL",
    "name": "New Zealand",
    "capital": "Wellington",
    "continent": "Oceania",
    "languages": [
      "English",
      "Maori"
    ],
    "flag_asset": "assets/flags/new-zealand.svg",
    "theme_colors": [
      "#012169",
      "#FFFFFF",
      "#C8102E"
    ],
    "flag_regions": [
      {
        "id": "field",
        "color": 0,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 300,
            "h": 200
          }
        ]
      },
      {
        "id": "canton",
        "color": 1,
        "shapes": [
          {
            "t": "rect",
            "x": 0,
            "y": 0,
            "w": 120,
            "h": 100
          }
        ]
      },
      {
        "id": "star",
        "color": 2,
        "shapes": [
          {
            "t": "circle",
            "cx": 210,
            "cy": 90,
            "r": 18
          }
        ]
      }
    ],
    "flag_colors": [
      "#012169",
      "#FFFFFF",
      "#C8102E"
    ],
    "difficulty": "hard",
    "landmark": "",
    "foods": [],
    "animals": [],
    "fun_facts": [],
    "currency": "Dollar",
    "population": ""
  }),
];

export const COUNTRY_BY_ID = Object.fromEntries(COUNTRIES.map(country => [country.id, country]));

export const COLOR_THE_FLAG_COUNTRIES = COUNTRIES
  .filter(country => country.flag_regions.length > 0 && country.flag_colors.length > 0)
  .map(country => ({
    id: country.id,
    iso2: country.iso2,
    iso3: country.iso3,
    name: country.name,
    palette: country.flag_colors,
    regions: country.flag_regions,
    difficulty: country.difficulty,
  }));

export const COLOR_THE_FLAG_BY_ID = Object.fromEntries(
  COLOR_THE_FLAG_COUNTRIES.map(country => [country.id, country])
);
