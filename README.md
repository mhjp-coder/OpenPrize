# OpenPrize

Simple Prize drawing webapp

## Development

Run the following during development for tailwind to compile the css.

```bash
npx tailwindcss -i ./src/input.css -o ./src/static/style.css --watch
```

If tailwind is not installed, run the following command from the project root to install it.

```bash
npm install -D tailwindcss
```

## TODO

- [x] Add a record prize awarded feature to record the prize and the winner this is needed because you have to be in the room to win the prize.
- [x] Complete the main page layout and fix responsiveness.
- [x] update the layout for the import page.
- [x] add feature to import a prize list from a xls file.
- [x] add feature to import from csv file as well.
- [x] add feature to remove name from list after prize is awarded.
- [x] add feature to log winners into a seperate table.
- [ ] add list view of prizes and the winners.
