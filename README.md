# Pokémon Draft

Un'applicazione desktop per fare draft di squadre Pokémon (Gen 1) e combattere, costruita con Python e Pygame.

![PokeDraft Logo](pokeball.svg)

## Requisiti

```
pip install pygame
```

## Avvio

```bash
python main.py
```

## Prima esecuzione — scarica gli sprite

Gli sprite non sono inclusi nel repo per questioni di dimensioni.  
Scaricali tutti con un solo comando prima di avviare il gioco:

```bash
python fetch_sprites.py
```

Questo scarica 151 sprite PNG da [PokeAPI/sprites](https://github.com/PokeAPI/sprites) (gratuiti, dominio pubblico) nella cartella `assets/sprites/`.  
Se mancano, il gioco mostra comunque un placeholder colorato al loro posto.

## Come si gioca

1. **Draft** — Clicca uno dei 6 slot vuoti per aprire la selezione. Scegli 1 Pokémon tra 3 casuali, per tutti e 6 gli slot.
2. **Mosse** — Per ogni Pokémon, scegli 4 mosse tra 3 opzioni casuali prese dal suo learnset.
3. **Natura** — Per ogni Pokémon, scegli 1 natura tra 3 casuali (ogni natura modifica +10%/-10% una stat).
4. **EV Spread** — Per ogni Pokémon, scegli tra 3 distribuzioni di EV: Offensiva, Difensiva, Bilanciata.
5. **Battaglia** — Combatti contro un team AI generato casualmente. Clicca una mossa o usa i tasti 1-2-3-4.

## Struttura del progetto

```
pokemon_draft/
├── main.py                  # Entry point
├── fetch_sprites.py         # Script per scaricare gli sprite
├── data/
│   ├── pokemon_gen1.json    # 151 Pokémon con stats e tipi
│   ├── moves_gen1.json      # Mosse Gen 1 con potenza, precisione, PP
│   ├── learnsets_gen1.json  # Mosse apprendibili per Pokémon
│   └── natures.json         # 25 nature con stat_up/stat_down
├── assets/
│   └── sprites/             # Sprite PNG (scaricati con fetch_sprites.py)
└── src/
    ├── pokemon.py           # Classi Pokemon, Move, Nature
    ├── utils.py             # Loader JSON, colori tipi, helpers
    ├── draft.py             # Schermata di draft
    ├── move_picker.py       # Scelta delle mosse
    ├── nature_picker.py     # Scelta della natura
    ├── ev_picker.py         # Scelta degli EV
    ├── battle.py            # Engine di battaglia
    └── battle_ui.py         # UI della battaglia
```

## Controlli battaglia

| Tasto | Azione |
|-------|--------|
| Click su mossa | Usa quella mossa |
| 1 / 2 / 3 / 4 | Seleziona mossa 1/2/3/4 |

## Prossimi sviluppi

- Online multiplayer (WebSocket)
- Gen 2 e oltre
- Animazioni mosse
- Effetti status più completi (confusion, attract, ecc.)
