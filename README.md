# espn-fantasy-league-analytics
Companion analytics app for ESPN fantasy leagues to visualize additional metrics for a given league season

## Useful commands

### Running the API
`pipenv run uvicorn api.main:app --reload`

### Updating frontend packages
1. `npx npm-check-updates --peer -u`
2. `rm -rf node_modules package-lock.json`
3. `npm install`
